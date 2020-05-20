import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2


async def Build_Wall(self):
    ccs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
    depot_placement_positions: Set[Point2] = self.main_base_ramp.corner_depots
    barracks_placement_position: Point2 = self.main_base_ramp.barracks_correct_placement
    depots: Units = self.structures.of_type({UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED})
    if not ccs:
        return
    else:
        cc: Unit = ccs.first
        # Raise depos when enemies are nearby
    for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
        for unit in self.enemy_units:
            if unit.distance_to(depo) < 15:
                break
        else:
            depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

    await self.distribute_workers()

    # Lower depos when no enemies are nearby
    for depo in self.structures(UnitTypeId.SUPPLYDEPOTLOWERED).ready:
        for unit in self.enemy_units:
            if unit.distance_to(depo) < 10:
                depo(AbilityId.MORPH_SUPPLYDEPOT_RAISE)
                break
    if depots:
        depot_placement_positions: Set[Point2] = {
            d for d in depot_placement_positions if depots.closest_distance_to(d) > 1
        }

    # Build depots
    if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0:
        if len(depot_placement_positions) == 0:
            return
        # Choose any depot location
        target_depot_location: Point2 = depot_placement_positions.pop()
        workers: Units = self.workers.gathering
        if workers:  # if workers were found
            worker: Unit = workers.random
            self.do(worker.build(UnitTypeId.SUPPLYDEPOT, target_depot_location))

    # Build barracks
    if depots.ready and self.can_afford(UnitTypeId.BARRACKS) and self.already_pending(UnitTypeId.BARRACKS) == 0:
        if self.structures(UnitTypeId.BARRACKS).amount + self.already_pending(UnitTypeId.BARRACKS) > 0:
            return
        workers = self.workers.gathering
        if workers and barracks_placement_position:  # if workers were found
            worker: Unit = workers.random
            worker.build(UnitTypeId.BARRACKS, barracks_placement_position)
