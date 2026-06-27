# Al Muthaqafun — المثقفون

### AI-Guided 3D Cultural Heritage Experience · Fanar Hackathon Submission

**Track:** Education & Cultural Preservation

**Primary Model:** Fanar-C-2-27B (via the Fanar 2.0 Unified Platform Gateway)

**Voice Synthesis:** Fanar Aura TTS (`Fanar-Aura-TTS-2` by default)

**Technology Stack:** FastAPI · Three.js · Python · GLB 3D Assets · Browser Web Speech API

**Team Name:** Team Not Found - Rahma Soedarnadi · Raneem AlHasan · Shrinidhi Sridhar

## 1. Problem Statement

Children growing up in Qatar often recognise cultural and Islamic symbols—such as a traditional _Majlis_, a _Dallah_, a _Mihrab_, or a mosque—without always understanding the deeper values, history, and customs those objects represent. Heritage education in schools and museums is typically structured around one-directional explanations: children are told _about_ an object rather than being invited to actively explore and converse with it.

The deeper problem is not awareness, but cognitive and emotional connection. Heritage is not merely a static collection of places and artefacts; it is the living meaning and etiquette (_Adab_) a community carries forward. When children encounter culture solely through passive instruction, they memorize names without cultivating a personal relationship with the narratives and identities behind them.

At the same time, Arabic-language educational technology has historically been underserved. Digital tools built for Gulf youth are frequently designed English-first, which pushes Arabic into a secondary, translation-dependent role. A heritage learning experience must be Arabic-native—built from the ground up to preserve linguistic, cultural, and spiritual authenticity.

This project addresses a critical question: **How can we leverage state-of-the-art Arabic Large Language Models to construct an interactive, culturally aligned, and highly engaging 3D environment where children can actively converse with Qatari history—in native Arabic—while maintaining cultural accuracy and educational integrity?**

## 2. Current Solution Architecture

### 2.1 Overview

_Al Muthaqafun_ is a browser-based interactive 3D heritage experience. A learner navigates a Three.js scene, clicks on cultural objects, and speaks or types questions. They receive real-time, bilingual explanations from **Maryam**, an autonomous AI cultural guide powered by the Fanar platform.

The current prototype covers these scene keys:

- **`majlis_ext`**: A cinematic exterior arrival outside a traditional _Bait Al Sha'ar_ (Bedouin tent).
    
- **`majlis`**: An explorable majlis interior featuring a _Dallah_ (coffee pot), _Sadu_ carpet, _Bakhoor_ burner, and floor cushions.
    
- **`masjid_ext`**: A cinematic exterior arrival outside Masjid Fanar.
    
- **`masjid`**: An explorable mosque interior featuring the Holy Qur'an, _Mihrab_ (prayer niche), _Hadith_ texts, and the Imam.
    
- **`zubarah`**: The Al Zubarah Fort scene containing primitive, explorable structural assets.
    

The frontend also includes a temporary offline **Next scene** button to ensure demo continuity and seamless navigation if the external API encounters latency.

### 2.2 System Architecture

```
User
  |-- 3D object click
  |     |
  |     v
  |   Frontend static object path (client/client.html)
  |     - Shows local object explanation immediately
  |     - Marks checklist item locally
  |     - Sends deterministic /tool sync to backend
  |
  |-- typed message or browser speech transcript
        |
        v
Frontend - Three.js client (client/client.html)
  - Renders scenes and GLB assets
  - Captures clicks through raycasting
  - Captures microphone text through the browser Web Speech API
  - Sends {session_id, user_message, history, game_state} to POST /turn
  - Receives reply, executed tool calls, updated history, and updated game state
  - Plays audio by calling POST /tts
        |
        v
Backend - FastAPI (src/main.py)
  - Serves client.html and /client static assets
  - Stores local in-memory sessions
  - Merges client game_state with cached session state
  - Deserializes GameState safely
  - Calls run_turn() for dialogue turns
  - Dispatches deterministic /tool calls for static object interactions
  - Proxies /tts to Fanar Aura TTS
        |
        v
Agentic layer (src/agent.py + src/prompts/prompts.py)
  - Builds Maryam's prompt from scene, phase, state, objects, and tool rules
  - Calls Fanar-C-2-27B through AsyncOpenAI
  - Parses JSON, Markdown-wrapped JSON, bare tool arrays, and pseudo tool syntax
  - Applies targeted retry and deterministic fallback heuristics
  - Dispatches validated tools through src/tools/tools.py
        |
        v
Story and state layer (src/storyline/storyline.py)
  - Defines StoryPhase, GameState, SCENE_REQUIREMENTS
  - Enforces required objects and questions for badge eligibility
  - Keeps exterior scenes cinematic and non-completable
```

### 2.3 Core Components

|File|Current role|
|---|---|
|`src/main.py`|FastAPI application serving static assets, managing CORS, tracking local sessions, exposing `/turn`, `/tool`, and `/tts` endpoints, and handling state serialization.|
|`src/agent.py`|Orchestrates the Fanar API call, parses model responses, applies retry/fallback heuristics, filters tool schemas, and manages the dispatch loop.|
|`src/prompts/prompts.py`|Stores scene descriptions, object metadata, phase-specific instructions, tool-calling constraints, and JSON response rules.|
|`src/tools/tools.py`|Defines functional tool schemas and executes deterministic, server-side dispatch logic.|
|`src/storyline/storyline.py`|Manages `GameState`, `StoryPhase`, scene requirements, and scene-completion rules.|
|`client/client.html`|Houses the Three.js viewport, handles asset loading (GLTF/Draco), scene lighting, raycasting, UI panels, WebSpeech, and TTS playback.|
|`client/models/`|Stores optimized 3D GLB models and texture maps used by the runtime environment.|
|`tests/`|Contains the unit testing framework for validating prompts, tools, storyline states, and agent behaviors.|

### 2.4 Current Data Flow

The application executes along two synchronized interaction paths:

1. **Object click path**
    
    - The player clicks on a required 3D object inside the Three.js viewport.
        
    - The frontend immediately displays the object's local, culturally verified description card to eliminate network latency.
        
    - The local checklist updates instantly.
        
    - The client fires a `POST /tool` payload containing `tool_name="explore_object"` to ensure the backend session state remains perfectly synchronized.
        
2. **Dialogue path**
    
    - The player inputs a text query or speaks into the microphone (transcribed locally by the browser's Web Speech API).
        
    - The frontend packages the state and dispatches a secure payload `{ session_id, user_message, history, game_state }` to `POST /turn`.
        
    - The backend retrieves the session cache, merges incoming updates, and deserializes the payload into a clean `GameState` object.
        
    - `run_turn()` synthesizes a custom system prompt injecting the current `StoryPhase` rules.
        
    - The request is dispatched to the Fanar API gateway. The model evaluates the state and returns a structured JSON payload with a conversational `reply` and corresponding `tools`.
        
    - The backend normalizes the JSON response, dispatches the validated tools, mutates the session state, and returns the unified result.
        
    - The frontend updates the subtitles, progress indicators, Maryam's gesture state, and triggers voice playback.
        

## 3. Agentic Workflow Design

### 3.1 Why This Is Agentic

Rather than following rigid, hardcoded branching trees, _Al Muthaqafun_ employs the `Fanar-C-2-27B` model as an active, reasoning agent. On every conversation turn, the model dynamically evaluates a comprehensive state envelope:

- Current scene identifier and active narrative phase.
    
- Currently explored objects and remaining checklist requirements.
    
- Full conversation history.
    
- Contextual guidelines and scene boundaries.
    
- Active tool definitions and JSON serialization constraints.
    

The agent independently determines the most appropriate conversational response and selects which system tools—such as `transition_scene`, `give_directions`, or `open_ui`—must be executed to progress the experience.

### 3.2 Three-Layer Agent Architecture

**Layer 1 - Fanar as reasoning agent**

`Fanar-C-2-27B` evaluates the user's intent to construct an authentic, Arabic-first bilingual response, while determining whether local, in-game functional tools should be triggered.

Example response shape:

```
{
  "reply": "الدلة رمز للكرم والضيافة في قطر. The dallah is a symbol of Qatari hospitality.",
  "tools": [
    {
      "name": "explore_object",
      "args": {
        "object_id": "dallah",
        "spoken_context": "The dallah represents Arabic coffee culture and welcoming guests."
      }
    }
  ]
}
```

**Layer 2 - Defensive parser and targeted heuristics**

To prevent formatting discrepancies from breaking gameplay, `agent.py` implements a resilient parsing pipeline that normalizes various output styles:

- Standard JSON objects.
    
- Markdown-wrapped (` ```json `) strings.
    
- Raw JSON arrays or unstructured text containing embedded tool definitions.
    

If a critical action (such as transitioning scenes or requesting coordinates) is requested but the model fails to populate the `tools` array, the system executes an automated, single-turn conversational retry. This nudges the model with precise formatting constraints to guarantee a successful tool call.

Furthermore, deterministic fallbacks are applied:

- Enforcing `explore_object` calls on explicit click events.
    
- Intercepting and resolving implicit travel requests to their target scene IDs.
    
- Safely managing badge awards through the backend state machine.
    

**Layer 3 - Backend as deterministic authority**

To preserve application stability, the backend acts as the ultimate authority over state mutation:

- `explore_object` only logs items that are valid for the active scene.
    
- `award_badge` fails if `state.scene_completable()` evaluates to `False`.
    
- `transition_scene` maps inputs strictly to valid `StoryPhase` parameters.
    
- Exterior scenes are locked as non-completable to prevent accidental progression.
    

## 3.3 Storyline and Phase State Machine

The narrative progresses through a structured, multi-scene phase graph:

```
majlis_ext / majlis_intro
  -> majlis / majlis_enter, majlis_coffee, majlis_explore
  -> badge: Guest of the Majlis (ضيف المجلس)
  -> masjid_ext / masjid_arrival
  -> masjid / masjid_enter, masjid_explore
  -> badge: Visitor of the Masjid (زائر المسجد)
  -> zubarah / zubarah_arrival, zubarah_explore
  -> badge: Guardian of Zubarah (حارس الزبارة)
  -> journey_complete
```

A scene is successfully completed only when:

1. All required objects inside the scene have been explored.
    
2. The minimum conversational question threshold is satisfied.
    
3. `scene_completable()` evaluates to `True`.
    

Cinematic exterior scenes have no required objects, do not award badges, and cannot be manually completed.

### 3.4 Implemented Tools

|Tool|Trigger|Current effect|
|---|---|---|
|`explore_object`|Player interacts with or asks about a required object.|Marks the object as explored if valid for the current scene.|
|`give_directions`|Player asks where a physical object is located.|Returns spatial guidance; frontend can highlight the target.|
|`open_ui`|Player requests the map, notes, inventory, or badges panel.|Returns a UI action to open the specified layout panel.|
|`award_badge`|Invoked deterministically upon meeting scene criteria.|Completes the scene and appends the badge to the player's profile.|
|`trigger_animation`|Narrative milestones or scene transition triggers.|Signals the frontend avatar to play a specific gesture (e.g., wave, bow).|
|`transition_scene`|Player explicitly travels or enters from an exterior scene.|Updates `current_scene`, clears temporary progress, and resets the phase.|

### 3.5 Memory and State Management

State tracking is split into two synchronized layers:

- **Client-Side State:** `client.html` tracks the active visual `gameState`, active UI panels, checklist items, and dialogue histories.
    
- **Server-Side Session Cache:** `src/main.py` maintains an in-memory `sessions` dictionary keyed by `session_id`.
    

On every incoming connection turn or click event, the backend merges the client's reported state with its cached session record. It then deserializes this unified profile into a validated `GameState` object, ensuring seamless sync while maintaining local development simplicity.

## 4. Use of Fanar and External Tools

### 4.1 Fanar-C-2-27B - Dialogue and Tool Selection

Our application communicates with the primary model via the OpenAI-compatible gateway:

```
base_url=os.getenv("FANAR_BASE_URL") or "https://api.fanar.qa/v1"
model=os.getenv("FANAR_MODEL")
```

The model is configured via the local `.env` environment variables file:

```
FANAR_MODEL=Fanar-C-2-27B
```

The model acts as the core of our system, handling bilingual conversational dialogue, evaluating user intentions, and selecting the appropriate tools.

### 4.2 Fanar Aura TTS

Voice synthesis is routed through a dedicated FastAPI reverse-proxy:

- The frontend calls `POST /tts`.
    
- The backend forwards the request to `tts_client.audio.speech.create(...)`.
    
- Audio streams are processed using `Fanar-Aura-TTS-2` and the premium `Amelia` voice, returning high-fidelity MP3 binaries directly to the client.
    

```
response = tts_client.audio.speech.create(
    model=os.getenv("FANAR_TTS_MODEL", "Fanar-Aura-TTS-2"),
    input=req.text,
    voice=req.voice,
    response_format="mp3",
)
```

### 4.3 Speech Input

Speech input utilizes the browser's native **Web Speech API**:

```
window.SpeechRecognition || window.webkitSpeechRecognition
```

This ensures free, real-time client-side transcription directly inside the viewport. Integrating a native, hosted Fanar Aura ASR model remains a key objective for future production releases.

### 4.4 Fanar Sadiq and Shaheen

Because our backend targets the unified `Fanar-C-2-27B` platform gateway, the system natively utilizes the hosted **Fanar Orchestrator**. This means we do not have to write or maintain custom API routing logic for specialized tasks.

When a user interacts with the application:

- Historical, ethical, and Islamic theological queries are automatically routed to the **Fanar Sadiq** (Grounded Islamic QA) family.
    
- High-fidelity, culturally nuanced English/Arabic translation and vocabulary alignments are natively managed by the **Fanar Shaheen** engine.
    
- Every synthesized output is processed by **Fanar Safeguards (FanarGuard)**, verifying that all dialogues and tool suggestions are culturally respectful and religiously accurate before reaching the user.
    

### 4.5 Three.js

Three.js powers our immersive, browser-based interactive 3D frontend:

- Manages real-time mesh rendering, ambient lighting, and fog.
    
- Performs raycasting to detect player mouse clicks on 3D objects.
    
- Dynamically scales and centers imported GLB assets.
    
- Resolves texture bindings for the traditional _Sadu_ carpet and floor cushions.
    

### 4.6 FastAPI

Our FastAPI backend provides a lightweight, highly responsive server:

- `GET /` serves the main entry point `client.html`.
    
- Exposes `POST /turn` to process player turns and run tool checks.
    
- Exposes `POST /tts` to proxy voice synthesis and stream audio files.
    
- Exposes `/health` to verify service availability.
    

### 4.7 GLB Assets and Scene Content

Interactive environments are enriched with custom 3D models:

- **Majlis:** `majlis_tent.glb`, `dallah.glb`, `bakhoor.glb`, `cushion.glb`, `camel.glb`.
    
- **Masjid:** `fanar_exterior_lights.glb`, `fanar_interior.glb`, `quran.glb`, `mihrab.glb`, `hadeeth.glb`, `imam.glb`.
    
- **Textures:** High-resolution patterns (`sadu_pattern1.jpg`, `sadu_pattern2.jpg`).
    

## 5. Evaluation Status

### 5.1 Test Coverage in Repository

The application's integrity was verified using a comprehensive unit testing suite:

|Test Script|Target Subsystem|
|---|---|
|`tests/test_agent.py`|Validates dialogue responses, parsing resilience, state history, and tool selections.|
|`tests/test_storyline.py`|Asserts requirements logging, phase transitions, and scene completion logic.|
|`tests/test_tools.py`|Verifies deterministic server-side tool dispatch outcomes.|
|`tests/test_prompts.py`|Tests prompt builder configurations across different phases.|

The project dependencies list `pytest` and `pytest-asyncio` in `requirements.txt`.

The agent was tested on 10 different tasks, which involves tool-calling, story progression, and memory functions, using tests/test_agent.py. Eight out of ten tests passed. The failed tests are due to incorrect tool-calling.

```
tests/test_agent.py::test_connection PASSED                                                                                                                      [  9%]
tests/test_agent.py::test_1_transition_scene PASSED                                                                                                              [ 18%]
tests/test_agent.py::test_2_give_directions PASSED                                                                                                               [ 27%]
tests/test_agent.py::test_3_open_map PASSED                                                                                                                      [ 36%]
tests/test_agent.py::test_4_open_inventory FAILED                                                                                                                [ 45%]
tests/test_agent.py::test_5_explore_object PASSED                                                                                                                [ 54%]
tests/test_agent.py::test_6_plain_text_no_tools PASSED                                                                                                           [ 63%]
tests/test_agent.py::test_7_award_badge PASSED                                                                                                                   [ 72%]
tests/test_agent.py::test_8_multi_tool_travel_with_animation FAILED                                                                                              [ 81%]
tests/test_agent.py::test_9_conversation_history PASSED                                                                                                          [ 90%]
tests/test_agent.py::test_10_majlis_intro_greeting PASSED                                                                                                        [100%]
```

### 5.2 Current Demo Capabilities

Our live interactive prototype fully demonstrates:

- Open-ended, Fanar-powered dialogue via `/turn`.
    
- Clickable 3D objects with instant local feedback and backend state synchronization.
    
- High-quality text-to-speech audio streaming using `Fanar-Aura-TTS-2`.
    
- Real-time player progress indicators, checklists, and earned badges.
    
- Dynamic visual overlays, including the Interactive Map and Campsite Journal.
    
- Character animation triggers synchronized with Maryam's speech states.
    

### 5.3 Strengths Observed

- **Strict Boundary Separation**: Clear division of labor between AI reasoning (Fanar LLM), deterministic state tracking (FastAPI), and visual rendering (Three.js).
    
- **Format Resilience**: The parsing pipeline handles Markdown wrapping and syntax variations cleanly, preventing formatting anomalies from disrupting gameplay.
    
- **Instant Click Responses**: Local front-end descriptions show immediately when an object is clicked, keeping the gameplay feeling fast and responsive.
    
- **High-Fidelity Audio**: In-game speech sounds exceptionally natural thanks to the integration of `Fanar-Aura-TTS-2`.
    

### 5.4 Current Limitations

- **Browser-Dependent STT**: Using the browser's Web Speech API means speech-to-text accuracy can vary across different web browsers.
    
- **Manual Navigation Fallback**: The "Next Scene" button is a temporary feature for demo continuity, rather than being part of the core agentic flow.
    
- **In-Memory Cache**: Sessions are cached in active system memory. Scaling to a production environment would require a database like Redis or PostgreSQL.
    

## 6. Recommendations for Future Fanar Improvements

### 6.1 Native Schema-Constrained Tool Calling

Integrating native, schema-enforced tool calling directly into the Fanar API would simplify parsing and reduce the need for custom retry logic.

### 6.2 Lower-Latency Arabic Voice Pipeline

Providing low-latency streaming modes for TTS and ASR would make conversations with Maryam feel even more natural and immediate.

### 6.3 Explicit Fanar Aura ASR Integration

Adding a dedicated Fanar ASR endpoint would guarantee consistent, high-accuracy Arabic speech transcription across all client devices and browsers.

### 6.4 Fanar Sadiq Integration

Deepening Sadiq integration would allow our guide to reference specific Quranic verses or Hadith contexts with verified, grounded citations.

### 6.5 Fanar Shaheen Integration

Allowing developers to configure Shaheen's translation behavior directly would make it easier to create specialized language and educational modes.

### 6.6 Cultural Education Mode

A specialized educational setting with child-friendly vocabulary, adjustable response complexity, and built-in safety filters would make the platform highly suitable for classrooms.

### 6.7 Persistent Learning Memory

Adding secure, database-backed progress tracking would enable children to continue their cultural journey across multiple sessions and devices.

### 6.8 Multimodal Scene Understanding

Passing visual scene context (such as the player's 3D coordinates or camera angle) to the model would allow Maryam to react directly to what the child is looking at in the game.

## 7. Local Setup

```
cd almuthaqafun
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the repository root:

```
FANAR_API_KEY=your_api_key
FANAR_BASE_URL=https://api.fanar.qa/v1
FANAR_MODEL=Fanar-C-2-27B
FANAR_TTS_MODEL=Fanar-Aura-TTS-2
```

Start the backend:

```
PYTHONPATH=. uvicorn src.main:app --reload --port 8000
```

Open your browser to:

```
http://localhost:8000/
```

Serving `client.html` through FastAPI is highly recommended to ensure all static GLB assets and API routes resolve correctly without CORS issues.