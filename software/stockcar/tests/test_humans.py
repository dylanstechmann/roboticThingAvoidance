import random
import unittest

from stockcar import mission
from stockcar.field import Field
from stockcar.geometry import rectangle, separation
from stockcar.humans import (HUMAN_RADIUS_IN, HumanMissionSim, human_polygon, min_human_clearance,
                             place_humans, run_human)


class HumanPlacementTests(unittest.TestCase):
    def test_nested_placements_cover_zones_and_clear_geometry(self):
        field = Field()
        layout = mission.random_layout(random.Random(106), field, reading="offsets",
                                       yaw_mode="aligned", obstacles=True)
        humans = place_humans(106, layout, field)
        self.assertEqual(len(humans), 10)
        self.assertEqual({h["zone"] for h in humans[:4]}, {"start", "pit_lane", "lane_change", "turn"})
        self.assertEqual(place_humans(106, layout, field), humans)
        for i, human in enumerate(humans):
            poly = human_polygon(human)
            self.assertTrue(all(separation(poly, b) >= 0.5 for b in field.barriers()))
            self.assertTrue(all(separation(poly, p) >= 1.0 for p in layout.polys))
            for other in humans[:i]:
                self.assertGreaterEqual(separation(poly, human_polygon(other)), 1.0)

    def test_closer_human_has_smaller_signed_clearance(self):
        robot = rectangle(0, 0, 0, 10, 10)
        near = {"cx": 12, "cy": 0, "radius_in": HUMAN_RADIUS_IN}
        far = {"cx": 22, "cy": 0, "radius_in": HUMAN_RADIUS_IN}
        self.assertAlmostEqual(min_human_clearance(robot, [near]), 12 - HUMAN_RADIUS_IN - 5)
        self.assertGreater(min_human_clearance(robot, [far]), min_human_clearance(robot, [near]))


class HumanMissionTests(unittest.TestCase):
    def test_seeded_single_human_completes_without_contact(self):
        info = run_human(105, 1, max_steps=4000)
        self.assertTrue(info["completed"])
        self.assertFalse(info["aborted"])
        self.assertEqual(info["human_contact_count"], 0)
        self.assertGreater(info["min_clearance_in"], 0)

    def test_human_contact_aborts_immediately_and_is_not_vehicle_contact(self):
        field = Field()
        start = ((field.start_box[0] + field.start_box[2]) / 2,
                 (field.start_box[1] + field.start_box[3]) / 2)
        human = {"id": "HX", "cx": start[0], "cy": start[1], "radius_in": HUMAN_RADIUS_IN,
                 "zone": "start", "side": "low"}
        sim = HumanMissionSim(humans=[human])
        layout = mission.random_layout(random.Random(7), field, obstacles=False)
        sim.reset(layout)
        _, _, done, info = sim.step()
        self.assertTrue(done)
        self.assertTrue(info["aborted"])
        self.assertEqual(info["stop_reason"], "human_contact")
        self.assertEqual(info["human_contact_count"], 1)
        self.assertEqual(info["human_contact_frames"], 1)
        self.assertEqual(info["vehicle_contact_steps"], [0, 0, 0])
        self.assertLess(info["min_clearance_in"], 0)

    def test_wall_adjacent_lane_change_human_changes_the_oracle_route(self):
        field = Field()
        layout = mission.random_layout(random.Random(7), field, obstacles=False)
        plain = HumanMissionSim()
        plain.reset(layout)
        human = {"id": "HL", "cx": 60.0, "cy": 6.5, "radius_in": HUMAN_RADIUS_IN,
                 "zone": "lane_change", "side": "low"}
        avoided = HumanMissionSim(humans=[human])
        avoided.reset(layout)
        self.assertNotEqual(plain.routes["LAP"].pts, avoided.routes["LAP"].pts)
        self.assertEqual(avoided.infeasible_humans, 0)


if __name__ == "__main__":
    unittest.main()
