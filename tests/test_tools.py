#tools/test_tools.py
import sys
from pathlib import Path

# --- BULLETPROOF PYTHON PATH RESOLUTION ---
# Guarantees 'src' is discoverable from anywhere in the directory hierarchy
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.storyline.storyline import GameState, StoryPhase
from src.tools.tools import dispatch_tool


def test_explore_object_updates_state():
    state = GameState()
    # Explicitly set scene to the interior majlis where 'dallah' is a valid object
    state.current_scene = "majlis"
    state.current_phase = StoryPhase.MAJLIS_EXPLORE
    
    result = dispatch_tool("explore_object", {
        "object_id": "dallah",
        "spoken_context": "The long-spouted coffee pot is a symbol of Qatari hospitality."
    }, state)
    
    assert "dallah" in state.explored_objects
    assert "marked as explored" in result
    assert "Progress: 1/4" in result  # Majlis has 4 required objects


def test_badge_not_awarded_when_incomplete():
    state = GameState()
    # Explicitly set scene to the interior majlis
    state.current_scene = "majlis"
    state.current_phase = StoryPhase.MAJLIS_EXPLORE
    
    result = dispatch_tool("award_badge", {
        "scene_name": "majlis",
        "badge_title": "ضيف المجلس",
        "congratulations": "أحسنت"
    }, state)
    
    assert "not yet completable" in result
    assert state.badges == []


def test_badge_awarded_when_complete():
    state = GameState()
    # Explicitly set scene to the interior majlis so its requirements are evaluated
    state.current_scene = "majlis"
    state.current_phase = StoryPhase.MAJLIS_EXPLORE
    
    # 1. Simulate complete exploration of the 4 required interior elements
    for obj in ["dallah", "sadu_carpet", "bakhoor", "cushion"]:
        dispatch_tool("explore_object", {"object_id": obj, "spoken_context": "..."}, state)
    
    # 2. Complete the required question count
    state.questions_asked = 1
    
    result = dispatch_tool("award_badge", {
        "scene_name": "majlis",
        "badge_title": "ضيف المجلس · Guest of the Majlis",
        "congratulations": "تهانينا! لقد أصبحت ضيفاً للمجلس. Congratulations! You are now a guest of the Majlis."
    }, state)
    
    assert "awarded" in result
    assert "ضيف المجلس · Guest of the Majlis" in state.badges
    assert "majlis" in state.completed_scenes
    # Badge awards no longer auto-transition. The visitor stays in the current
    # scene until they explicitly ask to travel.
    assert state.current_scene == "majlis"
    assert state.current_phase == StoryPhase.MAJLIS_EXPLORE
    assert state.explored_objects == ["dallah", "sadu_carpet", "bakhoor", "cushion"]
    assert state.questions_asked == 1


def test_transition_changes_scene():
    state = GameState()
    # Test transitioning from majlis to the exterior of Masjid Fanar
    dispatch_tool("transition_scene", {
        "scene_id": "masjid_ext",
        "transition_line": "Let us journey to Masjid Fanar."
    }, state)
    
    assert state.current_scene == "masjid_ext"
    assert state.current_phase == StoryPhase.MASJID_ARRIVAL
    assert state.explored_objects == []
    assert state.questions_asked == 0


def test_transition_from_completed_majlis_resets_per_scene_progress():
    state = GameState(
        current_scene="majlis",
        current_phase=StoryPhase.MAJLIS_EXPLORE,
        explored_objects=["dallah", "sadu_carpet", "bakhoor", "cushion"],
        questions_asked=1,
        completed_scenes=["majlis"],
        badges=["ضيف المجلس · Guest of the Majlis"],
    )

    result = dispatch_tool("transition_scene", {
        "scene_id": "masjid_ext",
        "transition_line": "Let us journey to Masjid Fanar."
    }, state)

    assert "Transitioning to scene 'masjid_ext'" in result
    assert state.current_scene == "masjid_ext"
    assert state.current_phase == StoryPhase.MASJID_ARRIVAL
    assert state.explored_objects == []
    assert state.questions_asked == 0
    assert state.completed_scenes == ["majlis"]
    assert state.badges == ["ضيف المجلس · Guest of the Majlis"]


def test_supplementary_auxiliary_tools():
    """
    Verifies state tracking and returns of secondary animation and UI tools.
    """
    state = GameState()
    
    # Test trigger_animation behavior
    anim_result = dispatch_tool("trigger_animation", {"animation": "offer_coffee"}, state)
    assert "offer_coffee" in anim_result
    
    # Test open_ui behavior
    ui_result = dispatch_tool("open_ui", {"panel": "map"}, state)
    assert "map" in ui_result
    
    # Test give_directions behavior
    directions_result = dispatch_tool("give_directions", {
        "destination": "bakhoor",
        "instruction": "Look at the corner of the majlis room."
    }, state)
    assert "bakhoor" in directions_result
