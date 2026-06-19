from src.storyline.storyline import GameState
from src.tools.tools import dispatch_tool

def test_explore_object_updates_state():
    state = GameState()
    dispatch_tool("explore_object", {
        "object_id": "dallah",
        "spoken_context": "..."
    }, state)
    assert "dallah" in state.explored_objects

def test_badge_not_awarded_when_incomplete():
    state = GameState()
    result = dispatch_tool("award_badge", {
        "scene_name": "majlis",
        "badge_title": "test",
        "congratulations": "..."
    }, state)
    assert "not yet completable" in result
    assert state.badges == []

def test_badge_awarded_when_complete():
    state = GameState()
    for obj in ["dallah", "sadu_carpet", "bakhoor", "cushion"]:
        dispatch_tool("explore_object", {"object_id": obj, "spoken_context": "..."}, state)
    state.questions_asked = 1
    result = dispatch_tool("award_badge", {
        "scene_name": "majlis",
        "badge_title": "ضيف المجلس",
        "congratulations": "أحسنت"
    }, state)
    assert "awarded" in result
    assert "majlis" in state.completed_scenes

def test_transition_changes_scene():
    state = GameState()
    dispatch_tool("transition_scene", {
        "scene_id": "souq",
        "transition_line": "..."
    }, state)
    assert state.current_scene == "souq"