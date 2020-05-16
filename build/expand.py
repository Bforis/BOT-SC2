import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2


async def Expand(self):
    self.ITERATIONS_PER_MINUTE = 165
    ccs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
    # Expand if we can afford (400 minerals) and have less than 2 bases
    if (
            1 <= self.townhalls.amount < 2
            and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
            and self.can_afford(UnitTypeId.COMMANDCENTER)
    ):
        # get_next_expansion returns the position of the next possible expansion location where you can place a command center
        location: Point2 = await self.get_next_expansion()
        if location:
            # Now we "select" (or choose) the nearest worker to that found location
            worker: Unit = self.select_build_worker(location)
            if worker and self.can_afford(UnitTypeId.COMMANDCENTER):
                # The worker will be commanded to build the command center
                worker.build(UnitTypeId.COMMANDCENTER, location)
