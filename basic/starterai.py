import ai
import random
import itertools
from operator import attrgetter
from collections import defaultdict
import logging

AIClass = "StarterAI"
log = logging.getLogger(AIClass)

GRID_RESOLUTION=32
def to_area((x,y)):
  return (x / GRID_RESOLUTION * GRID_RESOLUTION,
          y / GRID_RESOLUTION * GRID_RESOLUTION)


class BaseStrategy(object):
  def __init__(self, ai):
    self.units = {}
    self.ai = ai

  def _allocate(self, unit):
    # Basically, if it gets the unit, return True, otherwise, it is indicating
    # it didn't take the unit
    pass

  def _execute(self):
    pass

  def _deallocate(self, dead_unit):
    try:
      del self.units[dead_unit]
    except:
      pass

class DefendStrategy(BaseStrategy):
  def __init__(self, ai):
    self.defenders = self.units = {}
    self.ai = ai

  def _allocate(self, unit):
    if len(self.defenders) < len(self.ai.my_buildings):
      defended = defaultdict(int)

      for d in self.defenders:
        defended[self.defenders[d]] += 1

      for b in self.ai.my_buildings:
        if not b.position in defended:
          self.defenders[unit] = b.position
          return True

class AttackStrategy(BaseStrategy):
  # No attack strategy, at the moment.
  pass

# {{{ Exploration code
class ExploreStrategy(BaseStrategy):
  def __init__(self, ai):
    # Exploration Data
    self.explorers = self.units = {}
    self.to_explore = set()
    self.explored_areas = {}
    self.under_exploration = {}
    self.ai = ai

    self.destinations = {}
    self.build_grid()

  def _allocate(self, unit):
    self.explorers[unit] = unit
    return True

  def _execute(self):
      for area in self.to_explore:
        self.ai.highlightRegion(area)

      for unit in self.explorers:
        self.explore(unit, self.explorers[unit])


  def _deallocate(self, unit):
      try:
        del self.explorers[unit]
      except Exception, e:
        pass

      try:
        del self.under_exploration[self.destinations[dead_unit]]
      except Exception, e:
        pass

  def build_grid(self):
    for x in xrange((self.ai.mapsize / GRID_RESOLUTION) + 1):
      for y in xrange((self.ai.mapsize / GRID_RESOLUTION) + 1):
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

    self.ai.highlightLine(unit.position, self.destinations[unit])
    unit.move(self.destinations[unit])
# }}}

class StarterAI(ai.AI):

    # {{{ Initializer
    def _init(self):
      self.buildings = {}
      self.strategies = [
         AttackStrategy(self),
         ExploreStrategy(self),
         DefendStrategy(self)
        ]

    # }}}

    # {{{ Main method: called every world turn
    def _spin(self):
      self.clearHighlights()

      for b in self.visible_buildings:
        if not b in self.buildings:
          self.buildings[b] = b.position
          self._building_sighted(b)

      for strategy in self.strategies:
        strategy._execute()

      # Last ditch attack
      for unit in self.my_units:
        if not unit.is_capturing:
          if unit.visible_enemies:
            unit.shoot(unit.visible_enemies[0].position)
    # }}}

    # {{{ Callbacks
    def _building_sighted(self, building):
      pass

    def _unit_spawned(self, unit):
      for strategy in reversed(self.strategies):
        if strategy._allocate(unit):
          break

        log.info("Unclaimed unit")

    def _unit_died(self, dead_unit):
      for strategy in self.strategies:
        strategy._deallocate(dead_unit)
    # }}}



