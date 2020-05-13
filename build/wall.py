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

    # Build refinery
    elif self.structures(UnitTypeId.BARRACKS) and self.gas_buildings.amount < 1:
        if self.can_afford(UnitTypeId.REFINERY):
            # All the vespene geysirs nearby, including ones with a refinery on top of it
            vgs = self.vespene_geyser.closer_than(10, cc)
            for vg in vgs:
                if self.gas_buildings.filter(lambda unit: unit.distance_to(vg) < 1):
                    continue
                # Select a worker closest to the vespene geysir
                worker: Unit = self.select_build_worker(vg)
                # Worker can be none in cases where all workers are dead
                # or 'select_build_worker' function only selects from workers which carry no minerals
                if worker is None:
                    continue
                # Issue the build command to the worker, important: vg has to be a Unit, not a position
                worker.build_gas(vg)
                # Only issue one build geysir command per frame
                break
