import os
import sys
import sc2

from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.ids.unit_typeid import UnitTypeId

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

uti = UnitTypeId


class MyBot(sc2.BotAI):
    async def on_step(self, iteration):
        ccs: Units = self.townhalls(uti.COMMANDCENTER)
        if not ccs:
            target: Point2 = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
            for unit in self.units(uti.MARINE):
                unit.attack(target)
            return
        else:
            cc: Unit = ccs.first

        await self.build_scv_supply()
        await self.build_gas_and_barrack()
        await self.expand()

        # Saturate gas en scv
        for refinery in self.gas_buildings:
            if refinery.assigned_harvesters < refinery.ideal_harvesters:
                worker: Units = self.workers.closer_than(10, refinery)
                if worker:
                    worker.random.gather(refinery)

        for scv in self.workers.idle:
            scv.gather(self.mineral_field.closest_to(cc))

    async def build_scv_supply(self):  # BUILD SCV AND SUPPLY
        ccs: Units = self.townhalls(uti.COMMANDCENTER)
        cc: Unit = ccs.first
        # Train more SCVs
        if self.can_afford(uti.SCV) and self.supply_workers < 18 and cc.is_idle:
            cc.train(uti.SCV)

        # Build more depots
        elif (
                self.supply_left < (
                2 if self.structures(uti.BARRACKS).amount < 3 else 4) and self.supply_used >= 14
        ):
            if self.can_afford(uti.SUPPLYDEPOT) and self.already_pending(uti.SUPPLYDEPOT) < 2:
                await self.build(uti.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))

        # Send idle workers to gather minerals near command center
        for scv in self.workers.idle:
            scv.gather(self.mineral_field.closest_to(cc))

    async def expand(self):
        # expand if we can afford and have less than 2 bases
        if self.townhalls.amount < 2 and self.already_pending(uti.COMMANDCENTER) == 0 and self.can_afford(
                uti.COMMANDCENTER):
            await self.expand_now()

    async def build_gas_and_barrack(self):
        CCs: Units = self.townhalls(uti.COMMANDCENTER)
        cc: Unit = CCs.first
        # If we have supply depots (careful, lowered supply depots have a different UnitTypeId:
        # UnitTypeId.SUPPLYDEPOTLOWERED)
        if self.structures(uti.SUPPLYDEPOT):
            # If we have no barracks
            if not self.structures(uti.BARRACKS):
                # If we can afford barracks
                if self.can_afford(uti.BARRACKS):
                    # Near same command as above with the depot
                    await self.build(uti.BARRACKS, near=cc.position.towards(self.game_info.map_center, 8))

            # If we have a barracks (complete or under construction) and less than 2 gas structures (here: refineries)
            elif self.structures(uti.BARRACKS) and self.gas_buildings.amount < 1:
                if self.can_afford(uti.REFINERY):
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


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Terran, MyBot()), Computer(Race.Random, Difficulty.Easy)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
