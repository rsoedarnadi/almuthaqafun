# storyline.py

from enum import Enum
from dataclasses import dataclass, field

class StoryPhase(Enum):
    # Majlis scene
    MAJLIS_INTRO         = "majlis_intro"          # Maryam welcomes player, offers coffee
    MAJLIS_COFFEE        = "majlis_coffee"          # POV coffee drinking sequence
    MAJLIS_EXPLORE       = "majlis_explore"         # Player explores majlis objects
    MAJLIS_COMPLETE      = "majlis_complete"        # Badge awarded, tour offer made

    # Mosque scene
    MASJID_ARRIVAL       = "masjid_arrival"
    MASJID_EXPLORE       = "masjid_explore"
    MASJID_COMPLETE      = "masjid_complete"

    # Fort scene
    ZUBARAH_ARRIVAL      = "zubarah_arrival"
    ZUBARAH_EXPLORE      = "zubarah_explore"
    ZUBARAH_COMPLETE     = "zubarah_complete"

    JOURNEY_COMPLETE     = "journey_complete"       # All scenes done


# What must happen in each scene before it can be completed
SCENE_REQUIREMENTS = {
    "majlis": {
        "required_objects":   ["dallah", "sadu_carpet", "bakhoor", "cushion"],
        "required_questions":  1,
        "badge_title":         "ضيف المجلس · Guest of the Majlis",
        "next_phase":          StoryPhase.MASJID_ARRIVAL
    },
    "souq": {
        "required_objects":   ["spice_stall", "lantern", "falcon_shop", "textile"],
        "required_questions":  1,
        "badge_title":         "تاجر السوق · Trader of the Souq",
        "next_phase":          StoryPhase.ZUBARAH_ARRIVAL
    },
    "zubarah": {
        "required_objects":   ["main_gate", "watchtower", "inner_court", "well"],
        "required_questions":  1,
        "badge_title":         "حارس الزبارة · Guardian of Zubarah",
        "next_phase":          StoryPhase.MASJID_ARRIVAL
    },
    "masjid": {
        "required_objects":   ["minaret", "prayer_hall", "mihrab", "ablution"],
        "required_questions":  1,
        "badge_title":         "زائر المسجد · Visitor of the Masjid",
        "next_phase":          StoryPhase.JOURNEY_COMPLETE
    }
}


@dataclass
class GameState:
    current_phase:     StoryPhase     = StoryPhase.MAJLIS_INTRO
    current_scene:     str            = "majlis"
    explored_objects:  list           = field(default_factory=list)
    questions_asked:   int            = 0
    completed_scenes:  list           = field(default_factory=list)
    inventory:         list           = field(default_factory=list)
    badges:            list           = field(default_factory=list)

    def object_explored(self, obj_id: str):
        if obj_id not in self.explored_objects:
            self.explored_objects.append(obj_id)

    def scene_completable(self) -> bool:
        reqs = SCENE_REQUIREMENTS.get(self.current_scene, {})
        all_objects_done = all(
            obj in self.explored_objects
            for obj in reqs.get("required_objects", [])
        )
        enough_questions = self.questions_asked >= reqs.get("required_questions", 1)
        return all_objects_done and enough_questions

    def complete_scene(self):
        reqs = SCENE_REQUIREMENTS[self.current_scene]
        self.completed_scenes.append(self.current_scene)
        self.badges.append(reqs["badge_title"])
        self.current_phase = reqs["next_phase"]
        self.explored_objects = []
        self.questions_asked  = 0