// js/main.js
// Entry point — imports all modules and wires them together.
// This is the only file that knows about all the other modules.

import { sendToAgent, SESSION_ID }    from './agent.js';
import { speakText }                  from './tts.js';
import { toggleMic }                  from './voice.js';
import { handleToolCalls }            from './tools.js';
import { setStatus, setLoading,
         appendMessage, showTools,
         initTTSToggle }              from './ui.js';

// ── TTS toggle — keep track of whether it's enabled ──────────────────────────
let getTTSEnabled = initTTSToggle(() => {});   // returns a getter function

// ── Core send flow ────────────────────────────────────────────────────────────
async function handleUserMessage(message) {
  message = message.trim();
  if (!message) return;

  // Clear input and show user message
  document.getElementById("text-input").value = "";
  appendMessage("user", message);

  setLoading(true);
  setStatus("مريم تفكر… · Thinking…", "thinking");

  try {
    // 1. Send to Python agent
    const data = await sendToAgent(message);

    // 2. Show Maryam's text reply
    appendMessage("maryam", data.reply);

    // 3. Show tool calls in debug bar
    showTools(data.tool_calls_executed);

    // 4. Execute tool calls (scene transitions, animations, UI panels…)
    handleToolCalls(data.tool_calls_executed ?? []);

    // 5. Speak the reply via Fanar Aura TTS
    if (getTTSEnabled() && data.reply) {
      await speakText(data.reply, setStatus);
    } else {
      setStatus("جاهز · Ready", "");
    }

  } catch (err) {
    appendMessage("maryam", `⚠️ خطأ في الاتصال · Connection error: ${err.message}`);
    setStatus("خطأ · Error", "");
    console.error(err);
  } finally {
    setLoading(false);
  }
}

// ── Wire up send button ───────────────────────────────────────────────────────
document.getElementById("send-btn").addEventListener("click", () => {
  handleUserMessage(document.getElementById("text-input").value);
});

// ── Wire up Enter key ─────────────────────────────────────────────────────────
document.getElementById("text-input").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleUserMessage(e.target.value);
  }
});

// ── Wire up mic button ────────────────────────────────────────────────────────
document.getElementById("mic-btn").addEventListener("click", () => {
  toggleMic(
    transcript => handleUserMessage(transcript),   // called when speech ends
    setStatus                                      // called for status updates
  );
});

// ── Boot ──────────────────────────────────────────────────────────────────────
appendMessage(
  "maryam",
  "مرحباً! أنا مريم. اكتب أو تكلم لتبدأ الرحلة. · Hello! I am Maryam. Type or speak to begin your journey."
);
setStatus(`Session: ${SESSION_ID}`);
