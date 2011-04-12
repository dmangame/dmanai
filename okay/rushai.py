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

      self.map_reductions = 0

    def _spin(self):
      for unit in self.my_units:
        if unit in self.defenders:
          self.defend_position(unit, self.defenders[unit])

        if unit in self.explorers:
          self.explore_position(unit)

      if not self.defenders and self.buildings:
        b = random.choice(self.buildings.values())
        capturers = []
        for unit in self.explorers:
          capturers.append(unit)
        for unit in capturers:
          self.capture_building(unit, b)

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

      if not explorer:
        if self.buildings:
          min_dist = 10000
          min_pos = None
          for pos in self.buildings:
            dist = unit.calcDistance(pos)
            if dist < min_dist:
              min_dist = dist
              min_pos = pos

          if not min_pos:
            b = random.choice(self.buildings.values())
          else:
            b = self.buildings[min_pos]
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
        if not b.team == self.team:
          self.capture_building(unit, b)
          return

      def no_dest(unit):
        if unit in self.capturers:
          destination = self.capturers[unit]
          self.searcher.force[unit] = True
          del self.capturers[unit]
          del self.explorers[unit]
          self.defend_position(unit, destination)
          self.defenders[unit] = destination
          return destination
        else:
          b = random.choice(self.buildings.values())
          self.capture_building(unit, b)
          self.aggressive[unit] = True
          self.searcher.force[unit] = True
          return b.position


      self.searcher.assign_next_destination(unit, arrived_cb=no_dest, no_destination_cb=no_dest)

      unit.move(self.searcher.destinations[unit])

    def capture_building(self, unit, b):
      if not unit.position == b.position:
        self.searcher.destinations[unit] = b.position
      else:
        unit.capture(b)
        if unit in self.explorers: del self.explorers[unit]
        self.aggressive[unit] = False
        self.defenders[unit] = b.position
        self.positions[b.position].add(unit)

    def capture_position(self, units, position):
      for unit in units:
        x,y = self.fuzz_position(position, unit.sight*2)
        self.aggressive[unit] = True
        self.explorers[unit] = True
        self.searcher.force[unit] = True
        self.searcher.destinations[unit] = (x,y)
        self.capturers[unit] = position
        self.capture_attempts[(x,y)] += 1
        unit.move((x,y))

    def surround_position(self, units, position):
      for unit in units:
        x,y = self.fuzz_position(position, unit.sight*2)
        self.aggressive[unit] = True
        self.defenders[unit] = position
        self.searcher.force[unit] = True
        self.searcher.destinations[unit] = (x,y)


    def defend_position(self, unit, position):
      if unit.is_capturing:
        return


      b = self.buildings[position]
      if b in self.visible_buildings:
        ve = unit.in_range_enemies
        if ve:
          unit.shoot(ve[0].position)
          return

        else:
          if not b.team == self.team:
            self.capture_building(unit, b)
            return

          if unit.position == b.position or \
             unit.calcDistance(b.position) > unit.sight:
            x,y = b.position
            sight = self.sights[unit] - 2

            x,y = self.fuzz_position((x,y), sight)
            unit.move((x,y))
      else:
        ve = unit.in_range_enemies
        if ve:
          unit.shoot(ve[0].position)
        else:
          unit.move(position)


    def _unit_died(self, unit):
      if unit in self.capturers:
        del self.capturers[unit]

      if unit in self.defenders:
        del self.defenders[unit]

      for pos in self.positions:
        if unit in self.positions[pos]:
          self.positions[pos].remove(unit)

