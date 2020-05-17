import sc2
import os
import sys
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
import random
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.constants import *


async def TestBuild(self, iteration):
    CCs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
    # If no command center exists, attack-move with all workers and cyclones
    if not CCs:
        return
    else:
        # Otherwise, grab the first command center from the list of command centers
        cc: Unit = CCs.first

        # REFINERY AND GAS
        for cc in self.units(UnitTypeId.COMMANDCENTER).ready:
            vaspenes = self.state.vespene_geyser.closer_than(15.0, cc)
            for vaspene in vaspenes:
                if not self.can_afford(UnitTypeId.COMMANDCENTER):
                    break
                worker = self.select_build_worker(vaspene.position)
                if worker is None:
                    break
                if not self.units(UnitTypeId.COMMANDCENTER).closer_than(1.0, vaspene).exists:
                    await self.do(worker.build(UnitTypeId.COMMANDCENTER, vaspene))

        # BARRACKS AND FACTORY
        if len(self.units(UnitTypeId.BARRACKS)) < ((self.iteration / self.ITERATIONS_PER_MINUTE) / 2):
            if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                await self.build(UnitTypeId.BARRACKS, near=position)

        if len(self.units(UnitTypeId.FACTORY)) < ((self.iteration / self.ITERATIONS_PER_MINUTE) / 2):
            if self.can_afford(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.FACTORY):
                position: Point2 = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                await self.build(UnitTypeId.FACTORY, near=position)

        # BUILD MARINES AND MINES ?

        for brk in self.units(UnitTypeId.BARRACKS).ready.idle:
            if self.can_afford(UnitTypeId.MARINE) and self.supply_left > 0:
                await self.do(brk.train(UnitTypeId.MARINE))

        for fct in self.units(UnitTypeId.FACTORY).ready.idle:
            if self.can_afford(UnitTypeId.CYCLONE) and self.supply_left > 0:
                await self.do(fct.train(UnitTypeId.CYCLONE))

        # FIND ENEMY

        if len(self.enemy_units) > 0:
            return random.choice(self.enemy_units)
        elif len(self.enemy_structures) > 0:
            return random.choice(self.enemy_structures)

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
                if self.can_afford(UnitTypeId.CYCLONE):
                    facto.train(UnitTypeId.CYCLONE)

        # ATTACK

        # Pick a random enemy structure's position
        targets = self.enemy_structures
        if targets:
            return targets.random.position

        # Pick a random enemy unit's position
        targets = self.enemy_units
        if targets:
            return targets.random.position

        # Pick enemy start location if it has no friendly units nearby
        if min([unit.distance_to(self.enemy_start_locations[0]) for unit in self.units]) > 5:
            return self.enemy_start_locations[0]

        # Every 50 iterations (here: every 50*8 = 400 frames)
        if iteration % 50 == 0 and self.units(UnitTypeId.CYCLONE).amount > 2:
            target: Point2 = self.select_target()
            forces: Units = self.units(UnitTypeId.CYCLONE) + self.units(UnitTypeId.MARINE)
            # Every 4000 frames: send all forces to attack-move the target position
            if iteration % 500 == 0:
                for unit in forces:
                    unit.attack(target)
            # Every 400 frames: only send idle forces to attack the target position
            else:
                for unit in forces.idle:
                    unit.attack(target)
