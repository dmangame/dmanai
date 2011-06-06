import ai
import random
import itertools
from operator import attrgetter
from collections import defaultdict
import logging

AIClass = "SearchAI"
log = logging.getLogger(AIClass)

GRID_RESOLUTION=32
def to_area((x,y)):
  return (x / GRID_RESOLUTION * GRID_RESOLUTION,
          y / GRID_RESOLUTION * GRID_RESOLUTION)

class SearchAI(ai.AI):
    def _init(self):
      self.to_explore = set()
      self.explored_areas = {}
      self.under_exploration = {}

      self.destinations = {}
      self.build_grid()

    def _spin(self):
      self.clearHighlights()
      for unit in self.my_units:
        pos = to_area(unit.position)
        if pos in self.to_explore:
          self.to_explore.remove(pos)

        if not unit in self.destinations or \
          unit.position == self.destinations[unit]:
          self.explored_areas[pos] = unit
          self.destinations[unit] = self.next_destination(unit)

        self.highlightLine(unit.position, self.destinations[unit])
        unit.move(self.destinations[unit])

      for area in self.to_explore:
        self.highlightRegion(area)

    def _unit_died(self, dead_unit):
      del self.under_exploration[self.destinations[unit]]

    def build_grid(self):
      for x in xrange((self.mapsize / GRID_RESOLUTION) + 1):
        for y in xrange((self.mapsize / GRID_RESOLUTION) + 1):
          self.to_explore.add((x*GRID_RESOLUTION, y*GRID_RESOLUTION))

    def next_destination(self, unit):
      global GRID_RESOLUTION
      if not self.to_explore:
        if GRID_RESOLUTION >= 2*unit.sight:
          GRID_RESOLUTION /= 2
        self.build_grid()

      dest = random.choice(list(self.to_explore))
      return dest
