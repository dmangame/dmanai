import ai
import random
import itertools
from operator import attrgetter
from collections import defaultdict

require_dependency(module_name="okay")
AIClass = "ClockAI"

class ClockAI(ai.AI):
  PLAY_IN_LADDER=True
  def _init(self):
    self.clock = okay.LineSquad(mapsize=self.mapsize)

  def _spin(self):
    self.clock.destination = self.my_buildings[0].position
    self.clock.radian_offset += 0.05
    self.clock.spin()

  def _unit_spawned(self, unit):
    self.clock.add_unit(unit)

  def _unit_died(self, unit):
    self.clock.remove_unit(unit)
