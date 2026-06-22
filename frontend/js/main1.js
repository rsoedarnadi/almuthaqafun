// js/main.js
import { sendToAgent, fetchTTS } from './agent.js';
import { handleToolCalls }       from './tools.js';
import { showDialogue }          from './ui.js';
import { toggleMic }             from './voice.js';
import { initScene }             from './scene.js';

// Boot
initScene("majlis");

// Send message flow
async function handleUserMessage(message) {
  if (!message.trim()) return;
  document.getElementById("text-input").value = "";
  showDialogue("أنت · You", message);

  try {
    document.getElementById("status-bar").textContent = "مريم تفكر…";
    const data = await sendToAgent(message);

    // Show reply
    showDialogue("مريم · Maryam", data.reply);

    // Play TTS
    const blob  = await fetchTTS(data.reply);
    const audio = new Audio(URL.createObjectURL(blob));
    audio.play();

    // Execute tool calls
    handleToolCalls(data.tool_calls_executed ?? []);

    document.getElementById("status-bar").textContent = "";

  } catch (err) {
    document.getElementById("status-bar").textContent = "خطأ · Error: " + err.message;
    console.error(err);
  }
}

// Wire up send button
document.getElementById("send-btn").addEventListener("click", () => {
  handleUserMessage(document.getElementById("text-input").value);
});

// Wire up Enter key
document.getElementById("text-input").addEventListener("keydown", e => {
  if (e.key === "Enter") handleUserMessage(e.target.value);
});

// Wire up mic button
document.getElementById("mic-btn").addEventListener("click", () => {
  toggleMic(transcript => handleUserMessage(transcript));
});