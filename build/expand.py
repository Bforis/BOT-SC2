import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2


async def Expand(self):
    ccs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
    if self.units(UnitTypeId.COMMANDCENTER).amount < (
            self.iteration / self.ITERATIONS_PER_MINUTE
    ):
        if (
                self.already_pending(UnitTypeId.COMMANDCENTER) == 0
        ):  # get_next_expansion returns the position of the next possible expansion location where you can place a command center
            location: Point2 = await self.get_next_expansion()
            if location:
                # Now we "select" (or choose) the nearest worker to that found location
                worker: Unit = self.select_build_worker(location)
                if worker and self.can_afford(UnitTypeId.COMMANDCENTER):
                    # The worker will be commanded to build the command center
                    worker.build(UnitTypeId.COMMANDCENTER, location)
