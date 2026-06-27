#tests/test_prompts.py
import sys
from pathlib import Path

# --- BULLETPROOF PYTHON PATH RESOLUTION ---
# This guarantees that 'src' is discoverable from anywhere on your system.
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pytest
import asyncio
import io

# This prevents Python from crashing with UnicodeEncodeError in standard Windows CMD/PowerShell or non-UTF-8 terminals
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.storyline.storyline import GameState, StoryPhase
from src.prompts.prompts import build_system_prompt

# Mark all test functions in this module as asynchronous for Pytest compatibility
pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_intro_scene_prompt():
    """
    Validates that the system prompt generated for MAJLIS_INTRO contains
    correct metadata, the host's introduction instructions, and the correct phase.
    """
    state = GameState()
    state.current_phase = StoryPhase.MAJLIS_INTRO
    state.current_scene = "majlis"
    
    result = build_system_prompt(state)
    
    # Assertions
    assert result is not None, "System prompt should not be None."
    assert len(result) > 1000, "System prompt is too short."
    
    # Ensure Maryam's identity and bilingual guidelines are intact
    assert "مريم" in result or "Maryam" in result, "Prompt must establish Maryam's identity in Arabic or English."
    assert "الدلة" in result or "dallah" in result, "Prompt must contain reference to Dallah (الدلة)."
    assert "majlis_intro" in result, "Current phase should be mapped in prompt."
    
    print("\n" + "="*80)
    print(" [TEST SUCCESS] SYSTEM PROMPT FOR: MAJLIS_INTRO")
    print("="*80)
    print(result)
    print("="*80)


@pytest.mark.asyncio
async def test_explore_scene_prompt():
    """
    Validates that as objects are explored and questions are asked, 
    the system prompt dynamically updates the remaining required tasks and state variables.
    """
    state = GameState()
    state.current_phase = StoryPhase.MAJLIS_EXPLORE
    state.current_scene = "majlis"
    
    # Simulate a player exploring a couple of items
    explored_items = ["dallah", "bakhoor"]
    for item in explored_items:
        state.object_explored(item)
    
    state.questions_asked = 2
    
    result = build_system_prompt(state)
    
    # Assertions
    assert len(result) > 1000
    assert "Questions asked:   2" in result, "The questions counter must match the current game state."
    
    # Ensure remaining objects like the Sadu woven carpet are correctly listed
    assert "sadu_carpet" in result or "بساط السدو" in result, "Unexplored items must still reside in the target list."
    assert "dallah" not in result.split("Objects remaining:")[1].split("Questions asked:")[0], \
        "Explored items should be filtered out of the remaining required objects list."

    print("\n" + "="*80)
    print(" [TEST SUCCESS] SYSTEM PROMPT FOR: MAJLIS_EXPLORE")
    print("="*80)
    print(result)
    print("="*80)


@pytest.mark.asyncio
async def test_complete_scene_prompt():
    """
    Validates that once all required objects are explored and questions met,
    the system prompt transitions to the MAJLIS_COMPLETE state and enables the completion flags.
    """
    state = GameState()
    state.current_phase = StoryPhase.MAJLIS_COMPLETE
    state.current_scene = "majlis"
    
    # Simulate a player exploring all required items to trigger completion
    explored_items = ["dallah", "bakhoor", "sadu_carpet", "cushion"]
    for item in explored_items:
        state.object_explored(item)
    
    state.questions_asked = 2
    
    result = build_system_prompt(state)
    
    # Assertions
    assert len(result) > 500, "The generated system prompt is too short."
    assert "Questions asked:   2" in result, "The questions counter must match the current game state."
    assert "Scene completable: True" in result, "The scene should evaluate to completed/completable."
    assert "all explored ✓" in result, "The prompt should indicate that all required objects have been explored."
    
    # Ensure explored items are not sitting in the 'remaining' section slice
    remaining_section = result.split("Objects remaining:")[1].split("Questions asked:")[0]
    assert "dallah" not in remaining_section, "Explored objects must be cleared from the remaining list."

    print("\n" + "="*80)
    print(" [TEST SUCCESS] SYSTEM PROMPT FOR: MAJLIS_COMPLETE")
    print("="*80)
    print(result)
    print("="*80)


@pytest.mark.asyncio
async def test_masjid_arrival_prompt():
    """
    Validates that transitioning scene states to the Masjid correctly 
    modifies the mapped descriptions, objects, and phase-specific instructions.
    """
    state = GameState()
    state.current_phase = StoryPhase.MASJID_ARRIVAL
    # Changed from interior 'masjid' to exterior 'masjid_ext' to perfectly match minaret requirements 
    state.current_scene = "masjid_ext"
    
    result = build_system_prompt(state)
    
    # Assertions
    assert len(result) > 1000
    assert "masjid_ext" in result, "Current scene must be registered as masjid_ext."
    assert "minaret" in result or "المئذنة" in result, "Mosque objects like the minaret (المئذنة) must be exposed to the agent."
    assert "spiral minaret" in result or "الحلزونية" in result, "Phase instructions for Masjid arrival must be integrated."
    
    print("\n" + "="*80)
    print(" [TEST SUCCESS] SYSTEM PROMPT FOR: MASJID_ARRIVAL")
    print("="*80)
    print(result)
    print("="*80)


# If run directly as a standard Python file, execute all tests sequentially
if __name__ == "__main__":
    print("Starting Al Muthaqafun Prompt Test Diagnostic...\n")
    asyncio.run(test_intro_scene_prompt())
    asyncio.run(test_explore_scene_prompt())
    asyncio.run(test_complete_scene_prompt())
    asyncio.run(test_masjid_arrival_prompt())
    print("\nAll prompt diagnostics completed successfully!")