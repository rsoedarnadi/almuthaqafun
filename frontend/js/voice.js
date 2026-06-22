// js/voice.js
// Browser Web Speech API — STT only.
// Calls onTranscript(text) when speech is finalised.
// No agent calls here — just mic → text.

let recognition = null;
let isRecording  = false;

export function initVoice(onTranscript, onStatusChange) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    alert("Speech recognition not supported. Please use Chrome.");
    return false;
  }

  recognition                = new SR();
  recognition.lang           = "ar-QA";   // Qatari Arabic, falls back to ar
  recognition.continuous     = false;
  recognition.interimResults = true;

  recognition.onstart = () => {
    isRecording = true;
    document.getElementById("mic-btn").classList.add("active");
    onStatusChange("جارٍ الاستماع… · Listening…", "listening");
  };

  recognition.onresult = (e) => {
    // Show interim transcript in the input box while speaking
    const transcript = Array.from(e.results)
      .map(r => r[0].transcript)
      .join("");
    document.getElementById("text-input").value = transcript;

    // Auto-send when speech is finalised
    if (e.results[e.results.length - 1].isFinal) {
      recognition.stop();
    }
  };

  recognition.onend = () => {
    isRecording = false;
    document.getElementById("mic-btn").classList.remove("active");

    const transcript = document.getElementById("text-input").value.trim();
    if (transcript) {
      onStatusChange("جاهز · Ready", "");
      onTranscript(transcript);   // hand off to main.js to send
    } else {
      onStatusChange("لم يتم التعرف على الكلام · No speech detected", "");
    }
  };

  recognition.onerror = (e) => {
    isRecording = false;
    document.getElementById("mic-btn").classList.remove("active");
    onStatusChange(`خطأ في الميكروفون · Mic error: ${e.error}`, "");
    console.error("STT error:", e.error);
  };

  return true;
}

export function toggleMic(onTranscript, onStatusChange) {
  if (!recognition) {
    if (!initVoice(onTranscript, onStatusChange)) return;
  }

  if (isRecording) {
    recognition.stop();
  } else {
    try {
      recognition.start();
    } catch (e) {
      // Recognition may already be running — ignore
      console.warn("STT start error:", e.message);
    }
  }
}
