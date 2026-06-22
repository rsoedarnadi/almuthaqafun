// js/tts.js
// Plays Maryam's voice using the mp3 blob from agent.js fetchTTS().
// No fetch calls here — just blob → Audio → play.

import { fetchTTS } from './agent.js';

let currentAudio = null;

// ── Play a text reply as speech ───────────────────────────────────────────────
// Returns a Promise that resolves when audio finishes (or on error).
export async function speakText(text, onStatusChange) {
  onStatusChange("مريم تتكلم… · Speaking…", "speaking");
  document.getElementById("audio-indicator").style.display = "block";

  // Stop anything currently playing
  stopAudio();

  try {
    const blob = await fetchTTS(text, "Amelia");
    const url  = URL.createObjectURL(blob);
    currentAudio = new Audio(url);

    return new Promise((resolve) => {
      currentAudio.onended = () => {
        URL.revokeObjectURL(url);
        currentAudio = null;
        document.getElementById("audio-indicator").style.display = "none";
        onStatusChange("جاهز · Ready", "");
        resolve();
      };
      currentAudio.onerror = () => {
        URL.revokeObjectURL(url);
        currentAudio = null;
        document.getElementById("audio-indicator").style.display = "none";
        onStatusChange("جاهز · Ready", "");
        resolve();   // don't reject — TTS failure shouldn't break the flow
      };
      currentAudio.play().catch(() => resolve());
    });

  } catch (err) {
    console.warn("TTS failed:", err.message);
    document.getElementById("audio-indicator").style.display = "none";
    onStatusChange("جاهز (TTS unavailable) · Ready", "");
  }
}

// ── Play narration from a blob directly (used by transition.js) ──────────────
// Returns duration in ms so transition.js knows how long to wait.
export async function speakBlob(blob) {
  stopAudio();
  const url = URL.createObjectURL(blob);
  currentAudio = new Audio(url);

  return new Promise((resolve) => {
    currentAudio.onended = () => {
      URL.revokeObjectURL(url);
      currentAudio = null;
      resolve();
    };
    currentAudio.onerror = () => {
      URL.revokeObjectURL(url);
      currentAudio = null;
      resolve();
    };
    currentAudio.play().catch(() => resolve());
  });
}

export function stopAudio() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
}
