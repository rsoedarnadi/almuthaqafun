// js/agent.js
// All communication with the Python backend lives here.
// No UI code, no audio code — just fetch calls.

const AGENT_URL  = "http://localhost:8000";
const SESSION_ID = "player_" + Math.random().toString(36).slice(2, 8);
let   history    = [];

export { SESSION_ID };

// ── Send a user message to the agent, get reply + tool calls ──────────────────
export async function sendToAgent(userMessage) {
  const res = await fetch(`${AGENT_URL}/turn`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id:   SESSION_ID,
      user_message: userMessage,
      history:      history,
      game_state:   {}
    })
  });

  if (!res.ok) throw new Error(`Agent error: ${res.status}`);

  const data = await res.json();
  history = data.updated_history ?? history;   // keep history up to date
  return data;   // { reply, tool_calls_executed, game_state }
}

// ── Request TTS audio from the backend, return an mp3 blob ───────────────────
export async function fetchTTS(text, voice = "Amelia") {
  const ttsUrl = document.getElementById("tts-url")?.value.trim()
               ?? `${AGENT_URL}/tts`;

  const res = await fetch(ttsUrl, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice })
  });

  if (!res.ok) throw new Error(`TTS error: ${res.status}`);
  return await res.blob();   // caller creates Audio from this
}
