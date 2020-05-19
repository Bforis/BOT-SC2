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

    # BUILD MORE BARRACKS

    if self.structures(UnitTypeId.SUPPLYDEPOT).ready:
        """if self.structures(UnitTypeId.BARRACKS).amount == 1 and not self.already_pending(UnitTypeId.BARRACKS):
            if self.can_afford(UnitTypeId.BARRACKS):
                position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                await self.build(UnitTypeId.BARRACKS, near=position)"""
        if len(self.units(UnitTypeId.BARRACKS)) < ((self.iteration / self.ITERATIONS_PER_MINUTE) / 2):
            if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                await self.build(UnitTypeId.BARRACKS, near=position)

    # If we have at least one barracks that is completed, BUILD FACTORY AND MORE
    if self.structures(UnitTypeId.BARRACKS).ready:
        """if self.structures(UnitTypeId.FACTORY).amount < 1 and not self.already_pending(UnitTypeId.FACTORY):
            if self.can_afford(UnitTypeId.FACTORY):
                position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                await self.build(UnitTypeId.FACTORY, near=position)"""
        if len(self.units(UnitTypeId.FACTORY)) < ((self.iteration / self.ITERATIONS_PER_MINUTE) / 2):
            if self.can_afford(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.FACTORY):
                position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                await self.build(UnitTypeId.FACTORY, near=position)

    # If we have a barracks (complete or under construction) and less than 2 gas structures (here: REFINERIES)
    if self.structures(UnitTypeId.BARRACKS) and self.gas_buildings.amount < 6:
        if self.can_afford(UnitTypeId.REFINERY):
            # All the vespene geysirs nearby, including ones with a refinery on top of it
            for cc in CCs:
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

    # BUILD DEPOT
    if self.supply_left < 5:
        if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 2:
            await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))

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
                if Unit.has_add_on:
                    rax.train(UnitTypeId.MARINE) * 2

            # Loop through all idle barracks
        for facto in self.structures(UnitTypeId.FACTORY).idle:
            if self.can_afford(UnitTypeId.CYCLONE):
                facto.train(UnitTypeId.CYCLONE)

    # ATTACK
    # send them to their death
    marines: Units = self.units(UnitTypeId.MARINE).idle
    cyclones: Units = self.units(UnitTypeId.CYCLONE).idle
    if marines.amount > 10 and cyclones.amount > 2:
        target: Point2 = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
        for marine in marines:
            marine.attack(target)
        for cyclone in cyclones:
            cyclone.attack(target)
