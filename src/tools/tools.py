# tools.py
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
            "description": "Give spoken directions to a location and optionally highlight it on the map",
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
                        "enum": ["idle", "wave", "point", "bow", "offer_coffee", "drink_coffee", "laugh", "gesture_follow", "bakhoor_smoke"]
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
                        "enum": ["majlis", "masjid", "zubarah"]
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
        state.object_explored(args["object_id"])
        return f"Object '{args['object_id']}' marked as explored. Progress: {len(state.explored_objects)}/{len(SCENE_REQUIREMENTS.get(state.current_scene, {}).get('required_objects', []))}"

    elif tool_name == "give_directions":
        return f"Directions given to {args['destination']}."

    elif tool_name == "open_ui":
        return f"UI panel '{args['panel']}' opened."

    elif tool_name == "award_badge":
        if state.scene_completable():
            state.complete_scene()
            return f"Badge '{args['badge_title']}' awarded. Scene complete."
        else:
            return "Scene not yet completable — player hasn't explored all required objects."

    elif tool_name == "trigger_animation":
        return f"Animation '{args['animation']}' triggered."

    elif tool_name == "transition_scene":
        state.current_scene  = args["scene_id"]
        state.current_phase  = StoryPhase[f"{args['scene_id'].upper()}_ARRIVAL"]
        return f"Transitioning to scene '{args['scene_id']}'."

    return f"Unknown tool: {tool_name}"