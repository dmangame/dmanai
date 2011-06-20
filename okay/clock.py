import ai
import random
import itertools
import math
from operator import attrgetter
from collections import defaultdict

require_dependency(module_name="okay")
AIClass = "ClockAI"

RADIAN_FACTOR=0.0174532925
class ClockAI(ai.AI):
  PLAY_IN_LADDER=True
  def _init(self):
    self.buildings = {}
    self.building_map = {}
    self.clocks = defaultdict(lambda: okay.LineSquad(mapsize=self.mapsize))
    self.spawn_point = None

  def _spin(self):
    for b in self.visible_buildings:
      if not b in self.buildings:
        self.buildings[b] = b.position
        self.building_map[b.position] = b

    for position, clock in self.clocks.iteritems():
      clock.destination = position
      size = float(len(clock)*settings.unit.sight)
      theta = math.acos(
        (size**2 + size**2 - settings.unit.speed) \
        / (2*size*size))
      clock.radian_offset += theta
      clock.spin()

  def _unit_spawned(self, unit):
    self.clocks[unit.position].add_unit(unit)

  def _unit_died(self, unit):
    for clock in self.clocks.values():
      clock.remove_unit(unit)
      clock.reform()

