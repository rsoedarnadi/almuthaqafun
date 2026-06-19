# agent.py

import json
from openai import AsyncOpenAI
import os
from src.storyline.storyline import GameState
from src.prompts.prompts import build_system_prompt
from src.tools.tools import TOOLS, dispatch_tool
from src.services.rag_client import retrieve_context

MODEL = "Fanar-S-2-27B"

client = AsyncOpenAI(
    api_key=os.getenv("HE97DqvdhSCgx7uD9q4UTeISlgWNml8p"),
    base_url=os.getenv("https://api.fanar.qa/v1")
)

async def run_turn(
    user_message:   str,
    history:        list,
    state:          GameState
) -> dict:

    # 1. Retrieve relevant cultural knowledge for this message
    rag_context = await retrieve_context(user_message, state.current_scene)

    # 2. Build messages
    system  = build_system_prompt(state, rag_context)
    messages = [{"role": "system", "content": system}] + history
    messages.append({"role": "user", "content": user_message})

    executed_tools = []

    # 3. Agent loop
    for _ in range(5):
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=500
        )

        msg = response.choices[0].message

        # Plain text reply — done
        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content})

            # Track questions asked (any plain reply = player asked something)
            state.questions_asked += 1

            break

        # Tool call — execute and loop
        messages.append(msg)
        for tc in msg.tool_calls:
            name   = tc.function.name
            args   = json.loads(tc.function.arguments)
            result = dispatch_tool(name, args, state)

            executed_tools.append({"name": name, "args": args})
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      result
            })

    final_reply = next(
        (m["content"] if isinstance(m, dict) else m.content
         for m in reversed(messages)
         if (isinstance(m, dict) and m.get("role") == "assistant")
         or (hasattr(m, "role") and m.role == "assistant")),
        "..."
    )

    # 4. Return everything Unity needs
    return {
        "reply":               final_reply,
        "tool_calls_executed": executed_tools,
        "updated_history":     [m for m in messages if
                                (isinstance(m, dict) and m.get("role") != "system")
                                or (hasattr(m, "role") and m.role != "system")],
        "game_state":          state.__dict__
    }