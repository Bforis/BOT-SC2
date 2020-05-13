import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random, numpy as np

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units

from typing import List, Set


async def Build_Wall(self):
    ccs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
    if not ccs:
        return
    else:
        cc: Unit = ccs.first
    if self.supply_left < 3:
        if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 2:
            .

