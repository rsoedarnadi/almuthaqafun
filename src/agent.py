#src/agent.py
import json
import os
import re
from dotenv import load_dotenv
from openai import AsyncOpenAI
from src.storyline.storyline import GameState, StoryPhase, SCENE_REQUIREMENTS
from src.prompts.prompts import SCENE_OBJECTS, build_system_prompt
from src.tools.tools import TOOLS, dispatch_tool

load_dotenv()

# --- DEFENSIVE ENVIRONMENT CONFIGURATION ---
# Default to the premium model and local Qatari endpoints if environment variables are missing
MODEL = os.getenv("FANAR_MODEL")

client = AsyncOpenAI(
    api_key=os.getenv("FANAR_API_KEY") or "missing-api-key",
    base_url=os.getenv("FANAR_BASE_URL") or "https://api.fanar.qa/v1",
)

print("\n========== FANAR CONFIG ==========")
print("MODEL:", MODEL)
print("BASE_URL:", os.getenv("FANAR_BASE_URL"))
print("API_KEY EXISTS:", bool(os.getenv("FANAR_API_KEY")))
print("=================================\n")


def _normalize_tool_call(tool: dict) -> dict | None:
    if not isinstance(tool, dict):
        return None

    name = (
        tool.get("name")
        or tool.get("tool")
        or tool.get("function")
        or tool.get("function_name")
    )
    args = tool.get("args") or tool.get("arguments") or tool.get("parameters") or {}

    # Accept compact forms such as {"transition_scene": {"scene_id": "masjid_ext"}}.
    if not name and len(tool) == 1:
        only_name, only_args = next(iter(tool.items()))
        name = only_name
        args = only_args if isinstance(only_args, dict) else {}

    if not isinstance(name, str):
        return None

    normalized_name = name.strip()
    name_aliases = {
        "animation_gesture_follow": "trigger_animation",
        "gesture_follow": "trigger_animation",
        "animation": "trigger_animation",
    }
    normalized_name = name_aliases.get(normalized_name, normalized_name)

    if not isinstance(args, dict):
        args = {}

    if normalized_name == "trigger_animation" and "animation" not in args:
        lowered = name.strip().lower()
        if "gesture" in lowered and "follow" in lowered:
            args = {**args, "animation": "gesture_follow"}

    if normalized_name == "transition_scene" and "scene_id" not in args:
        scene_id = args.get("scene") or args.get("target_scene") or args.get("destination")
        if scene_id:
            args = {**args, "scene_id": scene_id}

    return {"name": normalized_name, "args": args}


def _normalize_tools(value) -> list:
    if not isinstance(value, list):
        return []
    normalized = []
    for tool in value:
        normalized_tool = _normalize_tool_call(tool)
        if normalized_tool:
            normalized.append(normalized_tool)
    return normalized


def _parse_pseudo_tool_calls(text: str) -> tuple[str, list]:
    """
    Accept model slips like:
    "حسنًا... [trigger_animation(gesture_follow), transition_scene(masjid_ext)]"
    and convert them into the same normalized tool-call shape as JSON.
    """
    raw_tools = []

    for match in re.finditer(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)", text or ""):
        name = match.group(1).strip()
        arg_text = match.group(2).strip()
        args = {}

        if arg_text:
            parts = [part.strip() for part in arg_text.split(",") if part.strip()]
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    args[key.strip()] = value.strip().strip("\"'")
                elif name == "trigger_animation":
                    args["animation"] = part.strip().strip("\"'")
                elif name == "transition_scene":
                    args["scene_id"] = part.strip().strip("\"'")
                elif name == "open_ui":
                    args["panel"] = part.strip().strip("\"'")
                elif name == "explore_object":
                    args["object_id"] = part.strip().strip("\"'")

        raw_tools.append({"name": name, "args": args})

    tools = _normalize_tools(raw_tools)
    if not tools:
        return text, []

    cleaned_reply = re.sub(r"\s*\[[^\]]*[a-zA-Z_][a-zA-Z0-9_]*\s*\([^]]*\)\s*[^\]]*\]\s*", " ", text or "").strip()
    return cleaned_reply, tools


def _coerce_response_payload(data) -> tuple[str, list]:
    if isinstance(data, list):
        return "", _normalize_tools(data)
    if not isinstance(data, dict):
        return "", []

    reply = data.get("reply") or data.get("message") or data.get("text") or ""
    tools = data.get("tools") or data.get("tool_calls") or data.get("tool_calls_executed") or []

    # Accept {"reply": "...", "tool": {"name": "...", "args": {...}}}
    if not tools and isinstance(data.get("tool"), dict):
        tools = [data["tool"]]

    return reply, _normalize_tools(tools)


def parse_response(raw: str) -> tuple[str, list]:
    """
    Parses structural JSON outputs returned by the Fanar Agent.
    Falls back gracefully to clean plain text if parsing errors occur.
    Returns: (text_reply, extracted_tools_list)
    """
    clean = raw.strip()
    
    # Clean up standard Markdown triple-backtick fences if the LLM wrapped its JSON response
    if clean.startswith("```"):
        clean = re.sub(r"```(?:json)?", "", clean).strip().rstrip("```").strip()

    # Step A: Attempt direct full-string JSON parsing
    try:
        data = json.loads(clean)
        return _coerce_response_payload(data)
    except json.JSONDecodeError:
        pass

    # Step B: Substring fallback scanning (find outermost curly braces)
    match = re.search(r'(\{.*\})', clean, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return _coerce_response_payload(data)
        except json.JSONDecodeError:
            pass

    # Step C: Bare tools-array fallback.
    match = re.search(r'(\[.*\])', clean, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            reply, tools = _coerce_response_payload(data)
            if tools:
                return reply, tools
        except json.JSONDecodeError:
            pass

    # Step D: Pseudo tool-call fallback, e.g. [transition_scene(masjid_ext)].
    reply, tools = _parse_pseudo_tool_calls(clean)
    if tools:
        return reply, tools

    # Step E: Ultimate plain text fallback if JSON remains unparsable
    return raw.strip(), []


def _message_requests_transition(user_message: str) -> bool:
    msg = (user_message or "").lower()
    transition_keywords = [
        "خذني", "اذهب", "انتقل", "دعنا نذهب", "ادخل", "ندخل",
        "المشهد التالي", "مشهد آخر", "مكان آخر",
        "take me", "go to", "let's go", "lets go", "let’s go", "visit", "enter", "go inside",
        "next scene", "another scene", "move on",
    ]
    return any(keyword in msg for keyword in transition_keywords)


def _filter_transition_tools(user_message: str, tools: list) -> list:
    if _message_requests_transition(user_message):
        return tools
    return [
        tool for tool in tools
        if (tool or {}).get("name") != "transition_scene"
    ]


def _filter_model_award_badge_tools(tools: list) -> list:
    return [
        tool for tool in tools
        if (tool or {}).get("name") != "award_badge"
    ]


def _infer_requested_scene_id(user_message: str, current_scene: str) -> str | None:
    msg = (user_message or "").lower()

    if any(term in msg for term in ["masjid", "fanar", "mosque", "مسجد", "فنار"]):
        return "masjid" if current_scene == "masjid_ext" and any(term in msg for term in ["enter", "inside", "ادخل", "ندخل"]) else "masjid_ext"

    if any(term in msg for term in ["majlis", "مجلس"]):
        return "majlis" if current_scene == "majlis_ext" and any(term in msg for term in ["enter", "inside", "ادخل", "ندخل"]) else "majlis_ext"

    if any(term in msg for term in ["zubarah", "fort", "زبارة", "قلعة"]):
        return "zubarah"

    return None


def _ensure_requested_transition_tool(user_message: str, state: GameState, tools: list) -> list:
    if not _message_requests_transition(user_message):
        return tools
    if any((tool or {}).get("name") == "transition_scene" for tool in tools):
        return tools

    target_scene = _infer_requested_scene_id(user_message, state.current_scene)
    if not target_scene or target_scene == state.current_scene:
        return tools

    transition_lines = {
        "majlis_ext": "هيا بنا إلى المجلس. · Let us go to the majlis.",
        "majlis": "تفضّل، لندخل المجلس الآن. · Please come in; let us enter the majlis now.",
        "masjid_ext": "حسنًا، فلنبدأ رحلتنا نحو مسجد فنار. · Let us begin our journey to Masjid Fanar.",
        "masjid": "تفضّل، لندخل مسجد فنار الآن. · Please follow me; let us enter Masjid Fanar now.",
        "zubarah": "هيا بنا إلى قلعة الزبارة. · Let us go to Al Zubarah Fort.",
    }

    return tools + [
        {"name": "trigger_animation", "args": {"animation": "gesture_follow"}},
        {
            "name": "transition_scene",
            "args": {
                "scene_id": target_scene,
                "transition_line": transition_lines.get(target_scene, "هيا بنا. · Let us go."),
            },
        },
    ]


def _is_object_click_turn(user_message: str) -> bool:
    return bool(re.search(r"\bobject_click\b|\bobject_id\s*=", user_message or "", re.IGNORECASE))


def _scene_ready_for_badge_after_answer(state: GameState, user_message: str) -> bool:
    if _is_object_click_turn(user_message) or _message_requests_transition(user_message):
        return False
    reqs = SCENE_REQUIREMENTS.get(state.current_scene, {})
    badge_title = reqs.get("badge_title")
    req_objs = reqs.get("required_objects") or []
    if not badge_title or not req_objs or state.current_scene in state.completed_scenes:
        return False
    return all(obj in state.explored_objects for obj in req_objs)


def _ensure_award_badge_after_answer(user_message: str, state: GameState, tools: list) -> tuple[list, bool]:
    if not _scene_ready_for_badge_after_answer(state, user_message):
        return tools, False
    if any((tool or {}).get("name") == "award_badge" for tool in tools):
        return tools, False

    reqs = SCENE_REQUIREMENTS[state.current_scene]
    return tools + [{
        "name": "award_badge",
        "args": {
            "scene_name": state.current_scene,
            "badge_title": reqs["badge_title"],
            "congratulations": "أحسنت! أكملت استكشاف هذا المشهد. · Well done! You completed this scene.",
        },
    }], True


def _auto_transition_from_exterior(start_scene: str, user_message: str, tools: list) -> list:
    """
    Exterior scenes are transition-only cutscenes.
    After Maryam gives the exterior explanation, force the matching interior transition
    so the player never gets stuck waiting for the model to decide.
    """
    targets = {
        "majlis_ext": "majlis",
        "masjid_ext": "masjid",
    }
    target = targets.get(start_scene)
    if not target or not _message_requests_transition(user_message):
        return tools

    # Do not duplicate if the model already emitted a transition.
    if any((t or {}).get("name") == "transition_scene" for t in tools):
        return tools

    transition_lines = {
        "majlis_ext": "تفضّل، لندخل المجلس الآن. · Please come in; let us enter the majlis now.",
        "masjid_ext": "تفضّل، لندخل مسجد فنار الآن. · Please follow me; let us enter Masjid Fanar now.",
    }

    return tools + [
        {"name": "trigger_animation", "args": {"animation": "gesture_follow"}},
        {
            "name": "transition_scene",
            "args": {
                "scene_id": target,
                "transition_line": transition_lines[start_scene],
            },
        },
    ]


def _extract_clicked_object_id(user_message: str) -> str | None:
    """
    The browser sends object-click turns with an explicit object_id=... marker.
    Treat that marker as deterministic input instead of relying on the model to
    infer the clicked object from prose.
    """
    match = re.search(r"\bobject_id\s*=\s*([a-zA-Z0-9_:-]+)", user_message or "")
    return match.group(1) if match else None


def _ensure_explore_tool_for_clicked_object(user_message: str, state: GameState, tools: list) -> list:
    """
    Guarantee that 3D object clicks mutate GameState even if the model replies
    conversationally without emitting explore_object.
    """
    obj_id = _extract_clicked_object_id(user_message)
    if not obj_id:
        return tools

    required_objects = SCENE_OBJECTS.get(state.current_scene, {})
    if obj_id not in required_objects:
        return tools

    normalized_explore_tool = {
        "name": "explore_object",
        "args": {
            "object_id": obj_id,
            "spoken_context": required_objects[obj_id],
        },
    }

    non_explore_tools = [
        tool for tool in tools
        if (tool or {}).get("name") != "explore_object"
    ]

    return non_explore_tools + [normalized_explore_tool]


async def run_turn(
    user_message: str,
    history:      list,
    state:        GameState
) -> dict:
    """
    Executes a single interactive turn of Al Muthaqafun.
    Applies dual-turn retry heuristics to guarantee tool emission when expected.
    """
    # Capture the scene at the start of the turn. If it is an exterior scene,
    # this turn should behave like a short arrival cutscene and then transition
    # to the playable interior.
    start_scene = state.current_scene

    # 1. Build and compile prompt history
    system   = build_system_prompt(state)
    messages = [{"role": "system", "content": system}] + history
    messages.append({"role": "user", "content": user_message})

    executed_tools = []
    final_reply    = "..."

    # ── FIRST COMPLETION ATTEMPT ──
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=600,
        )
        raw = response.choices[0].message.content

    except Exception as e:
        import traceback

        print("\n========== OPENAI REQUEST FAILED ==========")
        print("MODEL:", MODEL)
        print("BASE_URL:", client.base_url)
        print("API_KEY:", os.getenv("FANAR_API_KEY"))
        traceback.print_exc()
        print("===========================================\n")

        raise

    reply, tools = parse_response(raw)

    # ── TWO-TURN COMPLIANCE NUDGE ──
    if not tools and _should_have_tools(user_message, state):
        # Tell the model exactly which tool is expected so the retry is precise
        msg_lower = user_message.lower()
        travel_kw = ["خذني","اذهب","انتقل","دعنا نذهب","take me","let's go","go to","visit"]
        map_kw    = ["خريطة","الخريطة","افتح الخريطة","map","show map","open map"]
        dir_kw    = ["أين","كيف أجد","where is","how do i find"]

        if any(k in msg_lower for k in travel_kw):
            hint = 'include "transition_scene" in your tools array'
        elif any(k in msg_lower for k in map_kw):
            hint = 'include "open_ui" with panel="map" in your tools array'
        elif any(k in msg_lower for k in dir_kw):
            hint = 'include "give_directions" in your tools array'
        else:
            hint = 'include the appropriate tool in your tools array'

        nudge = (
            f"Your previous response was not valid JSON. {hint}.\n"
            "Respond ONLY with a valid JSON object, no other text:\n"
            '{"reply": "...", "tools": [{"name": "...", "args": {...}}]}'
        )
        messages_retry = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user",      "content": nudge}
        ]
        
        try:
            response2 = await client.chat.completions.create(
                model=MODEL,
                messages=messages_retry,
                max_tokens=600
            )
            raw2 = response2.choices[0].message.content
            reply2, tools2 = parse_response(raw2)

            if tools2:
                reply = reply2
                tools = tools2
        except Exception:
            pass  # Fall back to original turn reply if the retry itself fails

    # ── EXTERIOR CUTSCENE AUTO-TRANSITION ──
    # Fanar sometimes explains the exterior correctly but forgets the tool call.
    # Force majlis_ext -> majlis and masjid_ext -> masjid after the explanation.
    tools = _ensure_explore_tool_for_clicked_object(user_message, state, tools)
    tools = _filter_transition_tools(user_message, tools)
    tools = _filter_model_award_badge_tools(tools)
    tools = _ensure_requested_transition_tool(user_message, state, tools)
    tools = _auto_transition_from_exterior(start_scene, user_message, tools)
    tools, appended_award_badge = _ensure_award_badge_after_answer(user_message, state, tools)

    # ── TOOL DISPATCH ENGINE ──
    for tc in tools:
        name = tc.get("name", "")
        args = tc.get("args", {})
        if name:
            result = dispatch_tool(name, args, state)
            executed_tools.append({"name": name, "args": args})

    final_reply = reply if reply else raw
    if appended_award_badge:
        final_reply = (
            f"{final_reply}\n\n"
            "أحسنت! أكملت استكشاف هذا المشهد وحصلت على الشارة. · "
            "Well done! You completed this scene and earned the badge."
        )

    if not _is_object_click_turn(user_message):
        state.questions_asked += 1
    messages.append({"role": "assistant", "content": final_reply})

    # Convert Enum fields to raw string keys to prevent JSON serialization errors in FastAPI
    serializable_state = {}
    for k, v in state.__dict__.items():
        if isinstance(v, StoryPhase):
            serializable_state[k] = v.value
        else:
            serializable_state[k] = v

    return {
        "reply":               final_reply,
        "tool_calls_executed": executed_tools,
        "updated_history":     [m for m in messages if m.get("role") != "system"],
        "game_state":          serializable_state
    }


def _should_have_tools(message: str, state: GameState) -> bool:
    """
    Scans the conversational turn for indicators that suggest a tool call is required.
    Returns False for exterior/transition scenes to avoid spurious retries.
    """
    # Transition scenes (majlis_ext, masjid_ext) complete instantly with 0 questions
    # and no objects — don't trigger the retry nudge for them or every turn fires it.
    TRANSITION_SCENES = {"majlis_ext", "masjid_ext"}
    if state.current_scene in TRANSITION_SCENES:
        return False

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
    msg_lower = message.lower()

    return (
        any(k in msg_lower for k in travel_keywords) or
        any(k in msg_lower for k in map_keywords) or
        any(k in msg_lower for k in direction_keywords)
    )
