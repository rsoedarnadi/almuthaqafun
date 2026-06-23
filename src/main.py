# main.py
import os
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from src.storyline.storyline import GameState, StoryPhase
from src.agent import run_turn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

sessions: dict[str, dict] = {}

# ── Fanar TTS client (sync — audio.speech doesn't support async) ──────────────
tts_client = OpenAI(
    base_url=os.getenv("FANAR_BASE_URL"),
    api_key=os.getenv("FANAR_API_KEY")
)

# ── Request models ────────────────────────────────────────────────────────────

class TurnRequest(BaseModel):
    session_id:   str
    user_message: str
    history:      list = []
    game_state:   dict = {}

class TTSRequest(BaseModel):
    text:  str
    voice: str = "Hamad"    # Hamad (male) or Amelia (female) — default Hamad

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/turn")
async def turn(req: TurnRequest):
    if req.session_id not in sessions:
        sessions[req.session_id] = GameState().__dict__

    raw   = {**sessions[req.session_id], **req.game_state}
    state = GameState(**{
        k: v for k, v in raw.items()
        if k in GameState.__dataclass_fields__
    })
    state.current_phase = StoryPhase(state.current_phase) \
        if isinstance(state.current_phase, str) else state.current_phase

    result = await run_turn(req.user_message, req.history, state)

    sessions[req.session_id] = result["game_state"]
    return result

@app.post("/tts")
def tts(req: TTSRequest):
    """
    Converts Maryam's text reply to Arabic speech using Fanar Aura TTS.
    Returns an mp3 audio file the frontend plays directly.
    Note: sync endpoint because OpenAI audio.speech.create is synchronous.
    """
    response = tts_client.audio.speech.create(
        model="Fanar-Aura-TTS-2",
        input=req.text,
        voice=req.voice,
        response_format="mp3"
    )
    return Response(content=response.read(), media_type="audio/mpeg")