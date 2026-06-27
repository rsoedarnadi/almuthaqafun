# src/main.py
import os
import sys
import traceback
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from openai import OpenAI
from pydantic import BaseModel, Field

# Ensure environment variables are loaded from .env
load_dotenv()

from src.agent import run_turn
from src.storyline.storyline import GameState, StoryPhase
from src.tools.tools import dispatch_tool

app = FastAPI(title="Al Muthaqafun Backend Gate")

# ── Dynamic CORS Gateway ──────────────────────────────────────────────────────
# "null" allows files opened directly in browser tabs (file:// protocol).
# Keep allow_credentials=False when using wildcard origins.
ALLOWED_ORIGINS = ["*", "null"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Store local sessions in memory.
# NOTE: This is fine for local/dev. Use Redis/database if deployed with multiple workers.
sessions: dict[str, dict[str, Any]] = {}


def _serialize_state(state: GameState | dict[str, Any]) -> dict[str, Any]:
    """Convert GameState or state dict into JSON-safe values."""
    raw = state.__dict__ if isinstance(state, GameState) else dict(state)
    output: dict[str, Any] = {}

    for key, value in raw.items():
        if key not in GameState.__dataclass_fields__:
            continue
        if isinstance(value, StoryPhase):
            output[key] = value.value
        else:
            output[key] = value

    return output


def _deserialize_state(raw_state: dict[str, Any] | None) -> GameState:
    """Safely build GameState from client/session JSON."""
    raw_state = raw_state or {}
    clean_fields = {
        key: value
        for key, value in raw_state.items()
        if key in GameState.__dataclass_fields__
    }

    # Safely restore StoryPhase from API JSON.
    phase = clean_fields.get("current_phase")
    if isinstance(phase, str):
        try:
            clean_fields["current_phase"] = StoryPhase(phase)
        except ValueError:
            # Do not crash the API because of stale/bad frontend state.
            clean_fields["current_phase"] = StoryPhase.MAJLIS_INTRO

    # Normalize list-like fields so bad/null client values do not break prompt building.
    for list_field in ["explored_objects", "completed_scenes", "inventory", "badges"]:
        value = clean_fields.get(list_field)
        if value is None:
            clean_fields[list_field] = []
        elif not isinstance(value, list):
            clean_fields[list_field] = [value]

    # Normalize questions_asked.
    try:
        clean_fields["questions_asked"] = int(clean_fields.get("questions_asked", 0))
    except (TypeError, ValueError):
        clean_fields["questions_asked"] = 0

    return GameState(**clean_fields)


# Serve client.html at http://localhost:8000/
@app.get("/")
def serve_client():
    root = Path.cwd()
    candidates = [
        root / "client.html",
        root / "client" / "client.html",
        Path(__file__).resolve().parent.parent / "client.html",
        Path(__file__).resolve().parent.parent / "client" / "client.html",
    ]

    for path in candidates:
        if path.exists():
            return FileResponse(path)

    return JSONResponse(
        status_code=404,
        content={"error": "client.html not found in root, client/, project root, or project client/ directory"},
    )


# ── Fanar Speech/Aura client ──────────────────────────────────────────────────
try:
    tts_client = OpenAI(
        base_url=os.getenv("FANAR_BASE_URL", "https://api.fanar.qa/v1"),
        api_key=os.getenv("FANAR_API_KEY", ""),
    )
except Exception as e:
    print(f"[Warning] Failed to instantiate OpenAI client for TTS: {e}", file=sys.stderr)
    tts_client = None


# ── Request Validation Schemas ────────────────────────────────────────────────
class TurnRequest(BaseModel):
    session_id: str = "default"
    user_message: str
    history: list[dict[str, Any]] = Field(default_factory=list)
    game_state: dict[str, Any] = Field(default_factory=dict)


class ToolRequest(BaseModel):
    session_id: str = "default"
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    game_state: dict[str, Any] = Field(default_factory=dict)


class TTSRequest(BaseModel):
    text: str
    voice: str = "Amelia"


# ── REST API Endpoints ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_configured": bool(os.getenv("FANAR_API_KEY")),
        "model_configured": bool(os.getenv("FANAR_MODEL")),
        "base_url_configured": bool(os.getenv("FANAR_BASE_URL")),
    }


@app.post("/session/reset")
def reset_session(session_id: str = "default"):
    """Reset one local in-memory game session."""
    state = GameState()
    sessions[session_id] = _serialize_state(state)
    return {"ok": True, "session_id": session_id, "game_state": sessions[session_id]}


@app.post("/turn")
async def turn(req: TurnRequest):
    try:
        session_id = req.session_id or "default"

        # 1. Initialize session state if missing.
        if session_id not in sessions:
            sessions[session_id] = _serialize_state(GameState())

        # 2. Merge incoming client state updates over cached session state.
        raw_state = {**sessions[session_id], **(req.game_state or {})}
        state = _deserialize_state(raw_state)

        # 3. Run turn loop in agentic layer.
        result = await run_turn(req.user_message, req.history or [], state)

        # 4. Cache state changes locally as JSON-safe state.
        result_state = result.get("game_state", state)
        sessions[session_id] = _serialize_state(result_state)
        result["game_state"] = sessions[session_id]
        return result

    except Exception as err:
        print("\n" + "!" * 50)
        print(f"[CRITICAL ERROR] Error processing game turn for session: {req.session_id}")
        traceback.print_exc()
        print("!" * 50 + "\n")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(err),
                "detail": "Failed to compile LLM context or execute state mutation. Check terminal console.",
            },
        )


@app.post("/tool")
def tool(req: ToolRequest):
    """Run deterministic game tools for static client interactions."""
    try:
        session_id = req.session_id or "default"
        if session_id not in sessions:
            sessions[session_id] = _serialize_state(GameState())

        raw_state = {**sessions[session_id], **(req.game_state or {})}
        state = _deserialize_state(raw_state)
        result = dispatch_tool(req.tool_name, req.args or {}, state)

        sessions[session_id] = _serialize_state(state)
        return {
            "ok": True,
            "result": result,
            "tool_call": {"name": req.tool_name, "args": req.args or {}},
            "game_state": sessions[session_id],
        }

    except Exception as err:
        print("\n" + "!" * 50)
        print(f"[CRITICAL ERROR] Error processing tool call for session: {req.session_id}")
        traceback.print_exc()
        print("!" * 50 + "\n")
        return JSONResponse(
            status_code=500,
            content={"error": str(err), "detail": "Failed to execute deterministic tool call."},
        )


@app.post("/tts")
def tts(req: TTSRequest):
    """Convert Maryam's response text to speech using Fanar Aura TTS."""
    if not req.text.strip():
        return JSONResponse(status_code=400, content={"error": "TTS text cannot be empty."})

    if not tts_client or not os.getenv("FANAR_API_KEY"):
        return JSONResponse(
            status_code=500,
            content={"error": "FastAPI server has no active FANAR_API_KEY configured."},
        )

    try:
        print(f"[TTS Request] Generating speech for text: {req.text[:30]}...")
        response = tts_client.audio.speech.create(
            model=os.getenv("FANAR_TTS_MODEL", "Fanar-Aura-TTS-2"),
            input=req.text,
            voice=req.voice,
            response_format="mp3",
        )
        return Response(content=response.read(), media_type="audio/mpeg")

    except Exception as err:
        print("\n" + "!" * 50)
        print("[CRITICAL ERROR] Failed to synthesize premium speech stream.")
        traceback.print_exc()
        print("!" * 50 + "\n")
        return JSONResponse(
            status_code=500,
            content={"error": str(err), "detail": "Audio generation failed or timed out."},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
