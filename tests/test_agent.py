# tests/test_agent.py
# Real API tests — run with: PYTHONPATH=. python tests/test_agent.py

from dotenv import load_dotenv
load_dotenv()

import asyncio
from src.storyline.storyline import GameState, StoryPhase, SCENE_REQUIREMENTS
from src.agent import run_turn

# ── helpers ───────────────────────────────────────────────────────────────────

def fresh_majlis_explore() -> GameState:
    """A clean state sitting in the majlis explore phase."""
    state = GameState()
    state.current_phase = StoryPhase.MAJLIS_EXPLORE
    return state

def completed_majlis() -> GameState:
    """A state where all majlis requirements are met — badge should fire."""
    state = GameState()
    state.current_phase = StoryPhase.MAJLIS_EXPLORE
    for obj in SCENE_REQUIREMENTS["majlis"]["required_objects"]:
        state.object_explored(obj)
    state.questions_asked = 2
    return state

def print_result(result: dict, state: GameState, extras: list = None):
    print(f"  Reply: {result['reply']}")
    print(f"  Tools: {result['tool_calls_executed']}")
    if extras:
        for label, value in extras:
            print(f"  {label}: {value}")


# ── tests ─────────────────────────────────────────────────────────────────────

async def test_1_transition_scene():
    """
    'خذني إلى الزبارة' should fire:
      - trigger_animation(gesture_follow)
      - transition_scene(zubarah)
    And state.current_scene should change to 'zubarah'
    """
    print("\n── Test 1: transition scene ── \"خذني إلى الزبارة\"")
    state  = fresh_majlis_explore()
    result = await run_turn("خذني إلى الزبارة", [], state)
    print_result(result, state, [
        ("Scene after", state.current_scene),
        ("Phase after", state.current_phase),
    ])

    tool_names = [t["name"] for t in result["tool_calls_executed"]]
    assert "transition_scene" in tool_names, \
        f"Expected transition_scene but got: {tool_names}"
    assert state.current_scene == "zubarah", \
        f"Expected scene=zubarah but got: {state.current_scene}"
    print("  ✓ passed")


async def test_2_give_directions():
    """
    'أين البخور؟' should fire give_directions(destination='bakhoor', ...)
    """
    print("\n── Test 2: give directions ── \"أين البخور؟\"")
    state  = fresh_majlis_explore()
    result = await run_turn("أين البخور؟", [], state)
    print_result(result, state)

    tool_names = [t["name"] for t in result["tool_calls_executed"]]
    assert "give_directions" in tool_names, \
        f"Expected give_directions but got: {tool_names}"

    direction_call = next(t for t in result["tool_calls_executed"]
                         if t["name"] == "give_directions")
    assert "bakhoor" in direction_call["args"].get("destination", "").lower(), \
        f"Expected destination to contain 'bakhoor', got: {direction_call['args']}"
    print("  ✓ passed")


async def test_3_open_map():
    """
    'افتح الخريطة' should fire open_ui(panel='map')
    """
    print("\n── Test 3: open map ── \"افتح الخريطة\"")
    state  = fresh_majlis_explore()
    result = await run_turn("افتح الخريطة", [], state)
    print_result(result, state)

    tool_names = [t["name"] for t in result["tool_calls_executed"]]
    assert "open_ui" in tool_names, \
        f"Expected open_ui but got: {tool_names}"

    ui_call = next(t for t in result["tool_calls_executed"]
                  if t["name"] == "open_ui")
    assert ui_call["args"].get("panel") == "map", \
        f"Expected panel=map but got: {ui_call['args']}"
    print("  ✓ passed")


async def test_4_open_inventory():
    """
    'ما الذي جمعته؟' should fire open_ui(panel='inventory')
    """
    print("\n── Test 4: open inventory ── \"ما الذي جمعته؟\"")
    state  = fresh_majlis_explore()
    result = await run_turn("ما الذي جمعته؟", [], state)
    print_result(result, state)

    tool_names = [t["name"] for t in result["tool_calls_executed"]]
    assert "open_ui" in tool_names, \
        f"Expected open_ui but got: {tool_names}"

    ui_call = next(t for t in result["tool_calls_executed"]
                  if t["name"] == "open_ui")
    assert ui_call["args"].get("panel") == "inventory", \
        f"Expected panel=inventory but got: {ui_call['args']}"
    print("  ✓ passed")


async def test_5_explore_object():
    """
    'ما هذه الدلة؟' should fire explore_object(object_id='dallah', ...)
    and state.explored_objects should contain 'dallah'
    """
    print("\n── Test 5: explore object ── \"ما هذه الدلة؟\"")
    state  = fresh_majlis_explore()
    result = await run_turn("ما هذه الدلة؟", [], state)
    print_result(result, state, [
        ("Explored objects", state.explored_objects)
    ])

    tool_names = [t["name"] for t in result["tool_calls_executed"]]
    assert "explore_object" in tool_names, \
        f"Expected explore_object but got: {tool_names}"
    assert "dallah" in state.explored_objects, \
        f"Expected dallah in explored_objects, got: {state.explored_objects}"
    print("  ✓ passed")


async def test_6_plain_text_no_tools():
    """
    'ما هي قطر؟' is a general question — should return plain text, NO tools
    """
    print("\n── Test 6: plain text ── \"ما هي قطر؟\"")
    state  = fresh_majlis_explore()
    result = await run_turn("ما هي قطر؟", [], state)
    print_result(result, state)

    assert result["tool_calls_executed"] == [], \
        f"Expected no tools but got: {result['tool_calls_executed']}"
    assert len(result["reply"]) > 10, \
        "Expected a real text reply but got empty/short response"
    print("  ✓ passed")


async def test_7_award_badge():
    """
    When all objects explored and questions asked, Fanar should fire award_badge.
    Uses the message 'لقد استكشفت كل شيء في المجلس' to trigger it.
    """
    print("\n── Test 7: award badge ──")
    state = completed_majlis()

    # Confirm setup is correct before calling Fanar
    assert state.scene_completable(), \
        f"Test setup error — scene not completable. explored={state.explored_objects}, questions={state.questions_asked}"
    print(f"  Scene completable: {state.scene_completable()} ✓")

    result = await run_turn(
        "لقد استكشفت كل شيء في المجلس",
        [],
        state
    )
    print_result(result, state, [
        ("Badges earned", state.badges),
        ("Completed scenes", state.completed_scenes),
    ])

    tool_names = [t["name"] for t in result["tool_calls_executed"]]
    assert "award_badge" in tool_names, \
        f"Expected award_badge but got: {tool_names}"
    assert len(state.badges) > 0, \
        "Expected badge in state.badges but it's empty"
    assert "majlis" in state.completed_scenes, \
        "Expected majlis in completed_scenes"
    print("  ✓ passed")


async def test_8_multi_tool_travel_with_animation():
    """
    Travel request should fire BOTH trigger_animation(gesture_follow)
    AND transition_scene in the same turn.
    """
    print("\n── Test 8: multi-tool — travel + animation ──")
    state  = fresh_majlis_explore()
    result = await run_turn("تعال معي إلى مسجد فنار", [], state)
    print_result(result, state, [
        ("Scene after", state.current_scene),
    ])

    tool_names = [t["name"] for t in result["tool_calls_executed"]]
    assert "transition_scene" in tool_names, \
        f"Expected transition_scene but got: {tool_names}"

    # Check scene actually changed
    assert state.current_scene == "masjid", \
        f"Expected scene=masjid but got: {state.current_scene}"
    print("  ✓ passed")


async def test_9_conversation_history():
    """
    History carries context between turns — Maryam should remember
    what was said in the previous turn.
    """
    print("\n── Test 9: conversation history ──")
    state = fresh_majlis_explore()

    # Turn 1
    result1 = await run_turn("مرحباً، أنا أزور قطر للمرة الأولى", [], state)
    print(f"  Turn 1 reply: {result1['reply'][:80]}...")
    print(f"  History after turn 1: {len(result1['updated_history'])} messages")

    # Turn 2 — follow-up that requires remembering turn 1
    result2 = await run_turn(
        "ما الذي يجب أن أعرفه عن الضيافة القطرية؟",
        result1["updated_history"],
        state
    )
    print(f"  Turn 2 reply: {result2['reply'][:80]}...")
    print(f"  History after turn 2: {len(result2['updated_history'])} messages")

    assert len(result2["updated_history"]) > len(result1["updated_history"]), \
        "History should grow between turns"
    assert result2["reply"] and result2["reply"] != "...", \
        "Expected a real reply in turn 2"
    print("  ✓ passed")


async def test_10_majlis_intro_greeting():
    """
    On MAJLIS_INTRO phase, Maryam should greet, introduce herself,
    and fire wave + offer_coffee animations.
    """
    print("\n── Test 10: majlis intro greeting ──")
    state = GameState()   # default phase is MAJLIS_INTRO
    assert state.current_phase == StoryPhase.MAJLIS_INTRO

    result = await run_turn("مرحباً", [], state)
    print_result(result, state)

    tool_names = [t["name"] for t in result["tool_calls_executed"]]
    animations = [
        t["args"].get("animation")
        for t in result["tool_calls_executed"]
        if t["name"] == "trigger_animation"
    ]
    print(f"  Animations triggered: {animations}")

    assert "trigger_animation" in tool_names, \
        f"Expected trigger_animation on intro but got: {tool_names}"
    assert "wave" in animations or "offer_coffee" in animations, \
        f"Expected wave or offer_coffee animation but got: {animations}"
    print("  ✓ passed")


# ── run all ───────────────────────────────────────────────────────────────────

async def main():
    tests = [
        test_1_transition_scene,
        test_2_give_directions,
        test_3_open_map,
        test_4_open_inventory,
        test_5_explore_object,
        test_6_plain_text_no_tools,
        test_7_award_badge,
        test_8_multi_tool_travel_with_animation,
        test_9_conversation_history,
        test_10_majlis_intro_greeting,
    ]

    passed = 0
    failed = []

    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"  ✗ ERROR: {type(e).__name__}: {e}")
            failed.append(test.__name__)

    print(f"\n{'═'*50}")
    print(f"Results: {passed}/{len(tests)} passed")
    if failed:
        print(f"Failed:  {', '.join(failed)}")
    else:
        print("All tests passed ✓")
    print('═'*50)


asyncio.run(main())