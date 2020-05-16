import os
import sys
import sc2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.constants import *

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


async def BaseBuildOrder(self):
    CCs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
    # If no command center exists, attack-move with all workers and cyclones
    if not CCs:
        return
    else:
        # Otherwise, grab the first command center from the list of command centers
        cc: Unit = CCs.first

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

        # Build ADDONS TECH

        sp: Unit
        for sp in self.structures(UnitTypeId.BARRACKS).ready.idle:
            if not sp.has_add_on:
                if self.can_afford(UnitTypeId.BARRACKSREACTOR):
                    sp.build(UnitTypeId.BARRACKSREACTOR)
        for sp in self.structures(UnitTypeId.FACTORY).ready.idle:
            if not sp.has_add_on:
                if self.can_afford(UnitTypeId.TECHLAB):
                    sp.build(UnitTypeId.FACTORYTECHLAB)
        # Morph commandcenter to orbitalcommand
        # Check if tech requirement for orbital is complete (e.g. you need a barracks to be able to morph an orbital)
        orbital_tech_requirement: float = self.tech_requirement_progress(UnitTypeId.ORBITALCOMMAND)
        if orbital_tech_requirement == 1:
            # Loop over all idle command centers (CCs that are not building SCVs or morphing to orbital)
            for cc in self.townhalls(UnitTypeId.COMMANDCENTER).idle:
                # Check if we have 150 minerals; this used to be an issue when the API returned 550 (value) of the orbital, but we only wanted the 150 minerals morph cost
                if self.can_afford(UnitTypeId.ORBITALCOMMAND):
                    cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)

        # Build ARMY
        # Make reapers if we can afford them and we have supply remaining
        if self.supply_left > 0:
            # Loop through all idle barracks
            for rax in self.structures(UnitTypeId.BARRACKS).idle:
                if self.can_afford(UnitTypeId.MARINE):
                    rax.train(UnitTypeId.MARINE)

            # Loop through all idle barracks
            for facto in self.structures(UnitTypeId.FACTORY).idle:
                if self.can_afford(UnitTypeId.WIDOWMINE):
                    facto.train(UnitTypeId.WIDOWMINE)
