import ai
import random
import itertools
from operator import attrgetter
from collections import defaultdict
import sys
import os
sys.path.append(os.path.dirname(__file__))
import okay

AIClass = "RushAI"
EXPLORER_RATIO=4
AREA_SIZE = 8

class RushAI(okay.OkayAI):
    def _init(self):
      AREA_SIZE = self.mapsize / 12

      self.capturers = {}
      self.defenders = {}
      self.sights = {}
      self.capture_attempts = defaultdict(int)

      self.aggressive = defaultdict(bool)
      self.positions = defaultdict(set)
      self.surrounding = defaultdict(lambda: 10)

      self.map_reductions = 0

    def _spin(self):
      for unit in self.my_units:
        if unit in self.defenders:
          self.defend_position(unit, self.defenders[unit])

        if unit in self.explorers:
          self.explore_position(unit)

        if unit in self.capturers:
          self.surround_position(unit, self.capturers[unit])


      if not self.defenders and self.buildings:
        b = random.choice(self.buildings.values())
        capturers = []
        for unit in self.explorers:
          capturers.append(unit)

      # If we have enough units at a base, send them on the
      # offensive
      for pos in self.positions:
        p_set = self.positions[pos]
        if len(p_set) >= 2*EXPLORER_RATIO:
          ordered_list = list(p_set)
          cut_idx = int(0.5 * len(ordered_list))
          stay = ordered_list[:cut_idx]
          leave = ordered_list[cut_idx:]
          for p in self.buildings:
            if self.buildings[p] not in self.visible_buildings:
              self.capture_position(leave, p)
              for unit in leave:
                if unit in p_set:
                  p_set.remove(unit)
              return

          # If we don't look for a building, how about we send
          # a bunch of guys to a place where the most of our
          # explorers have died.
          most_deaths = 0
          most_pos = None
          for dead_point in self.explorer_death_positions:
            deaths = self.explorer_death_positions[dead_point]
            if most_deaths <= deaths:
              most_deaths = deaths
              most_pos = dead_point

          if most_pos and len(leave) > most_deaths:
            del self.explorer_death_positions[most_pos]
            self.capture_position(leave, most_pos)

    def _unit_spawned(self, unit):
      self.sights[unit] = unit.sight

      explorer = False
      if len(self.explorers) < len(self.my_buildings):
        explorer = True

      if self.explorers and len(self.defenders) / len(self.explorers) > EXPLORER_RATIO:
        explorer = True

      if len(self.buildings) > len(self.my_buildings):
        explorer = False

      if self.map_reductions > 1:
        explorer = False

      if explorer:
        self.explorers[unit] = True

      # Assign to base with least number of units.
      if not explorer:
        if self.my_buildings:
          min_pos = None
          min_units = 100000
          for pos in self.my_buildings:
            defense = self.positions[pos]
            num_units = len(defense)
            if num_units < min_units and num_units > 5:
              min_units = num_units
              min_pos = pos

          if not min_pos:
            b = random.choice(self.my_buildings)
          else:
            b = self.my_buildings[min_pos]

          self.defenders[unit] = b.position
          self.positions[b.position].add(unit)

    def explore_position(self, unit):

      # If we see any visible enemies and there is more than one or we are
      # aggressive, attack them.
      ve = unit.in_range_enemies
      for e in ve:
        if self.aggressive[unit] or len(ve) > 1:
          unit.shoot(e.position)
          return

      for b in unit.visible_buildings:
        self.capture_building(unit, b)

      def no_dest(unit):
        if unit in self.capturers:
          destination = self.capturers[unit]
          self.searcher.force[unit] = True
          del self.capturers[unit]
          del self.explorers[unit]
          return destination
        else:
          b = random.choice(self.buildings.values())
          self.surround_position(unit, b.position)
          self.aggressive[unit] = True
          self.searcher.force[unit] = True
          return b.position


      self.searcher.assign_next_destination(unit, arrived_cb=no_dest, no_destination_cb=no_dest)

      unit.move(self.searcher.destinations[unit])

    def capture_building(self, unit, b):
      if b.team == self.team:
        return

      if not unit.position == b.position:
        self.searcher.destinations[unit] = b.position
        self.searcher.force[unit] = True
        unit.move(b.position)
      else:
        unit.capture(b)
        if unit in self.explorers: del self.explorers[unit]
        self.aggressive[unit] = False
        self.defenders[unit] = b.position
        self.positions[b.position].add(unit)

    def capture_position(self, units, position):
      for unit in units:
        x,y = self.fuzz_position(position, unit.sight*4)
        self.aggressive[unit] = True
        self.explorers[unit] = True
        self.searcher.force[unit] = True
        self.searcher.destinations[unit] = (x,y)
        self.capturers[unit] = position
        self.capture_attempts[(x,y)] += 1
        unit.move((x,y))

    def surround_position(self, unit, position, attempts=3):
      if unit.is_capturing:
        return


      ve = unit.in_range_enemies
      if ve:
        unit.shoot(ve[0].position)
        return

      x,y = position
      sight = self.sights[unit]
      x,y = self.fuzz_position((x,y), sight)
      unit.move((x,y))

      bs = unit.visible_buildings
      for b in bs:
        self.capture_building(unit, b)

      if unit.calcDistance(position) <= unit.sight:
        self.surrounding[unit] -= 1
        if self.surrounding[unit] <= 0:
          del self.surrounding[unit]
          del self.capturers[unit]


    # Defendingis:
    # Attacking
    # Capturing
    # Moving
    # In the order.
    def defend_position(self, unit, position):
      if unit.is_capturing:
        return

      ve = unit.in_range_enemies
      if ve:
        unit.shoot(ve[0].position)
        return

      x,y = position
      sight = self.sights[unit]
      x,y = self.fuzz_position((x,y), sight)
      unit.move((x,y))

      bs = unit.visible_buildings
      for b in bs:
        self.capture_building(unit, b)


    def _unit_died(self, unit):
      if unit in self.capturers:
        del self.capturers[unit]

      if unit in self.defenders:
        del self.defenders[unit]

      for pos in self.positions:
        if unit in self.positions[pos]:
          self.positions[pos].remove(unit)

