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

    # {{{ Initializer
    def _init(self):
      # Exploration Data
      self.to_explore = set()
      self.explored_areas = {}
      self.under_exploration = {}

      self.destinations = {}
      self.build_grid()

      self.buildings = {}

      self.explorers = {}
      self.defenders = {}
      self.attackers = {}
    # }}}

    # {{{ Main method: called every world turn
    def _spin(self):
      self.clearHighlights()

      for b in self.visible_buildings:
        if not b in self.buildings:
          self.buildings[b] = b.position
          self._building_sighted(b)

      for area in self.to_explore:
        self.highlightRegion(area)

      for unit in self.explorers:
        self.explore(unit, self.explorers[unit])

      for unit in self.defenders:
        self.defend(unit, self.defenders[unit])

      for unit in self.attackers:
        self.attack(unit, self.attackers[unit])

      for unit in self.my_units:
        if not unit.is_capturing:
          if unit.visible_enemies:
            unit.shoot(unit.visible_enemies[0].position)
    # }}}

    # {{{ Callbacks
    def _building_sighted(self, building):
      pass

    def _unit_spawned(self, unit):

      if len(self.defenders) < len(self.my_buildings):
        defended = defaultdict(int)

        for d in self.defenders:
          defended[self.defenders[d]] += 1

        for b in self.my_buildings:
          if not b.position in defended:
            self.defenders[unit] = b.position

      else:
        self.explorers[unit] = None

    def _unit_died(self, dead_unit):
      allocations = [self.attackers, self.defenders, self.explorers, self.destinations]

      for assignment in allocations:
        if dead_unit in assignment:
          del assignment[dead_unit]

      try:
        del self.under_exploration[self.destinations[dead_unit]]
      except Exception, e:
        pass


    # }}}

    # {{{ Exploration code
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

    def explore(self, unit, position):
      pos = to_area(unit.position)

      if pos in self.to_explore:
        self.to_explore.remove(pos)

      if not unit in self.destinations or \
        unit.position == self.destinations[unit]:
        self.explored_areas[pos] = unit
        self.destinations[unit] = self.next_destination(unit)

      self.highlightLine(unit.position, self.destinations[unit])
      unit.move(self.destinations[unit])
    # }}}

    # {{{ Defense code
    def defend(self, unit, position):
      pass
    # }}}

    # {{{ Attack and capture code
    def attack(self, unit, position):
      pass
    # }}}


