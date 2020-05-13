import os
import sys
import sc2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


async def BaseBuildOrder(self):
    CCs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
    # If no command center exists, attack-move with all workers and cyclones
    if not CCs:
        return
    else:
        # Otherwise, grab the first command center from the list of command centers
        cc: Unit = CCs.first

    # If we have supply depots (careful, lowered supply depots have a different UnitTypeId: UnitTypeId.SUPPLYDEPOTLOWERED)
    if self.structures(UnitTypeId.SUPPLYDEPOT):
        # If we have no barracks
        if not self.structures(UnitTypeId.BARRACKS):
            # If we can afford barracks
            if self.can_afford(UnitTypeId.BARRACKS):
                # Near same command as above with the depot
                await self.build(UnitTypeId.BARRACKS, near=cc.position.towards(self.game_info.map_center, 8))

        # If we have at least one barracks that is completed, build factory
        if self.structures(UnitTypeId.BARRACKS).ready:
            if self.structures(UnitTypeId.FACTORY).amount < 1 and not self.already_pending(UnitTypeId.FACTORY):
                if self.can_afford(UnitTypeId.FACTORY):
                    position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                    await self.build(UnitTypeId.FACTORY, near=position)
            # If we have a barracks (complete or under construction) and less than 2 gas structures (here: refineries)
        elif self.structures(UnitTypeId.BARRACKS) and self.gas_buildings.amount < 2:
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
