# src/tools/tools.py
from src.storyline.storyline import GameState, StoryPhase, SCENE_REQUIREMENTS

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "explore_object",
            "description": "Called when the player interacts with a scene object. Updates exploration progress and provides cultural context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "object_id":      {"type": "string", "description": "The unique ID of the object e.g. 'dallah', 'sadu_carpet'"},
                    "spoken_context": {"type": "string", "description": "What Maryam says about this object"}
                },
                "required": ["object_id", "spoken_context"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "give_directions",
            "description": "Give spoken directions to an object's location and optionally highlight it on the map",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination":    {"type": "string"},
                    "instruction":    {"type": "string", "description": "Spoken directions in Arabic and English"},
                    "highlight_on_map": {"type": "boolean", "default": True}
                },
                "required": ["destination", "instruction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_ui",
            "description": "Open a UI panel in the game",
            "parameters": {
                "type": "object",
                "properties": {
                    "panel": {"type": "string", "enum": ["map", "notes", "inventory", "badges"]}
                },
                "required": ["panel"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "award_badge",
            "description": "Award the player a scene completion badge. Only call when scene_completable is true in the game state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scene_name":        {"type": "string"},
                    "badge_title":       {"type": "string"},
                    "congratulations":   {"type": "string", "description": "Warm spoken congratulations in Arabic and English"}
                },
                "required": ["scene_name", "badge_title", "congratulations"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_animation",
            "description": "Play a named animation on the scene and chatacter models.",
            "parameters": {
                "type": "object",
                "properties": {
                    "animation": {
                        "type": "string",
                        "enum": ["idle", "wave", "point", "offer_coffee", "drink_coffee", "laugh", "gesture_follow", "bakhoor_smoke", "bow", "nod"]
                    }
                },
                "required": ["animation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transition_scene",
            "description": "Trigger a transition to a new scene after the player agrees to travel there",
            "parameters": {
                "type": "object",
                "properties": {
                    "scene_id": {
                        "type": "string",
                        "enum": ["majlis_ext", "majlis", "masjid_ext", "masjid", "zubarah"]
                    },
                    "transition_line": {"type": "string", "description": "What Maryam says as the scene fades out"}
                },
                "required": ["scene_id", "transition_line"]
            }
        }
    }
]


def dispatch_tool(tool_name: str, args: dict, state: "GameState") -> str:
    """Executes tool logic server-side and returns result string for Fanar."""

    if tool_name == "explore_object":
        required_objs = SCENE_REQUIREMENTS.get(state.current_scene, {}).get("required_objects") or []
        if not required_objs:
            return f"Scene '{state.current_scene}' has no explorable objects. Ignored explore_object."
        obj_id = args.get("object_id")
        if obj_id not in required_objs:
            return f"Object '{obj_id}' is not explorable in scene '{state.current_scene}'."
        state.object_explored(obj_id)
        return f"Object '{obj_id}' marked as explored. Progress: {len(state.explored_objects)}/{len(required_objs)}"

    elif tool_name == "give_directions":
        return f"Directions given to {args['destination']}."

    elif tool_name == "open_ui":
        return f"UI panel '{args['panel']}' opened."

    elif tool_name == "award_badge":
        if state.scene_completable():
            badge_title = args.get("badge_title") or SCENE_REQUIREMENTS.get(state.current_scene, {}).get("badge_title")
            state.complete_scene()
            if badge_title:
                return f"Badge '{badge_title}' awarded. Scene complete."
            return "Scene complete. No badge is awarded for this transition scene."
        else:
            return "Scene not yet completable — player hasn't met exploration/question criteria."

    elif tool_name == "trigger_animation":
        return f"Animation '{args['animation']}' triggered."

    elif tool_name == "transition_scene":
        scene_id = args["scene_id"]


        state.current_scene = scene_id
        state.explored_objects = []
        state.questions_asked = 0

        # Explicit scene -> phase mapping. Do not build enum names dynamically:
        # "masjid" should enter MASJID_ENTER, not fall through to JOURNEY_COMPLETE.
        scene_to_phase = {
            "majlis_ext": StoryPhase.MAJLIS_INTRO,
            "majlis": StoryPhase.MAJLIS_ENTER,
            "masjid_ext": StoryPhase.MASJID_ARRIVAL,
            "masjid": StoryPhase.MASJID_ENTER,
            "zubarah": StoryPhase.ZUBARAH_ARRIVAL,
        }
        state.current_phase = scene_to_phase.get(scene_id, StoryPhase.JOURNEY_COMPLETE)

        return f"Transitioning to scene '{scene_id}'. Mapped to phase: {state.current_phase.value}"

    return f"Unknown tool: {tool_name}"