from src.storyline.storyline import GameState

def test_scene_not_completable_without_all_objects():
    state = GameState()
    state.object_explored("dallah")
    assert state.scene_completable() == False

def test_scene_completable_when_requirements_met():
    state = GameState()
    for obj in ["dallah", "sadu_carpet", "bakhoor", "cushion"]:
        state.object_explored(obj)
    state.questions_asked = 1
    assert state.scene_completable() == True