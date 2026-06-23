# src/agent.py
import json, os, re
from openai import AsyncOpenAI
from src.storyline.storyline import GameState
from src.prompts.prompts import build_system_prompt
from src.tools.tools import TOOLS, dispatch_tool

MODEL  = os.getenv("FANAR_MODEL")
client = AsyncOpenAI(
    api_key  = os.getenv("FANAR_API_KEY"),
    base_url = os.getenv("FANAR_BASE_URL")
)

def parse_response(raw: str) -> tuple[str, list]:
    """
    Try to parse JSON response from Fanar.
    Falls back to plain text with empty tools if JSON parsing fails.
    Returns (reply, tools_list)
    """
    # Strip markdown code fences if present
    clean = raw.strip()
    if clean.startswith("```"):
        clean = re.sub(r"```(?:json)?", "", clean).strip().rstrip("```").strip()

    # Try JSON first
    try:
        data  = json.loads(clean)
        reply = data.get("reply", "")
        tools = data.get("tools", [])
        return reply, tools
    except json.JSONDecodeError:
        pass

    # Try to find JSON object embedded in text
    match = re.search(r'\{.*"reply".*"tools".*\}', clean, re.DOTALL)
    if match:
        try:
            data  = json.loads(match.group())
            reply = data.get("reply", "")
            tools = data.get("tools", [])
            return reply, tools
        except json.JSONDecodeError:
            pass

    # Pure plain text fallback — no tools
    return raw.strip(), []


async def run_turn(
    user_message: str,
    history:      list,
    state:        GameState
) -> dict:

    system   = build_system_prompt(state)
    messages = [{"role": "system", "content": system}] + history
    messages.append({"role": "user", "content": user_message})

    executed_tools = []
    final_reply    = "..."

    # ── First attempt ─────────────────────────────────────────────────────────
    response = await client.chat.completions.create(
        model      = MODEL,
        messages   = messages,
        max_tokens = 600
    )
    raw = response.choices[0].message.content
    reply, tools = parse_response(raw)

    # ── If no tools found and we expected some, retry with a nudge ────────────
    if not tools and _should_have_tools(user_message, state):
        nudge = (
            "Remember: you must respond ONLY with a JSON object in this exact format:\n"
            '{"reply": "...", "tools": [{"name": "...", "args": {...}}]}\n'
            "Do not write anything outside the JSON. "
            f"The player said: \"{user_message}\""
        )
        messages_retry = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user",      "content": nudge}
        ]
        response2 = await client.chat.completions.create(
            model      = MODEL,
            messages   = messages_retry,
            max_tokens = 600
        )
        raw2          = response2.choices[0].message.content
        reply2, tools2 = parse_response(raw2)

        # Use retry result only if it actually has tools
        if tools2:
            reply = reply2
            tools = tools2

    # ── Execute tools ─────────────────────────────────────────────────────────
    for tc in tools:
        name   = tc.get("name", "")
        args   = tc.get("args", {})
        if name:
            result = dispatch_tool(name, args, state)
            executed_tools.append({"name": name, "args": args})

    final_reply = reply if reply else raw
    state.questions_asked += 1
    messages.append({"role": "assistant", "content": final_reply})

    return {
        "reply":               final_reply,
        "tool_calls_executed": executed_tools,
        "updated_history":     [m for m in messages
                                if m.get("role") != "system"],
        "game_state":          state.__dict__
    }


def _should_have_tools(message: str, state: GameState) -> bool:
    """
    Heuristic — returns True when we strongly expect a tool call.
    Used to decide whether to retry with a nudge.
    """
    travel_keywords = [
        "خذني", "اذهب", "انتقل", "دعنا نذهب",
        "take me", "let's go", "go to", "visit"
    ]
    map_keywords = [
        "خريطة", "الخريطة", "افتح الخريطة",
        "map", "show map", "open map"
    ]
    direction_keywords = [
        "أين", "كيف أجد", "where is", "how do i find"
    ]
    badge_expected = state.scene_completable()

    msg_lower = message.lower()

    return (
        any(k in message for k in travel_keywords) or
        any(k in message for k in map_keywords) or
        any(k in message for k in direction_keywords) or
        badge_expected
    )