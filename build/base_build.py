import os
import sys

from sc2.constants import *
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


async def BaseBuildOrder(self):
    CCs: Units = self.townhalls
    if not CCs:
        return
    else:
        # Otherwise, grab the first command center from the list of command centers
        cc: Unit = CCs.first
    position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)

    # TRAIN VCS

    for cc in CCs:
        if self.can_afford(UnitTypeId.SCV) and (cc.assigned_harvesters < cc.ideal_harvesters) and cc.is_idle:
            cc.train(UnitTypeId.SCV)

    # BUILD MORE BARRACKS

    if self.structures(UnitTypeId.SUPPLYDEPOT).ready:
        if self.structures(UnitTypeId.BARRACKS).amount == 0 and not self.already_pending(UnitTypeId.BARRACKS):
            if self.can_afford(UnitTypeId.BARRACKS):
                await self.build(UnitTypeId.BARRACKS, near=position)
        if len(self.units(UnitTypeId.BARRACKS)) < (self.iteration / self.ITERATIONS_PER_MINUTE) and self.townhalls.amount > 1:
            if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                await self.build(UnitTypeId.BARRACKS, near=position)

    # If we have at least one barracks that is completed, BUILD FACTORY AND MORE
    if self.structures(UnitTypeId.BARRACKS).ready:
        if self.structures(UnitTypeId.FACTORY).amount < 1 and not self.already_pending(UnitTypeId.FACTORY):
            if self.can_afford(UnitTypeId.FACTORY):
                await self.build(UnitTypeId.FACTORY, near=position)
        """if len(self.units(UnitTypeId.FACTORY)) < (self.iteration / self.ITERATIONS_PER_MINUTE) and self.townhalls.amount > 1:
            if self.can_afford(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.FACTORY):
                await self.build(UnitTypeId.FACTORY, near=position)"""
    if self.structures(UnitTypeId.FACTORY).ready:
        if self.structures(UnitTypeId.STARPORT).amount < 1 and not self.already_pending(UnitTypeId.STARPORT):
            if self.can_afford(UnitTypeId.STARPORT):
                await self.build(UnitTypeId.STARPORT, near=position)

    # If we have a barracks (complete or under construction) and less than 2 gas structures (here: REFINERIES)
    if self.structures(UnitTypeId.BARRACKS) and self.gas_buildings.amount < 3:
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
                    # Issue the build command to the worker, important: vg has to be a Uni t, not a position
                    worker.build_gas(vg)
                    # Only issue one build geysir command per frame
                    break

    # BUILD DEPOT
    if self.supply_left < 5:
        if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 2:
            await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))
            for depos in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
                depos(AbilityId.MORPH_SUPPLYDEPOT_LOWER)


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
    for sp in self.structures(UnitTypeId.STARPORT).ready.idle:
        if not sp.has_add_on:
            if self.can_afford(UnitTypeId.STARPORTREACTOR):
                sp.build(UnitTypeId.STARPORTREACTOR)

    # Morph commandcenter to orbitalcommand
    # Check if tech requirement for orbital is complete (e.g. you need a barracks to be able to morph an orbital)
    orbital_tech_requirement: float = self.tech_requirement_progress(UnitTypeId.ORBITALCOMMAND)
    if orbital_tech_requirement == 1:
        # Loop over all idle command centers (CCs that are not building SCVs or morphing to orbital)
        for cc in self.townhalls(UnitTypeId.COMMANDCENTER).idle:
            # Check if we have 150 minerals; this used to be an issue when the API returned 550 (value) of the orbital, but we only wanted the 150 minerals morph cost
            if self.can_afford(UnitTypeId.ORBITALCOMMAND):
                cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)

    # BUILD MISSILE TURRET
    for cc in self.townhalls(UnitTypeId.COMMANDCENTER).ready:
        if self.structures(UnitTypeId.FACTORY).amount > 0 and self.structures(UnitTypeId.MISSILETURRET).ready.amount < 2:
            if self.can_afford(UnitTypeId.MISSILETURRET) and self.already_pending(UnitTypeId.MISSILETURRET) < 2:
                await self.build(UnitTypeId.MISSILETURRET, near=cc.position.towards(self.game_info.map_center, -4))

    for cc in self.townhalls(UnitTypeId.ORBITALCOMMAND).ready:
        if self.structures(UnitTypeId.FACTORY).amount > 0 and self.structures(
                UnitTypeId.MISSILETURRET).ready.amount < 2:
            if self.can_afford(UnitTypeId.MISSILETURRET) and self.already_pending(UnitTypeId.MISSILETURRET) < 2:
                await self.build(UnitTypeId.MISSILETURRET, near=cc.position.towards(self.game_info.map_center, -4))

    # Build ARMY
    # Make reapers if we can afford them and we have supply remaining
    if self.supply_left > 0:
        # Loop through all idle barracks
        for rax in self.structures(UnitTypeId.BARRACKS).idle:
            if self.can_afford(UnitTypeId.MARINE):
                rax.train(UnitTypeId.MARINE)
                if Unit.has_add_on:
                    rax.train(UnitTypeId.MARINE) * 2

        for facto in self.structures(UnitTypeId.FACTORY).idle:
            if self.can_afford(UnitTypeId.CYCLONE):
                facto.train(UnitTypeId.CYCLONE)

        for starp in self.structures(UnitTypeId.STARPORT).idle:
            if self.can_afford(UnitTypeId.MEDIVAC):
                starp.train(UnitTypeId.MEDIVAC)
                if Unit.has_add_on:
                    starp.train(UnitTypeId.MEDIVAC) * 2

    # ATTACK
    # send them to their death
    marines: Units = self.units(UnitTypeId.MARINE).idle
    cyclones: Units = self.units(UnitTypeId.CYCLONE).idle
    medivacs: Units = self.units(UnitTypeId.MEDIVAC).idle
    if marines.amount > 15 and medivacs.amount > 2:
        target: Point2 = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
        for marine in marines:
            marine.attack(target)
            for medivac in medivacs:
                medivac.move(marine)
        for cyclone in cyclones:
            cyclone.attack(target)
