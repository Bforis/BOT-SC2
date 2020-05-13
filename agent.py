import os
import sys

import sc2
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from build.base_build import BaseBuildOrder
from build.wall import Build_Wall

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


class MyBot(sc2.BotAI):
    def select_target(self) -> Point2:
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

        # Pick a random mineral field on the map
        return self.mineral_field.random.position

    async def on_step(self, iteration):
        CCs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
        # If no command center exists, attack-move with all workers and cyclones
        if not CCs:
            target = self.structures.random_or(self.enemy_start_locations[0]).position
            return
        else:
            # Otherwise, grab the first command center from the list of command centers
            cc: Unit = CCs.first

        # While we have less than 22 workers: build more
        # Check if we can afford them (by minerals and by supply)
        if (
                self.can_afford(UnitTypeId.SCV)
                and self.supply_workers + self.already_pending(UnitTypeId.SCV) < 22
                and cc.is_idle
        ):
            cc.train(UnitTypeId.SCV)
        """
        # Build supply depots if we are low on supply, do not construct more than 2 at a time
        elif self.supply_left < 3:
            if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 2:
                # This picks a near-random worker to build a depot at location
                # 'from command center towards game center, distance 8'
                await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))
        for scv in self.workers.idle:
            scv.gather(self.mineral_field.closest_to(cc))"""

        # Saturate gas
        for refinery in self.gas_buildings:
            if refinery.assigned_harvesters < refinery.ideal_harvesters:
                worker: Units = self.workers.closer_than(10, refinery)
                if worker:
                    worker.random.gather(refinery)

        # BUILD ORDERS
        await Build_Wall(self)
        # await BaseBuildOrder(self)


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [
            # Human(Race.Terran),
            Bot(Race.Terran, MyBot()),
            Computer(Race.Random, Difficulty.Easy),
        ],
        realtime=False,
    )


if __name__ == "__main__":
    main()
