# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from src.storyline.storyline import GameState, StoryPhase
from src.agent import run_turn          # ← fix this line

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

sessions: dict[str, dict] = {}

class TurnRequest(BaseModel):
    session_id:   str
    user_message: str
    history:      list = []
    game_state:   dict = {}

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

@app.get("/health")
def health():
    return {"status": "ok"}