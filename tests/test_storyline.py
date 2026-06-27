#tests/test_storyline.py
import sys
from pathlib import Path

# Find project root (one level up from tests/) and add to python path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pytest
from src.storyline.storyline import GameState, StoryPhase

def test_scene_not_completable_without_all_objects():
    """
    Ensures that 'majlis' scene does not evaluate to completed
    until all 4 required objects are explored and at least 1 question is asked.
    """
    state = GameState()
    # Set target interior scene explicitly because default is majlis_ext (exterior transition)
    state.current_scene = "majlis" 
    
    # Explore only one object
    state.object_explored("dallah")
    
    # Verify scene is not completable
    assert state.scene_completable() is False, "Scene should not be completable with only one object explored."


def test_scene_completable_when_requirements_met():
    """
    Verifies that 'majlis' scene transitions to completable (True)
    once all required objects are explored and the minimum questions asked threshold is reached.
    """
    state = GameState()
    # Set target interior scene explicitly
    state.current_scene = "majlis"
    
    # Explore all four required objects
    for obj in ["dallah", "sadu_carpet", "bakhoor", "cushion"]:
        state.object_explored(obj)
        
    # Meet the minimum question requirement
    state.questions_asked = 1
    
    # Verify scene is successfully completable
    assert state.scene_completable() is True, "Scene should be completable when all objects are explored and questions asked."


def test_exterior_scene_is_not_completable():
    """
    Verifies that exterior transition scenes (like 'majlis_ext' and 'masjid_ext')
    are cinematic only. They do not award badges and should move only through
    transition_scene.
    """
    state = GameState()
    # 'majlis_ext' is the default start scene
    assert state.current_scene == "majlis_ext"
    assert state.scene_completable() is False, "Transition/exterior scenes should not be badge-completable."


def test_complete_scene_awards_badge_without_transitioning():
    """
    Verifies that calling complete_scene() correctly appends the badge,
    adds the scene to completed_scenes list, and keeps the visitor in the
    current scene until an explicit transition_scene call.
    """
    state = GameState()
    state.current_scene = "majlis"
    state.current_phase = StoryPhase.MAJLIS_EXPLORE
    
    # Meet requirements
    for obj in ["dallah", "sadu_carpet", "bakhoor", "cushion"]:
        state.object_explored(obj)
    state.questions_asked = 1
    
    # Trigger scene completion
    state.complete_scene()
    
    # Check assertions
    assert "majlis" in state.completed_scenes, "The scene must be recorded as completed."
    assert "ضيف المجلس · Guest of the Majlis" in state.badges, "The player must be awarded the correct badge."
    assert state.current_scene == "majlis", "Completing a badge must not transition scenes."
    assert state.current_phase == StoryPhase.MAJLIS_EXPLORE, "The phase should remain in the same exploration scene."
    assert state.explored_objects == ["dallah", "sadu_carpet", "bakhoor", "cushion"]
    assert state.questions_asked == 1
