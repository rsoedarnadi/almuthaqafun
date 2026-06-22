// js/transition.js
// Handles the full cinematic transition sequence:
//   fade out → exterior shot + narration → fade in → interior scene
// No agent calls here — narration text comes from SCENE_INTROS (pre-written).

import { fetchTTS } from './agent.js';
import { speakBlob } from './tts.js';

// ── Pre-written exterior narrations (no API call needed — zero latency) ────────
const SCENE_INTROS = {
  zubarah: {
    title:     "قلعة الزبارة · Al Zubarah Fort",
    subtitle:  "UNESCO World Heritage Site · موقع التراث العالمي لليونسكو",
    narration: "أمامك قلعة الزبارة، بُنيت عام ١٩٣٨ لحماية مدينة الزبارة التجارية العريقة. هذه القلعة شاهدة على عصر اللؤلؤ والتجارة في قطر. Welcome to Al Zubarah Fort, built in 1938 to guard the ancient pearling town — a UNESCO World Heritage Site.",
    exterior:  "assets/exteriors/zubarah.jpg",
  },
  masjid: {
    title:     "مسجد فنار · Masjid Fanar",
    subtitle:  "Qatar Islamic Cultural Center · مركز قطر الإسلامي الثقافي",
    narration: "هذا هو مسجد فنار، رمز الثقافة الإسلامية في قطر. يتميز بمئذنته الحلزونية الفريدة المستوحاة من مساجد سامراء. This is Masjid Fanar — its iconic spiral minaret is inspired by the ancient minarets of Samarra, Iraq.",
    exterior:  "assets/exteriors/masjid.jpg",
  },
  majlis: {
    title:     "المجلس التقليدي · Traditional Majlis",
    subtitle:  "Heart of Qatari Hospitality · قلب الضيافة القطرية",
    narration: "المجلس هو قلب الضيافة القطرية، مكان يجتمع فيه الناس للحديث وتناول القهوة العربية. The majlis is where Qatari culture comes alive — through coffee, conversation, and community.",
    exterior:  "assets/exteriors/majlis.jpg",
  },
};

let isTransitioning = false;

// ── Main entry point — called by tools.js when transition_scene fires ─────────
export async function transitionToScene(sceneId) {
  if (isTransitioning) return;
  isTransitioning = true;

  const intro = SCENE_INTROS[sceneId];
  if (!intro) {
    console.warn("No intro defined for scene:", sceneId);
    isTransitioning = false;
    return;
  }

  // Phase 1 — fade current scene to black
  await fadeToBlack(500);

  // Phase 2 — show exterior image
  showExteriorPanel(intro);

  // Phase 3 — speak narration over exterior (wait for audio to finish)
  await playExteriorNarration(intro.narration);

  // Phase 4 — fade exterior to black
  await fadeToBlack(500);
  hideExteriorPanel();

  // Phase 5 — load interior scene (hook your Three.js loader here)
  await loadInteriorScene(sceneId);

  // Phase 6 — fade into interior
  await fadeIn(800);

  isTransitioning = false;
}

// ── Fade helpers ──────────────────────────────────────────────────────────────
function fadeToBlack(ms) {
  return new Promise(resolve => {
    const el = document.getElementById("fade-overlay");
    el.style.transition = `opacity ${ms}ms ease`;
    el.style.opacity    = "1";
    setTimeout(resolve, ms);
  });
}

function fadeIn(ms) {
  return new Promise(resolve => {
    const el = document.getElementById("fade-overlay");
    el.style.transition = `opacity ${ms}ms ease`;
    el.style.opacity    = "0";
    setTimeout(resolve, ms);
  });
}

// ── Exterior panel ────────────────────────────────────────────────────────────
function showExteriorPanel(intro) {
  document.getElementById("exterior-img").src            = intro.exterior;
  document.getElementById("exterior-title").textContent  = intro.title;
  document.getElementById("exterior-subtitle").textContent = intro.subtitle;

  const panel = document.getElementById("exterior-panel");
  panel.style.display = "flex";
  panel.style.opacity = "0";

  // Trigger CSS fade-in on next frame
  requestAnimationFrame(() => {
    panel.style.opacity = "1";
  });
}

function hideExteriorPanel() {
  const panel = document.getElementById("exterior-panel");
  panel.style.opacity = "0";
  panel.style.display = "none";
}

// ── Narration audio ───────────────────────────────────────────────────────────
async function playExteriorNarration(text) {
  try {
    const blob = await fetchTTS(text, "Amelia");
    await speakBlob(blob);
  } catch (err) {
    // TTS unavailable — just wait 4 seconds so user can read the subtitle
    console.warn("Narration TTS failed:", err.message);
    await new Promise(resolve => setTimeout(resolve, 4000));
  }
}

// ── Interior scene loader — replace with your Three.js code ──────────────────
async function loadInteriorScene(sceneId) {
  // TODO: your friend hooks their Three.js scene loader here
  // e.g. await SceneManager.load(sceneId);
  console.log(`[transition] Loading interior scene: ${sceneId}`);
  await new Promise(resolve => setTimeout(resolve, 300)); // placeholder
}
