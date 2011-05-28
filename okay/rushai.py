import ai
import random
import itertools
from operator import attrgetter
from collections import defaultdict
import sys
import os

require_dependency(module_name="okay")

AIClass = "RushAI"
EXPLORER_RATIO=4

class RushAI(okay.OkayAI):
    PLAY_IN_LADDER=True
    def _init(self):
      self.capturers = {}
      self.defenders = {}
      self.sights = {}
      self.capture_attempts = defaultdict(int)

      self.aggressive = defaultdict(bool)
      self.positions = defaultdict(set)
      self.surrounding = defaultdict(lambda: 10)


    def _spin(self):
      # Send each unit to do its task
      for unit in self.my_units:
        if unit.is_capturing:
          continue

        if unit in self.defenders:
          self.defend_position(unit, self.defenders[unit])

        if unit in self.explorers:
          self.explore_position(unit)

        if unit in self.capturers:
          self.capture_position(unit, self.capturers[unit])

      self.go_on_offensive()
      self.setup_defense()

      # Follow up with units to follow most overriding orders.  Capture
      # buildings, then shoot any nearby enemies
      for unit in self.my_units:
        for b in unit.visible_buildings:
          self.capture_building(unit, b)

        # If we see any visible enemies and there is more than one or we are
        # aggressive, attack them.
        ve = unit.in_range_enemies
        for e in ve:
          if self.aggressive[unit] or len(ve) > 1:
            unit.shoot(e.position)
            break
          elif unit in self.capturers or unit in self.defenders:
            unit.shoot(e.position)
            break



    def _unit_spawned(self, unit):
      self.sights[unit] = unit.sight

      explorer = False
      if len(self.explorers) < len(self.my_buildings):
        explorer = True

      if self.explorers and len(self.defenders) / len(self.explorers) > EXPLORER_RATIO:
        explorer = True

      if len(self.buildings) > len(self.my_buildings):
        explorer = False

      if explorer:
        self.explorers[unit] = True

      if not explorer:
        self.make_defender(unit)

    def _unit_died(self, unit):
      self.highlightRegion(unit.position)
      if unit in self.capturers:
        del self.capturers[unit]

      if unit in self.defenders:
        del self.defenders[unit]

      for pos in self.positions:
        if unit in self.positions[pos]:
          self.positions[pos].remove(unit)

    def make_capturer(self, unit, position):
      self.highlightLine(unit.position, position)
      x,y = self.fuzz_position(position, unit.sight*4)
      self.searcher.force[unit] = True
      self.searcher.destinations[unit] = (x,y)
      self.capturers[unit] = position
#      self.capture_attempts[position] += 1

    def make_defender(self, unit, building=None):
      if not building:
        min_pos = None
        min_units = 100000
        for pos in self.my_buildings:
          defense = self.positions[pos]
          num_units = len(defense)
          if num_units < min_units and num_units > 5:
            min_units = num_units
            min_pos = pos

        if not min_pos:
          building = random.choice(self.my_buildings)
        else:
          building = self.my_buildings[min_pos]

      if unit in self.capturers:
        del self.capturers[unit]

      if unit in self.explorers:
        del self.explorers[unit]

      self.defenders[unit] = building.position
      self.positions[building.position].add(unit)

    # Makes sure bases are covered
    def setup_defense(self):
      defending = {}
      for building in self.my_buildings:
        pos = building.position

        if not len(self.positions[pos]) > 5:
          unit_distances = []
          for u in self.my_units:
            if len(self.explorers) < 2 and u in self.explorers:
              continue

            if not u in defending:
              unit_distances.append((u.calcDistance(pos), u))

          unit_distances.sort()

          for dist, u in unit_distances[:5]:
            defending[u] = True
            self.make_defender(u, building)
            self.defend_position(u, pos)

    def go_on_offensive(self):
      # If we have enough units at a base, send them on the
      # offensive
      available_offense = []
      for pos in self.positions:
        p_set = self.positions[pos]
        if len(p_set) >= 2*EXPLORER_RATIO:
          ordered_list = list(p_set)
          cut_idx = int(0.5 * len(ordered_list))
          stay = ordered_list[:cut_idx]
          leave = ordered_list[cut_idx:]
          available_offense.extend(leave)


      for p in self.buildings:
        if self.buildings[p] not in self.visible_buildings:
          building_deaths = self.capture_attempts[p]

          if len(available_offense) <= building_deaths:
            continue

          self.capture_attempts[p] += 1
          map(lambda u: self.make_capturer(u, p), available_offense)

          for unit in available_offense:
            for p_set in self.positions.values():
              if unit in p_set:
                p_set.remove(unit)
          break



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

      if most_pos and len(available_offense) > most_deaths:
        del self.explorer_death_positions[most_pos]
        for unit in available_offense:
          self.make_capturer(unit, most_pos)

    def capture_position(self, unit, position):
      self.defend_position(unit, position)

      if unit.calcDistance(position) <= self.sights[unit]:
        self.surrounding[unit] -= 1
        if self.surrounding[unit] <= 0:
          self.aggressive[unit] = True
          self.explorers[unit] = True
          del self.surrounding[unit]
          del self.capturers[unit]

    def defend_position(self, unit, position):
      x,y = position
      sight = self.sights[unit]
      x,y = self.fuzz_position((x,y), sight)
      unit.move((x,y))

    def explore_position(self, unit):
      def no_dest(unit):
        if unit in self.capturers:
          destination = self.capturers[unit]
          self.searcher.force[unit] = True
          del self.capturers[unit]
          del self.explorers[unit]
          return destination
        else:
          b = random.choice(self.buildings.values())
          self.defend_position(unit, b.position)
          self.aggressive[unit] = True
          return b.position

      self.searcher.assign_next_destination(unit, arrived_cb=no_dest, no_destination_cb=no_dest)
      unit.move(self.searcher.destinations[unit])

    def capture_building(self, unit, b):
      if b.team == self.team or unit.is_capturing:
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

