// js/ui.js
// All DOM updates live here — no fetch, no audio, no game logic.

// ── Status bar ────────────────────────────────────────────────────────────────
export function setStatus(text, cls = "") {
  const el  = document.getElementById("status");
  el.textContent = text;
  el.className   = cls;
}

// ── Disable / enable input while waiting for agent ────────────────────────────
export function setLoading(on) {
  document.getElementById("send-btn").disabled      = on;
  document.getElementById("text-input").disabled    = on;
}

// ── Append a chat bubble to the conversation log ──────────────────────────────
export function appendMessage(role, text) {
  const log = document.getElementById("log");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="sender">${role === "user" ? "أنت · You" : "مريم · Maryam"}</div>
    <div>${text}</div>
  `;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

// ── Show tool calls in the debug bar ─────────────────────────────────────────
export function showTools(tools) {
  const el = document.getElementById("tools-log");
  if (!tools || tools.length === 0) {
    el.innerHTML = "<span style='opacity:0.3'>No tools called</span>";
    return;
  }
  el.innerHTML = tools
    .map(t => `<span>${t.name}</span>(${JSON.stringify(t.args)})`)
    .join("  ·  ");
}

// ── TTS toggle button ─────────────────────────────────────────────────────────
export function initTTSToggle(onToggle) {
  let enabled = true;
  const btn   = document.getElementById("tts-toggle");
  btn.addEventListener("click", () => {
    enabled = !enabled;
    btn.textContent = enabled ? "TTS ON" : "TTS OFF";
    btn.className   = enabled ? "on"     : "";
    onToggle(enabled);
  });
  return () => enabled;   // returns a getter — call it to read current state
}
