# src/storyline/storyline.py

from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class StoryPhase(Enum):
    # Majlis exterior + interior
    MAJLIS_INTRO         = "majlis_intro"
    MAJLIS_ENTER         = "majlis_enter"
    MAJLIS_COFFEE        = "majlis_coffee"
    MAJLIS_EXPLORE       = "majlis_explore"
    MAJLIS_COMPLETE      = "majlis_complete"

    # Mosque exterior + interior
    MASJID_ARRIVAL       = "masjid_arrival"
    MASJID_ENTER         = "masjid_enter"
    MASJID_EXPLORE       = "masjid_explore"
    MASJID_COMPLETE      = "masjid_complete"

    # Fort
    ZUBARAH_ARRIVAL      = "zubarah_arrival"
    ZUBARAH_EXPLORE      = "zubarah_explore"
    ZUBARAH_COMPLETE     = "zubarah_complete"

    JOURNEY_COMPLETE     = "journey_complete"


SCENE_REQUIREMENTS = {
    # Exterior scenes are cinematic transition scenes only.
    # They are not completable, do not award badges, and have no explorable objects.
    "majlis_ext": {
        "required_objects":   None,
        "required_questions":  None,
        "badge_title":         None,
        "next_scene":          "majlis",
        "next_phase":          StoryPhase.MAJLIS_ENTER,
    },
    "majlis": {
        "required_objects":   ["dallah", "sadu_carpet", "bakhoor", "cushion"],
        "required_questions":  1,
        "badge_title":         "ضيف المجلس · Guest of the Majlis",
        "next_scene":          "masjid_ext",
        "next_phase":          StoryPhase.MASJID_ARRIVAL,
    },
    "masjid_ext": {
        "required_objects":   None,
        "required_questions":  None,
        "badge_title":         None,
        "next_scene":          "masjid",
        "next_phase":          StoryPhase.MASJID_ENTER,
    },
    "masjid": {
        "required_objects":   ["mihrab", "quran", "hadeeth", "imam"],
        "required_questions":  1,
        "badge_title":         "زائر المسجد · Visitor of the Masjid",
        "next_scene":          "zubarah",
        "next_phase":          StoryPhase.ZUBARAH_ARRIVAL,
    },
    "zubarah": {
        "required_objects":   ["main_gate", "watchtower", "inner_court", "well"],
        "required_questions":  1,
        "badge_title":         "حارس الزبارة · Guardian of Zubarah",
        "next_scene":          None,
        "next_phase":          StoryPhase.JOURNEY_COMPLETE,
    },
}


@dataclass
class GameState:
    current_phase:     StoryPhase | str = StoryPhase.MAJLIS_INTRO
    current_scene:     str              = "majlis_ext"
    explored_objects:  list             = field(default_factory=list)
    questions_asked:   int              = 0
    completed_scenes:  list             = field(default_factory=list)
    inventory:         list             = field(default_factory=list)
    badges:            list             = field(default_factory=list)

    def __post_init__(self):
        self.current_phase = self._coerce_phase(self.current_phase)

        # Keep old tests/backends safe: many callers set current_phase but omit
        # current_scene, which used to default to majlis_ext. Infer the real scene
        # from the phase so MAJLIS_EXPLORE checks majlis objects, not exterior ones.
        if self.current_scene in (None, "", "majlis_ext"):
            phase_to_scene = {
                StoryPhase.MAJLIS_ENTER: "majlis",
                StoryPhase.MAJLIS_COFFEE: "majlis",
                StoryPhase.MAJLIS_EXPLORE: "majlis",
                StoryPhase.MAJLIS_COMPLETE: "majlis",
                StoryPhase.MASJID_ARRIVAL: "masjid_ext",
                StoryPhase.MASJID_ENTER: "masjid",
                StoryPhase.MASJID_EXPLORE: "masjid",
                StoryPhase.MASJID_COMPLETE: "masjid",
                StoryPhase.ZUBARAH_ARRIVAL: "zubarah",
                StoryPhase.ZUBARAH_EXPLORE: "zubarah",
                StoryPhase.ZUBARAH_COMPLETE: "zubarah",
            }
            self.current_scene = phase_to_scene.get(self.current_phase, self.current_scene or "majlis")

        self.explored_objects = list(self.explored_objects or [])
        self.completed_scenes = list(self.completed_scenes or [])
        self.inventory = list(self.inventory or [])
        self.badges = list(self.badges or [])
        self.questions_asked = int(self.questions_asked or 0)

    @staticmethod
    def _coerce_phase(value: Any) -> StoryPhase:
        if isinstance(value, StoryPhase):
            return value
        if isinstance(value, str):
            for phase in StoryPhase:
                if value == phase.value or value == phase.name:
                    return phase
        return StoryPhase.MAJLIS_INTRO

    def object_explored(self, obj_id: str):
        if obj_id and obj_id not in self.explored_objects:
            self.explored_objects.append(obj_id)

    def scene_completable(self) -> bool:
        reqs = SCENE_REQUIREMENTS.get(self.current_scene, {})

        if self.current_scene in self.completed_scenes:
            return False

        # Cinematic transition scenes have no badge and no required objects.
        # They should not auto-complete; they move only through transition_scene.
        if reqs.get("badge_title") is None and reqs.get("required_objects") is None:
            return False

        req_objs = reqs.get("required_objects") or []
        req_questions = reqs.get("required_questions") or 0
        return all(obj in self.explored_objects for obj in req_objs) and self.questions_asked >= req_questions

    def complete_scene(self):
        reqs = SCENE_REQUIREMENTS.get(self.current_scene)
        if not reqs:
            return

        if self.current_scene not in self.completed_scenes:
            self.completed_scenes.append(self.current_scene)

        badge_title = reqs.get("badge_title")
        if badge_title and badge_title not in self.badges:
            self.badges.append(badge_title)

        # Stay in the same exploration phase after badge award so the visitor
        # can keep asking unlimited Q&A until they explicitly request travel.
