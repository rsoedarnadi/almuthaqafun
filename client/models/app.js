import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const CONFIG = {
  backendUrl: "http://127.0.0.1:8000/vr/hotspot",

  // Fresh session every refresh so old backend progress does not instantly unlock badges.
  sessionId: `threejs-fanar-demo-${Date.now()}`,

  models: {
    majlisTent: "./assets/models/majlis_tent.glb",
    dallah: "./assets/models/dallah.glb",
    bakhoor: "./assets/models/bakhoor.glb",
    camel: "./assets/models/camel.glb",
    exterior: "./assets/models/fanar_exterior.glb",
    interior: `./assets/models/fanar_interior.glb?v=${Date.now()}`,
    imam: "./assets/models/imam.glb",
    quran: "./assets/models/quran.glb",
  },

  modelSetup: {
    majlisTent: {
      targetSize: 9.5,
      position: [0, 0, 0],
      rotation: [0, 0, 0],
    },

    camel: {
      targetSize: 1.35,
      position: [-5.2, 0, 2.05],
      rotation: [0, Math.PI * 0.18, 0],
    },

    dallah: {
      targetSize: 0.55,
      position: [0.0, 0.56, -0.82],
      rotation: [0, 0, 0],
    },

    bakhoor: {
      targetSize: 0.45,
      position: [0.9, 0.08, 0.18],
      rotation: [0, 0.2, 0],
    },

    exterior: {
      targetSize: 8.5,
      position: [0, 0, 0],
      rotation: [0, 0, 0],
    },

    interior: {
      // Bigger display size so your enlarged Blender room does not get normalized back too small.
      targetSize: 12.0,
      position: [0, 0, 0],
      rotation: [0, 0, 0],
    },

    quran: {
      targetSize: 1.0,
      position: [-1.15, 0, -2],
      rotation: [0, 0, 0],
    },

    imam: {
      // Smaller and moved closer to the podium.
      targetSize: 1.05,
      position: [1.35, 0, -1.85],

      // Flipped from Math.PI to 0 so he faces the other way.
      // If he is still backwards, change this to Math.PI.
      rotation: [0, 0, 0],
    },
  },

  camera: {
    majlis: {
      position: [0, 2.0, 8.0],
      target: [0, 1.2, 0],
    },

    fanar_exterior: {
      position: [0, 2.6, 7.0],
      target: [0, 1.35, 0],
    },

    fanar_interior: {
      // Opens inside the room instead of outside / inside the back wall.
      // If your GLB faces the opposite direction, swap the Z signs:
      // position: [0, 1.35, -2.65], target: [0, 1.25, 1.55]
      position: [0, 1.35, 2.65],
      target: [0, 1.25, -1.55],
    },
  },

  hotspots: {
    majlis_tent: {
      scene: "majlis",
      label: "Majlis Tent",
      position: [0, 1.25, 0.6],
      prompt: "Tell me about the traditional majlis tent.",
    },

    camel: {
      scene: "majlis",
      label: "Camel",
      position: [-5.2, 1.05, 2.05],
      prompt: "Tell me about the role of camels in desert life.",
    },

    dallah: {
      scene: "majlis",
      label: "Dallah",
      position: [0.0, 0.95, -0.82],
      prompt: "Tell me about the dallah and Arabic coffee hospitality.",
    },

    bakhoor: {
      scene: "majlis",
      label: "Bakhoor",
      position: [0.9, 0.62, 0.18],
      prompt: "Tell me about bakhoor incense in Qatari hospitality.",
    },

    campfire: {
      scene: "majlis",
      label: "Campfire",
      position: [-3.45, 0.55, 3.35],
      prompt: "Tell me about desert gatherings around fire.",
    },

    exterior_architecture: {
      scene: "fanar_exterior",
      label: "Architecture",
      position: [0, 2.15, 0.85],
      prompt: "Tell me about Fanar's exterior architecture.",
    },

    mihrab: {
      scene: "fanar_interior",
      label: "Mihrab",
      position: [0, 1.05, -1.55],
      prompt: "Tell me about the mihrab.",
    },

    quran: {
      scene: "fanar_interior",
      label: "Qur’an",
      position: [-1.15, 0.45, -2],
      prompt: "Tell me about the Qur’an.",
    },

    imam: {
      scene: "fanar_interior",
      label: "Imam",
      position: [1.35, 1.00, -1.85],
      prompt: "Tell me about the imam.",
    },
  },

  requiredObjects: ["majlis_tent", "camel", "dallah", "bakhoor", "campfire"],
  majlisRequiredObjects: ["majlis_tent", "camel", "dallah", "bakhoor", "campfire"],
  fanarRequiredObjects: ["exterior_architecture", "mihrab", "quran", "imam"],
};

const ui = {
  canvas: document.getElementById("threeCanvas"),
  loading: document.getElementById("loadingOverlay"),
  enterBtn: document.getElementById("enterBtn"),
  backBtn: document.getElementById("backBtn"),
  resetBtn: document.getElementById("resetBtn"),
  sceneBadge: document.getElementById("sceneBadge"),
  dialoguePanel: document.getElementById("dialoguePanel"),
  dialogueText: document.getElementById("dialogueText"),
  closeDialogueBtn: document.getElementById("closeDialogueBtn"),
  badgePopup: document.getElementById("badgePopup"),
  passportPanel: document.getElementById("passportPanel"),
  progressList: document.getElementById("progressList"),
  statusToast: document.getElementById("statusToast"),
  continueFanarBtn: document.getElementById("continueFanarBtn"),
};

let scene;
let camera;
let renderer;
let controls;
let loader;
let raycaster;
let pointer;

let majlisGroup;
let exteriorGroup;
let interiorGroup;
let hotspotGroup;
let majlisLightGroup;
let fanarLightGroup;
let sharedGround;
let majlisStars;
let currentSceneName = "majlis";

const hotspotMeshes = new Map();
const explored = new Set();
let selectedHotspotId = null;
let isSceneTransitioning = false;
let majlisCompleted = false;
let fanarUnlocked = false;
let transitionOverlay = null;

init();
await loadExperience();
animate();

function init() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x08090d);
  scene.fog = new THREE.Fog(0x08090d, 12, 28);

  camera = new THREE.PerspectiveCamera(
    55,
    window.innerWidth / window.innerHeight,
    0.02,
    100
  );

  renderer = new THREE.WebGLRenderer({
    canvas: ui.canvas,
    antialias: true,
    alpha: false,
  });

  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = false;

  // Normal zoom again. No tight interior restrictions.
  controls.minDistance = 0.15;
  controls.maxDistance = 9.0;
  controls.maxPolarAngle = Math.PI * 0.49;

  loader = new GLTFLoader();
  raycaster = new THREE.Raycaster();
  pointer = new THREE.Vector2();

  majlisGroup = new THREE.Group();
  majlisGroup.name = "MajlisNightDesertRoot";

  exteriorGroup = new THREE.Group();
  exteriorGroup.name = "FanarExteriorRoot";

  interiorGroup = new THREE.Group();
  interiorGroup.name = "FanarInteriorRoot";

  majlisLightGroup = new THREE.Group();
  majlisLightGroup.name = "MajlisNightLighting";

  fanarLightGroup = new THREE.Group();
  fanarLightGroup.name = "FanarLighting";

  hotspotGroup = new THREE.Group();
  hotspotGroup.name = "Hotspots";

  scene.add(majlisGroup);
  scene.add(exteriorGroup);
  scene.add(interiorGroup);
  scene.add(majlisLightGroup);
  scene.add(fanarLightGroup);
  scene.add(hotspotGroup);

  addLights();
  addSubtleGround();

  window.addEventListener("resize", onResize);
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("click", onClick);
  window.addEventListener("keydown", onKeyDown);

  ensureContinueFanarButton();

  ui.enterBtn.addEventListener("click", enterInteriorWithAnimation);
  ui.backBtn.addEventListener("click", () => showScene("fanar_exterior"));
  ui.continueFanarBtn.addEventListener("click", () => showScene("fanar_exterior"));
  ui.resetBtn.addEventListener("click", resetProgress);

  ui.closeDialogueBtn.addEventListener("click", () => {
    ui.dialoguePanel.style.display = "none";
  });

  ui.badgePopup.classList.add("hidden");
  ui.passportPanel.classList.add("hidden");

  updateProgressUI();
  showScene("majlis");
}

function addLights() {
  const hemi = new THREE.HemisphereLight(0xffedd0, 0x1f2430, 2.0);
  fanarLightGroup.add(hemi);

  const sun = new THREE.DirectionalLight(0xffdca3, 3.2);
  sun.position.set(4, 8, 6);
  fanarLightGroup.add(sun);

  const fill = new THREE.DirectionalLight(0xffffff, 0.85);
  fill.position.set(-4, 4, -5);
  fanarLightGroup.add(fill);

  const warmInteriorFill = new THREE.PointLight(0xffdfad, 1.4, 12);
  warmInteriorFill.name = "WarmInteriorFill";
  warmInteriorFill.position.set(0, 2.4, 0.8);
  fanarLightGroup.add(warmInteriorFill);
}

function addSubtleGround() {
  const geo = new THREE.CircleGeometry(10, 64);

  const mat = new THREE.MeshStandardMaterial({
    color: 0x19130d,
    roughness: 0.92,
    metalness: 0.0,
  });

  const ground = new THREE.Mesh(geo, mat);
  ground.name = "SubtleGround";
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.012;
  sharedGround = ground;
  scene.add(ground);
}

function ensureContinueFanarButton() {
  if (ui.continueFanarBtn) return ui.continueFanarBtn;

  const btn = document.createElement("button");
  btn.id = "continueFanarBtn";
  btn.textContent = "Continue to Fanar";
  btn.style.position = "fixed";
  btn.style.right = "32px";
  btn.style.bottom = "32px";
  btn.style.zIndex = "20";
  btn.style.display = "none";
  btn.style.padding = "16px 24px";
  btn.style.borderRadius = "999px";
  btn.style.border = "1px solid rgba(255,210,110,0.65)";
  btn.style.background = "linear-gradient(135deg, #ffd36b, #c18a2a)";
  btn.style.color = "#17110a";
  btn.style.fontWeight = "900";
  btn.style.fontSize = "16px";
  btn.style.cursor = "pointer";
  btn.style.boxShadow = "0 12px 30px rgba(0,0,0,0.35)";
  document.body.appendChild(btn);
  ui.continueFanarBtn = btn;
  return btn;
}

function createSandRippleTexture(grayscale = false) {
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;

  const ctx = canvas.getContext("2d");
  const image = ctx.createImageData(size, size);
  const data = image.data;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const nx = x / size;
      const ny = y / size;
      const ripple =
        Math.sin((nx * 18 + Math.sin(ny * 7) * 0.7) * Math.PI * 2) * 0.5 +
        Math.sin((ny * 13 + nx * 3.5) * Math.PI * 2) * 0.25;
      const shade = THREE.MathUtils.clamp(0.58 + ripple * 0.16, 0, 1);
      const i = (y * size + x) * 4;

      if (grayscale) {
        const v = Math.floor(shade * 255);
        data[i] = v;
        data[i + 1] = v;
        data[i + 2] = v;
      } else {
        data[i] = Math.floor(198 * shade + 78);
        data[i + 1] = Math.floor(164 * shade + 66);
        data[i + 2] = Math.floor(105 * shade + 42);
      }

      data[i + 3] = 255;
    }
  }

  ctx.putImageData(image, 0, 0);

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(8, 8);
  texture.colorSpace = THREE.SRGBColorSpace;

  return texture;
}

function createMajlisNightEnvironment() {
  const sandTexture = createSandRippleTexture(false);
  const sandBump = createSandRippleTexture(true);

  const sandMat = new THREE.MeshStandardMaterial({
    color: 0xd8b878,
    map: sandTexture,
    bumpMap: sandBump,
    bumpScale: 0.055,
    roughness: 0.96,
    metalness: 0.0,
  });

  const groundGeometry = new THREE.PlaneGeometry(38, 38, 34, 34);
  const groundPositions = groundGeometry.attributes.position;

  for (let i = 0; i < groundPositions.count; i++) {
    const x = groundPositions.getX(i);
    const y = groundPositions.getY(i);
    const softRipple =
      Math.sin(x * 0.45) * 0.014 +
      Math.cos(y * 0.42) * 0.012 +
      Math.sin((x + y) * 0.23) * 0.01;

    // Local Z becomes world Y after the ground is rotated flat.
    groundPositions.setZ(i, softRipple);
  }

  groundGeometry.computeVertexNormals();

  const ground = new THREE.Mesh(groundGeometry, sandMat);
  ground.name = "Majlis_Night_Desert_Sand_Ground";
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.085;
  ground.receiveShadow = true;
  majlisGroup.add(ground);

  createMajlisStars();
  createMajlisLowTable();
  createMajlisCampfire();
  createMajlisLighting();
}

function createMajlisStars() {
  const starCount = 280;
  const positions = new Float32Array(starCount * 3);

  for (let i = 0; i < starCount; i++) {
    const radius = THREE.MathUtils.randFloat(13, 24);
    const angle = THREE.MathUtils.randFloat(0, Math.PI * 2);
    const height = THREE.MathUtils.randFloat(6.5, 15.5);

    positions[i * 3] = Math.cos(angle) * radius;
    positions[i * 3 + 1] = height;
    positions[i * 3 + 2] = Math.sin(angle) * radius;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

  const material = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 2.2,
    sizeAttenuation: false,
    transparent: true,
    opacity: 0.92,
    depthWrite: false,
  });

  majlisStars = new THREE.Points(geometry, material);
  majlisStars.name = "Majlis_Soft_Twinkling_Stars";
  majlisGroup.add(majlisStars);
}

function createMajlisLowTable() {
  const woodMat = new THREE.MeshStandardMaterial({
    color: 0x3b1f0d,
    roughness: 0.78,
    metalness: 0.0,
  });

  const trayMat = new THREE.MeshStandardMaterial({
    color: 0xb6823a,
    roughness: 0.55,
    metalness: 0.22,
  });

  const table = new THREE.Group();
  table.name = "Majlis_Low_Table_Tray";
  table.position.set(0, 0, -0.82);
  table.rotation.y = Math.PI / 2;

  const top = new THREE.Mesh(new THREE.BoxGeometry(1.55, 0.12, 0.72), woodMat);
  top.name = "Majlis_Low_Table_Top";
  top.position.y = 0.28;
  table.add(top);

  const tray = new THREE.Mesh(new THREE.BoxGeometry(1.22, 0.045, 0.48), trayMat);
  tray.name = "Majlis_Simple_Service_Tray";
  tray.position.y = 0.36;
  table.add(tray);

  for (const x of [-0.58, 0.58]) {
    for (const z of [-0.22, 0.22]) {
      const leg = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.28, 0.08), woodMat);
      leg.name = "Majlis_Low_Table_Leg";
      leg.position.set(x, 0.12, z);
      table.add(leg);
    }
  }

  majlisGroup.add(table);
}

function createMajlisCampfire() {
  const fireGroup = new THREE.Group();
  fireGroup.name = "Majlis_Warm_Campfire";
  fireGroup.position.set(-3.45, 0, 3.35);

  const stoneMat = new THREE.MeshStandardMaterial({
    color: 0x3b3025,
    roughness: 0.9,
  });

  const logMat = new THREE.MeshStandardMaterial({
    color: 0x3a1b08,
    roughness: 0.8,
  });

  const flameMat = new THREE.MeshBasicMaterial({
    color: 0xff8a24,
    transparent: true,
    opacity: 0.88,
    side: THREE.DoubleSide,
  });

  for (let i = 0; i < 10; i++) {
    const a = (Math.PI * 2 * i) / 10;
    const stone = new THREE.Mesh(new THREE.DodecahedronGeometry(0.12, 0), stoneMat);
    stone.name = "Campfire_Stone_Ring";
    stone.position.set(Math.cos(a) * 0.48, 0.08, Math.sin(a) * 0.48);
    fireGroup.add(stone);
  }

  for (const rot of [-0.55, 0.55]) {
    const log = new THREE.Mesh(new THREE.BoxGeometry(0.86, 0.13, 0.16), logMat);
    log.name = "Campfire_Wood_Log";
    log.position.y = 0.12;
    log.rotation.y = rot;
    fireGroup.add(log);
  }

  const flame1 = new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.55, 7), flameMat);
  flame1.name = "Campfire_Stylized_Flame";
  flame1.position.y = 0.45;
  fireGroup.add(flame1);

  const flame2 = new THREE.Mesh(new THREE.ConeGeometry(0.14, 0.38, 7), flameMat.clone());
  flame2.material.color.set(0xffd76b);
  flame2.name = "Campfire_Inner_Flame";
  flame2.position.y = 0.48;
  fireGroup.add(flame2);

  const fireLight = new THREE.PointLight(0xff8a32, 3.8, 10);
  fireLight.name = "Majlis_Campfire_Point_Light";
  fireLight.position.set(0, 0.75, 0);
  fireLight.shadow = false;
  fireGroup.add(fireLight);

  majlisGroup.add(fireGroup);
}

function createMajlisLighting() {
  const hemi = new THREE.HemisphereLight(0x536f9f, 0x3a1f0d, 1.75);
  hemi.name = "Majlis_Night_Hemisphere_Light";
  majlisLightGroup.add(hemi);

  const moon = new THREE.DirectionalLight(0xb6cfff, 1.15);
  moon.name = "Majlis_Soft_Moonlight";
  moon.position.set(-6, 8, 6);
  majlisLightGroup.add(moon);

  const tentWarm = new THREE.PointLight(0xffc477, 4.2, 16);
  tentWarm.name = "Majlis_Tent_Warm_Lantern_Fill";
  tentWarm.position.set(2.7, 2.45, -0.35);
  majlisLightGroup.add(tentWarm);

  const tentWarmOtherSide = new THREE.PointLight(0xffc477, 3.4, 15);
  tentWarmOtherSide.name = "Majlis_Tent_Warm_Lantern_Fill_Other_Side";
  tentWarmOtherSide.position.set(-2.7, 2.45, -0.35);
  majlisLightGroup.add(tentWarmOtherSide);

  const entranceGlow = new THREE.PointLight(0xffa85c, 2.8, 11);
  entranceGlow.name = "Majlis_Entrance_Warm_Glow";
  entranceGlow.position.set(0, 1.35, 2.35);
  majlisLightGroup.add(entranceGlow);
}

function addInteriorCeiling() {
  // Intentionally no-op.
  // The previous fake plane caused the beige slab to hang visibly above the box.
  // The real GLB ceiling is fixed through fixVeryDarkInteriorMaterials() instead.
}

async function loadExperience() {
  showToast("Loading models...");

  createMajlisNightEnvironment();

  const majlisTent = await loadGLBOrPlaceholder(CONFIG.models.majlisTent, "Majlis Tent");
  prepareModel(majlisTent, CONFIG.modelSetup.majlisTent);
  majlisGroup.add(majlisTent);

  const camel = await loadGLBOrPlaceholder(CONFIG.models.camel, "Camel");
  prepareModel(camel, CONFIG.modelSetup.camel);
  majlisGroup.add(camel);

  const dallah = await loadGLBOrPlaceholder(CONFIG.models.dallah, "Dallah");
  prepareModel(dallah, CONFIG.modelSetup.dallah);
  majlisGroup.add(dallah);

  const bakhoor = await loadGLBOrPlaceholder(CONFIG.models.bakhoor, "Bakhoor");
  prepareModel(bakhoor, CONFIG.modelSetup.bakhoor);
  majlisGroup.add(bakhoor);

  const exterior = await loadGLBOrPlaceholder(CONFIG.models.exterior, "Fanar Exterior");
  prepareModel(exterior, CONFIG.modelSetup.exterior);
  exteriorGroup.add(exterior);

  const interior = await loadGLBOrPlaceholder(CONFIG.models.interior, "Fanar Interior");
  prepareModel(interior, CONFIG.modelSetup.interior);

  // Tries to fix black ceiling/roof materials if Blender exported them too dark.
  fixVeryDarkInteriorMaterials(interior);

  interiorGroup.add(interior);

  // Do not add a fake ceiling plane. It hangs above the room when the model is viewed
  // from outside/top angles. We fix the real GLB ceiling material instead.

  const quran = await loadGLBOrPlaceholder(CONFIG.models.quran, "Qur’an");
  prepareModel(quran, CONFIG.modelSetup.quran);
  interiorGroup.add(quran);

  const imam = await loadGLBOrPlaceholder(CONFIG.models.imam, "Imam");
  prepareModel(imam, CONFIG.modelSetup.imam);
  interiorGroup.add(imam);

  createHotspots();

  // Important: apply scene visibility after hotspots exist.
  showScene(currentSceneName);

  ui.loading.classList.add("hidden");
  showDialogue("Welcome to the Majlis Night Desert. Explore the tent, camel, dallah, bakhoor, and campfire.");
  showToast("Experience loaded");
}

function loadGLBOrPlaceholder(path, label) {
  return new Promise((resolve) => {
    loader.load(
      path,
      (gltf) => {
        const model = gltf.scene;
        model.name = label;
        resolve(model);
      },
      undefined,
      (error) => {
        console.warn(`Could not load ${path}`, error);
        resolve(createPlaceholder(label));
      }
    );
  });
}

function createPlaceholder(label) {
  const group = new THREE.Group();
  group.name = `${label}_Placeholder`;

  const geo = new THREE.BoxGeometry(1.5, 1, 1.5);

  const mat = new THREE.MeshStandardMaterial({
    color: 0x3b2a1a,
    roughness: 0.8,
  });

  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.y = 0.5;
  group.add(mesh);

  const sprite = makeTextSprite(`${label}\nmissing GLB`, {
    fontSize: 42,
    background: "rgba(60,0,0,0.78)",
    color: "#fff0d7",
  });

  sprite.position.set(0, 1.45, 0);
  sprite.scale.set(1.6, 0.75, 1);
  group.add(sprite);

  return group;
}

function prepareModel(model, setup) {
  fitObjectToSize(model, setup.targetSize);

  model.position.set(setup.position[0], setup.position[1], setup.position[2]);
  model.rotation.set(setup.rotation[0], setup.rotation[1], setup.rotation[2]);

  model.traverse((child) => {
    if (!child.isMesh) return;

    child.castShadow = false;
    child.receiveShadow = true;

    if (child.material) {
      const mats = Array.isArray(child.material) ? child.material : [child.material];

      for (const mat of mats) {
        mat.side = THREE.DoubleSide;
        mat.needsUpdate = true;
      }
    }
  });
}

function fixVeryDarkInteriorMaterials(model) {
  const beigeCeiling = new THREE.MeshBasicMaterial({
    name: "Forced_Beige_Ceiling_Material",
    color: 0xd8c59e,
    side: THREE.DoubleSide,
    toneMapped: false,
  });

  const warmCreamCeiling = new THREE.MeshBasicMaterial({
    name: "Forced_Warm_Cream_Ceiling_Material",
    color: 0xe6d8b8,
    side: THREE.DoubleSide,
    toneMapped: false,
  });

  const goldLightMaterial = new THREE.MeshBasicMaterial({
    name: "Forced_Gold_Ceiling_Light_Material",
    color: 0xffdc86,
    side: THREE.DoubleSide,
    toneMapped: false,
  });

  model.traverse((child) => {
    if (!child.isMesh || !child.material) return;

    const objectName = `${child.name || ""}`.toLowerCase();
    const materialName = Array.isArray(child.material)
      ? child.material.map((m) => m?.name || "").join(" ").toLowerCase()
      : `${child.material?.name || ""}`.toLowerCase();

    const name = `${objectName} ${materialName}`;

    const isCeiling =
      name.includes("ceiling") ||
      name.includes("roof") ||
      name.includes("dome") ||
      name.includes("tray") ||
      name.includes("cove") ||
      name.includes("recess");

    const isCeilingLight =
      name.includes("light") ||
      name.includes("stained") ||
      name.includes("glass") ||
      name.includes("gold") ||
      name.includes("ring") ||
      name.includes("disc") ||
      name.includes("spotlight");

    // Main ceiling / tray / roof surfaces: force beige.
    if (isCeiling && !isCeilingLight) {
      child.material = beigeCeiling.clone();
      child.material.needsUpdate = true;
      return;
    }

    // Ceiling decorative rings/discs/lights: force visible warm gold instead of black.
    if (isCeiling && isCeilingLight) {
      child.material = goldLightMaterial.clone();
      child.material.needsUpdate = true;
      return;
    }

    // General safety: prevent black backside rendering on all interior meshes.
    const mats = Array.isArray(child.material) ? child.material : [child.material];

    for (const mat of mats) {
      if (!mat) continue;

      mat.side = THREE.DoubleSide;

      if (mat.color) {
        const maxChannel = Math.max(mat.color.r, mat.color.g, mat.color.b);

        if (maxChannel < 0.04) {
          mat.map = null;
          mat.aoMap = null;
          mat.lightMap = null;
          mat.color.set(0xd8c59e);

          if (mat.emissive) {
            mat.emissive.set(0x1a1208);
            mat.emissiveIntensity = 0.25;
          }
        }
      }

      mat.needsUpdate = true;
    }
  });
}

function fitObjectToSize(object, targetSize) {
  let box = new THREE.Box3().setFromObject(object);
  const size = new THREE.Vector3();
  box.getSize(size);

  const maxDim = Math.max(size.x, size.y, size.z);

  if (!Number.isFinite(maxDim) || maxDim <= 0) return;

  const scale = targetSize / maxDim;
  object.scale.multiplyScalar(scale);

  box = new THREE.Box3().setFromObject(object);
  const center = new THREE.Vector3();
  box.getCenter(center);

  object.position.x -= center.x;
  object.position.z -= center.z;
  object.position.y -= box.min.y;
}

function showScene(name, options = {}) {
  const { preserveCamera = false, silent = false } = options;
  currentSceneName = name;

  if (name === "majlis") {
    scene.background = new THREE.Color(0x081226);
    scene.fog = new THREE.Fog(0x081226, 18, 42);
  } else if (name === "fanar_interior") {
    scene.background = new THREE.Color(0x08090d);
    scene.fog = null;
  } else {
    scene.background = new THREE.Color(0x08090d);
    scene.fog = new THREE.Fog(0x08090d, 12, 28);
  }

  majlisGroup.visible = name === "majlis";
  exteriorGroup.visible = name === "fanar_exterior";
  interiorGroup.visible = name === "fanar_interior";
  majlisLightGroup.visible = name === "majlis";
  fanarLightGroup.visible = name !== "majlis";

  if (sharedGround) {
    sharedGround.visible = name !== "majlis";
  }

  for (const [id, mesh] of hotspotMeshes) {
    const sceneName = CONFIG.hotspots[id].scene;
    const shouldShow = sceneName === name;

    if (mesh.userData.parentGroup) {
      mesh.userData.parentGroup.visible = shouldShow;
    }

    mesh.visible = shouldShow;

    if (mesh.userData.labelSprite) {
      mesh.userData.labelSprite.visible = false;
    }
  }

  const cameraConfig = CONFIG.camera[name];

  if (!preserveCamera && cameraConfig) {
    camera.position.set(...cameraConfig.position);
    controls.target.set(...cameraConfig.target);
  }

  if (name === "majlis") {
    controls.enablePan = true;
    controls.screenSpacePanning = true;
    controls.minDistance = 1.0;
    controls.maxDistance = 14.0;
    controls.minPolarAngle = 0;
    controls.maxPolarAngle = Math.PI * 0.58;
    controls.minAzimuthAngle = -Infinity;
    controls.maxAzimuthAngle = Infinity;
  } else if (name === "fanar_interior") {
    controls.enablePan = true;
    controls.screenSpacePanning = true;
    controls.minDistance = 0.08;
    controls.maxDistance = 12.0;
    controls.minPolarAngle = 0;
    controls.maxPolarAngle = Math.PI * 0.64;
    controls.minAzimuthAngle = -Infinity;
    controls.maxAzimuthAngle = Infinity;
  } else {
    controls.enablePan = false;
    controls.minDistance = 0.5;
    controls.maxDistance = 9.0;
    controls.minPolarAngle = 0;
    controls.maxPolarAngle = Math.PI * 0.49;
    controls.minAzimuthAngle = -Infinity;
    controls.maxAzimuthAngle = Infinity;
  }

  controls.update();

  ui.enterBtn.style.display = name === "fanar_exterior" ? "block" : "none";
  ui.backBtn.style.display = name === "fanar_interior" ? "block" : "none";
  ui.continueFanarBtn.style.display =
    name === "majlis" && majlisCompleted ? "block" : "none";

  const sceneLabels = {
    majlis: "Majlis",
    fanar_exterior: "Fanar Exterior",
    fanar_interior: "Fanar Interior",
  };

  ui.sceneBadge.textContent = sceneLabels[name] || name;

  if (!silent) {
    if (name === "majlis") {
      showDialogue("Explore the Majlis Night Desert: tent, camel, dallah, bakhoor, and campfire.");
    } else if (name === "fanar_interior") {
      showDialogue("You are now inside Fanar. Click the mihrab, Qur’an, and imam markers.");
    } else {
      showDialogue("You are outside Fanar. Click the architecture marker or enter the mosque.");
    }
  }
}

function getTransitionOverlay() {
  if (transitionOverlay) return transitionOverlay;

  transitionOverlay = document.createElement("div");
  transitionOverlay.id = "sceneTransitionOverlay";
  transitionOverlay.style.position = "fixed";
  transitionOverlay.style.inset = "0";
  transitionOverlay.style.background =
    "radial-gradient(circle at center, rgba(255,221,157,0.18), rgba(8,9,13,0.96) 68%)";
  transitionOverlay.style.opacity = "0";
  transitionOverlay.style.pointerEvents = "none";
  transitionOverlay.style.zIndex = "9999";
  transitionOverlay.style.transition = "none";
  document.body.appendChild(transitionOverlay);

  return transitionOverlay;
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function animateCameraMove({
  fromPosition,
  toPosition,
  fromTarget,
  toTarget,
  duration = 900,
  onUpdate,
  onComplete,
}) {
  const start = performance.now();

  function step(now) {
    const raw = Math.min((now - start) / duration, 1);
    const t = easeInOutCubic(raw);

    camera.position.lerpVectors(fromPosition, toPosition, t);
    controls.target.lerpVectors(fromTarget, toTarget, t);

    if (onUpdate) onUpdate(raw, t);

    controls.update();

    if (raw < 1) {
      requestAnimationFrame(step);
    } else if (onComplete) {
      onComplete();
    }
  }

  requestAnimationFrame(step);
}

function enterInteriorWithAnimationLegacy() {
  if (isSceneTransitioning || currentSceneName === "fanar_interior") return;

  isSceneTransitioning = true;
  controls.enabled = false;
  ui.enterBtn.style.pointerEvents = "none";

  const overlay = getTransitionOverlay();

  const startPosition = camera.position.clone();
  const startTarget = controls.target.clone();

  // Exterior dolly-in: move forward toward the current exterior target/entrance.
  const forward = startTarget.clone().sub(startPosition).normalize();
  const exteriorPushPosition = startPosition.clone().add(forward.multiplyScalar(3.2));
  exteriorPushPosition.y = Math.max(exteriorPushPosition.y * 0.82, 1.15);
  const exteriorPushTarget = startTarget.clone();

  animateCameraMove({
    fromPosition: startPosition,
    toPosition: exteriorPushPosition,
    fromTarget: startTarget,
    toTarget: exteriorPushTarget,
    duration: 850,
    onUpdate: (raw) => {
      overlay.style.opacity = String(Math.min(raw * 1.25, 1));
    },
    onComplete: () => {
      // Switch scenes while covered, then glide into the interior camera.
      showScene("fanar_interior", { preserveCamera: true, silent: true });

      const finalPosition = new THREE.Vector3(...CONFIG.camera.fanar_interior.position);
      const finalTarget = new THREE.Vector3(...CONFIG.camera.fanar_interior.target);
      const entryPosition = finalPosition.clone().add(new THREE.Vector3(0, 0.05, 1.15));
      const entryTarget = finalTarget.clone().add(new THREE.Vector3(0, 0.0, 0.45));

      camera.position.copy(entryPosition);
      controls.target.copy(entryTarget);
      controls.update();

      animateCameraMove({
        fromPosition: entryPosition,
        toPosition: finalPosition,
        fromTarget: entryTarget,
        toTarget: finalTarget,
        duration: 950,
        onUpdate: (raw) => {
          overlay.style.opacity = String(1 - raw);
        },
        onComplete: () => {
          overlay.style.opacity = "0";
          controls.enabled = true;
          ui.enterBtn.style.pointerEvents = "";
          isSceneTransitioning = false;
          showDialogue("You are now inside Fanar. Click the mihrab, Qur’an, and imam markers.");
        },
      });
    },
  });
}

function enterInteriorWithAnimation() {
  if (isSceneTransitioning || currentSceneName === "fanar_interior") return;

  isSceneTransitioning = true;
  controls.enabled = false;
  ui.enterBtn.style.pointerEvents = "none";
  ui.backBtn.style.pointerEvents = "none";

  const overlay = getTransitionOverlay();
  overlay.style.opacity = "0";

  // Simple, reliable transition:
  // fade exterior out, switch scene while hidden, then fade interior in.
  // No zooming through the 3D model, so it cannot get stuck on the tower.
  const fadeOutDuration = 900;
  const fadeOutStartedAt = performance.now();

  function fadeOut(now) {
    const raw = Math.min((now - fadeOutStartedAt) / fadeOutDuration, 1);
    const t = easeInOutCubic(raw);
    overlay.style.opacity = String(t);

    if (raw < 1) {
      requestAnimationFrame(fadeOut);
      return;
    }

    // Switch while fully hidden. showScene() sets the correct interior camera,
    // visibility, buttons, badge, controls, and hotspots.
    showScene("fanar_interior", { silent: true });
    controls.update();

    const fadeInDuration = 650;
    const fadeInStartedAt = performance.now();

    function fadeIn(fadeNow) {
      const fadeRaw = Math.min((fadeNow - fadeInStartedAt) / fadeInDuration, 1);
      const fadeT = easeInOutCubic(fadeRaw);
      overlay.style.opacity = String(1 - fadeT);

      if (fadeRaw < 1) {
        requestAnimationFrame(fadeIn);
        return;
      }

      overlay.style.opacity = "0";
      controls.enabled = true;
      ui.enterBtn.style.pointerEvents = "";
      ui.backBtn.style.pointerEvents = "";
      isSceneTransitioning = false;
      showDialogue("You are now inside Fanar. Click the mihrab, Qur’an, and imam markers.");
    }

    requestAnimationFrame(fadeIn);
  }

  requestAnimationFrame(fadeOut);
}

function clampInteriorCamera() {
  if (currentSceneName !== "fanar_interior") return;

  // Light clamp only:
  // - keeps camera below the ceiling so you do not fly above the room
  // - does NOT clamp X/Z, so you can still move around freely
  // - does NOT change your configured starting position/item positions
  camera.position.y = THREE.MathUtils.clamp(camera.position.y, 0.65, 3.25);
  controls.target.y = THREE.MathUtils.clamp(controls.target.y, 0.75, 2.6);
}

function createHotspots() {
  const baseMat = new THREE.MeshStandardMaterial({
    color: 0xffd46b,
    emissive: 0xffc861,
    emissiveIntensity: 0.7,
    roughness: 0.25,
    metalness: 0.08,
    transparent: true,
    opacity: 0.55,
    depthWrite: false,
  });

  const ringMat = new THREE.MeshBasicMaterial({
    color: 0xffe4a6,
    transparent: true,
    opacity: 0.28,
    side: THREE.DoubleSide,
    depthWrite: false,
  });

  for (const [id, data] of Object.entries(CONFIG.hotspots)) {
    const group = new THREE.Group();
    group.name = `Hotspot_${id}`;
    group.position.set(...data.position);

    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.065, 24, 16),
      baseMat.clone()
    );

    sphere.name = `Clickable_${id}`;
    sphere.userData.hotspotId = id;
    sphere.userData.prompt = data.prompt;
    sphere.userData.isHotspot = true;
    sphere.userData.parentGroup = group;

    group.add(sphere);

    const ring = new THREE.Mesh(
      new THREE.RingGeometry(0.095, 0.12, 36),
      ringMat.clone()
    );

    ring.name = `Hotspot_Ring_${id}`;
    ring.rotation.x = -Math.PI / 2;
    ring.userData.ignoreRaycast = true;

    group.add(ring);

    const label = makeTextSprite(data.label, {
      fontSize: 42,
      background: "rgba(10,10,14,0.72)",
      color: "#f5ead6",
    });

    label.position.set(0, 0.2, 0);
    label.scale.set(0.45, 0.14, 1);
    label.visible = false;

    group.add(label);

    sphere.userData.labelSprite = label;
    sphere.userData.ring = ring;

    hotspotGroup.add(group);
    hotspotMeshes.set(id, sphere);
  }
}

function makeTextSprite(text, options = {}) {
  const fontSize = options.fontSize ?? 40;
  const bg = options.background ?? "rgba(0,0,0,0.7)";
  const color = options.color ?? "#ffffff";

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  canvas.width = 512;
  canvas.height = 180;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  roundRect(ctx, 18, 18, canvas.width - 36, canvas.height - 36, 28, bg);

  ctx.font = `800 ${fontSize}px system-ui, sans-serif`;
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  const lines = String(text).split("\n");
  const lineHeight = fontSize * 1.18;
  const startY = canvas.height / 2 - ((lines.length - 1) * lineHeight) / 2;

  for (let i = 0; i < lines.length; i++) {
    ctx.fillText(lines[i], canvas.width / 2, startY + i * lineHeight);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;

  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false,
  });

  return new THREE.Sprite(material);
}

function roundRect(ctx, x, y, width, height, radius, fillStyle) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + width, y, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x, y + height, radius);
  ctx.arcTo(x, y + height, x, y, radius);
  ctx.arcTo(x, y, x + width, y, radius);
  ctx.closePath();
  ctx.fillStyle = fillStyle;
  ctx.fill();
}

function updatePointer(event) {
  pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
}

function onPointerMove(event) {
  updatePointer(event);

  for (const [, mesh] of hotspotMeshes) {
    if (mesh.userData.labelSprite) {
      mesh.userData.labelSprite.visible = false;
    }
  }

  const hit = getHotspotHit();

  document.body.style.cursor = hit ? "pointer" : "default";

  if (hit && hit.object.userData.labelSprite) {
    hit.object.userData.labelSprite.visible = true;
  }
}

function onClick(event) {
  updatePointer(event);

  const hit = getHotspotHit();

  if (!hit) return;

  const hotspotId = hit.object.userData.hotspotId;

  selectedHotspotId = hotspotId;
  sendHotspot(hotspotId, hit.object.userData.prompt);
}

function getHotspotHit() {
  raycaster.setFromCamera(pointer, camera);

  const clickable = Array.from(hotspotMeshes.values()).filter((mesh) => {
    return (
      mesh.visible &&
      mesh.userData.parentGroup &&
      mesh.userData.parentGroup.visible
    );
  });

  const hits = raycaster.intersectObjects(clickable, false);

  return hits.length > 0 ? hits[0] : null;
}

// Calibration controls:
// 1/2/3/4 selects hotspot.
// Arrow keys move X/Z.
// PageUp/PageDown moves Y.
// Hold Shift for bigger movement.
// P prints positions to browser console.
function onKeyDown(event) {
  const ids = currentRequiredObjects();

  if (/^[1-9]$/.test(event.key)) {
    selectedHotspotId = ids[Number(event.key) - 1];
    if (!selectedHotspotId) return;
    showToast(`Selected hotspot: ${selectedHotspotId}`);
    return;
  }

  if (event.key.toLowerCase() === "p") {
    printHotspotPositions();
    return;
  }

  if (!selectedHotspotId) return;

  const mesh = hotspotMeshes.get(selectedHotspotId);

  if (!mesh || !mesh.userData.parentGroup) return;

  const amount = event.shiftKey ? 0.25 : 0.08;
  const group = mesh.userData.parentGroup;

  let moved = true;

  switch (event.key) {
    case "ArrowLeft":
      group.position.x -= amount;
      break;

    case "ArrowRight":
      group.position.x += amount;
      break;

    case "ArrowUp":
      group.position.z -= amount;
      break;

    case "ArrowDown":
      group.position.z += amount;
      break;

    case "PageUp":
      group.position.y += amount;
      break;

    case "PageDown":
      group.position.y -= amount;
      break;

    default:
      moved = false;
  }

  if (moved) {
    CONFIG.hotspots[selectedHotspotId].position = [
      Number(group.position.x.toFixed(2)),
      Number(group.position.y.toFixed(2)),
      Number(group.position.z.toFixed(2)),
    ];

    showToast(
      `Moved ${selectedHotspotId}: ${CONFIG.hotspots[
        selectedHotspotId
      ].position.join(", ")}`
    );
  }
}

function printHotspotPositions() {
  const output = {};

  for (const [id, mesh] of hotspotMeshes) {
    const p = mesh.userData.parentGroup.position;

    output[id] = [
      Number(p.x.toFixed(2)),
      Number(p.y.toFixed(2)),
      Number(p.z.toFixed(2)),
    ];
  }

  console.log("Copy these positions into CONFIG.hotspots:", output);
  showToast("Hotspot positions printed to browser console.");
}

async function sendHotspot(hotspotId, prompt) {
  showToast(`Asking Al Rawi about ${labelFor(hotspotId)}...`);

  const payload = {
    session_id: CONFIG.sessionId,
    scene_id: currentSceneName === "majlis" ? "majlis" : "masjid",
    hotspot_id: hotspotId,
    user_message: prompt,
    language: "en",
  };

  try {
    const response = await fetch(CONFIG.backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || response.statusText);
    }

    const data = await response.json();

    handleBackendResponse(hotspotId, data);
  } catch (error) {
    console.error("Backend failed:", error);

    // Local demo fallback keeps frontend working even if backend is off.
    explored.add(hotspotId);

    const fallback = localFallbackResponse(hotspotId);

    handleBackendResponse(hotspotId, fallback);

    showToast("Backend offline. Using local demo response.");
  }
}

function handleBackendResponse(hotspotId, data) {
  explored.add(hotspotId);

  if (Array.isArray(data.explored_objects)) {
    for (const obj of data.explored_objects) {
      explored.add(obj);
    }
  }

  const reply = data.reply || localFallbackResponse(hotspotId).reply;

  showDialogue(reply);

  updateProgressUI();

  const required = requiredObjectsForHotspot(hotspotId);
  const completedCurrentSet = required.every((obj) => explored.has(obj));

  if (currentSceneName === "majlis" && completedCurrentSet) {
    majlisCompleted = true;
    fanarUnlocked = true;
    if (ui.continueFanarBtn) ui.continueFanarBtn.style.display = "block";
    showBadge("Guest of the Majlis", "Majlis Night Desert");
    showDialogue(`${reply}\n\nMajlis journey complete. Continue to Fanar when you are ready.`);
    return;
  }

  if (
    currentSceneName !== "majlis" &&
    (Boolean(data.badge_unlocked) || completedCurrentSet)
  ) {
    showBadge("Visitor of Fanar", data.passport_stamp || "Fanar Mosque");
  }
}

function localFallbackResponse(hotspotId) {
  const fallbackReplies = {
    majlis_tent:
      "The traditional majlis tent is a welcoming social space for guests, conversation, hospitality, and shared desert life.",

    camel:
      "Camels were essential in desert life, helping people travel, carry goods, and survive long journeys across harsh landscapes.",

    dallah:
      "The dallah is the Arabic coffee pot, closely tied to generosity, welcome, and Qatari hospitality rituals.",

    bakhoor:
      "Bakhoor incense is often used to perfume the majlis and create a warm, respectful atmosphere for guests.",

    campfire:
      "Desert gatherings around fire brought warmth, storytelling, coffee, and companionship during cool nights.",

    exterior_architecture:
      "Fanar's spiral minaret is one of Doha's recognizable landmarks. It represents guidance, learning, and Islamic cultural identity.",

    mihrab:
      "The mihrab is the prayer niche that indicates the qibla direction. It is a focal point of the prayer hall.",

    quran:
      "The Qur’an is the central text of Islam. In this experience, it represents knowledge, recitation, and spiritual reflection.",

    imam:
      "The imam leads prayer and guides the community. Here, Al Rawi explains the mosque and its cultural meaning.",
  };

  return {
    reply:
      fallbackReplies[hotspotId] ||
      "This is part of the heritage journey.",

    badge_unlocked: requiredObjectsForHotspot(hotspotId).every((obj) =>
      obj === hotspotId ? true : explored.has(obj)
    ),

    passport_stamp:
      CONFIG.hotspots[hotspotId]?.scene === "majlis"
        ? "Majlis Night Desert"
        : "Fanar Mosque",
    explored_objects: Array.from(explored),
    completed_scenes: [],
    badges: [],
  };
}

function showDialogue(text) {
  ui.dialoguePanel.style.display = "block";
  ui.dialogueText.textContent = text;
}

function showBadge(badgeName = "Visitor of Fanar", stampName = "Fanar Mosque") {
  ui.badgePopup.classList.remove("hidden");
  ui.passportPanel.classList.remove("hidden");

  ui.badgePopup.setAttribute("data-badge", badgeName);
  ui.passportPanel.setAttribute("data-stamp", stampName);

  showToast(`Badge unlocked: ${badgeName}`);
}

function showToast(text) {
  ui.statusToast.textContent = text;
  ui.statusToast.classList.add("visible");

  clearTimeout(showToast.timeout);

  showToast.timeout = setTimeout(() => {
    ui.statusToast.classList.remove("visible");
  }, 2200);
}

function updateProgressUI() {
  const labels = {
    majlis_tent: "Majlis tent",
    camel: "Camel",
    dallah: "Dallah",
    bakhoor: "Bakhoor",
    campfire: "Campfire",
    exterior_architecture: "Exterior architecture",
    mihrab: "Mihrab",
    quran: "Qur’an",
    imam: "Imam",
  };

  ui.progressList.innerHTML = "";

  for (const id of currentRequiredObjects()) {
    const item = document.createElement("div");
    item.className = "progressItem";

    const label = document.createElement("span");
    label.textContent = labels[id] || id;

    const mark = document.createElement("span");

    mark.className = "progressMark" + (explored.has(id) ? " done" : "");
    mark.textContent = explored.has(id) ? "✓" : "○";

    item.appendChild(label);
    item.appendChild(mark);

    ui.progressList.appendChild(item);
  }
}

function resetProgress() {
  explored.clear();
  majlisCompleted = false;
  fanarUnlocked = false;

  CONFIG.sessionId = `threejs-heritage-demo-${Date.now()}`;

  ui.badgePopup.classList.add("hidden");
  ui.passportPanel.classList.add("hidden");
  if (ui.continueFanarBtn) ui.continueFanarBtn.style.display = "none";

  for (const [, mesh] of hotspotMeshes) {
    mesh.material.color.set(0xffd46b);
    mesh.material.emissive.set(0xffc861);
    mesh.material.opacity = 0.55;
  }

  updateProgressUI();
  showScene("majlis", { silent: true });

  showDialogue("Progress reset. Start again by exploring the Majlis Night Desert.");

  showToast("Progress reset");
}

function labelFor(id) {
  return CONFIG.hotspots[id]?.label || id;
}

function currentRequiredObjects() {
  return currentSceneName === "majlis"
    ? CONFIG.majlisRequiredObjects
    : CONFIG.fanarRequiredObjects;
}

function requiredObjectsForHotspot(hotspotId) {
  return CONFIG.hotspots[hotspotId]?.scene === "majlis"
    ? CONFIG.majlisRequiredObjects
    : CONFIG.fanarRequiredObjects;
}

function animate(time = 0) {
  requestAnimationFrame(animate);

  for (const [id, mesh] of hotspotMeshes) {
    if (!mesh.visible) continue;

    const pulse = 1 + Math.sin(time * 0.004 + id.length) * 0.1;

    mesh.scale.setScalar(pulse);
    mesh.rotation.y += 0.01;

    // Explored hotspots stay golden/cream, not green.
    if (explored.has(id)) {
      mesh.material.color.set(0xfff1b8);
      mesh.material.emissive.set(0xffd46b);
      mesh.material.opacity = 0.5;
    }
  }

  if (majlisStars && majlisStars.visible) {
    majlisStars.material.opacity = 0.78 + Math.sin(time * 0.0016) * 0.14;
    majlisStars.rotation.y += 0.00008;
  }

  controls.update();
  clampInteriorCamera();
  renderer.render(scene, camera);
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();

  renderer.setSize(window.innerWidth, window.innerHeight);
}
