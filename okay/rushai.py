
import ai
import random
import itertools
from operator import attrgetter
from collections import defaultdict
from world import isValidSquare

AIClass = "RushAI"
EXPLORER_RATIO=4
AREA_SIZE = 8

def fuzz_position((x, y), sight, mapsize):
  dx = int((sight - random.randint(0, 3)) * random.choice([-1, 1]))
  dy = int((sight - random.randint(0, 3)) * random.choice([-1, 1]))

  ox,oy = x,y
  x += dx
  y += dy
  attempts = 30
  while not isValidSquare((x,y), mapsize) and attempts > 0:
    x,y = ox,oy
    dx = int((sight - random.randint(0, 3)) * random.choice([-1, 1]))
    dy = abs(sight - abs(dx)) * random.choice([-1, 1])
    x += dx
    y += dy
    attempts -= 1
  return x,y

  return int(x),int(y)
def to_area((x,y)):
   return x/AREA_SIZE*AREA_SIZE, y/AREA_SIZE*AREA_SIZE

class RushAI(ai.AI):
    def _init(self):
      AREA_SIZE = self.mapsize / 12

      self.buildings = {}
      self.defenders = {}
      self.destinations = {}
      self.explorers = {}
      self.sights = {}
      self.to_visit = set()
      self.visiting = {}

      self.explorer_death_positions = defaultdict(int)
      self.aggressive = defaultdict(bool)
      self.positions = defaultdict(set)

      for i in xrange(self.mapsize/AREA_SIZE):
        for j in xrange(self.mapsize/AREA_SIZE):
          self.to_visit.add((i*AREA_SIZE,j*AREA_SIZE))


    def _spin(self):
      positions = [to_area(u.position) for u in self.my_units]
      self.to_visit.difference_update(positions)

      for b in self.visible_buildings:
        self.buildings[b.position] = b

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
          cut_idx = int(10.0 / 16.0 * len(ordered_list))
          stay = ordered_list[:cut_idx]
          leave = ordered_list[cut_idx:]
          for p in self.buildings:
            if self.buildings[p] not in self.visible_buildings:
              self.surround_position(leave, p)
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
            if most_deaths < deaths:
              most_deaths = deaths
              most_pos = dead_point

          if most_pos:
            del self.explorer_death_positions[most_pos]
            for unit in leave:
              self.capture_position(leave, most_pos)

    def _unit_spawned(self, unit):
      self.sights[unit] = unit.sight

      if not self.explorers:
        self.explorers[unit] = True
      if len(self.explorers) < len(self.my_buildings) or len(self.defenders) / len(self.explorers) > EXPLORER_RATIO :
        self.explorers[unit] = True
      else:
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

    def next_destination(self, unit):
      global AREA_SIZE
      if len(self.to_visit) < len(self.visiting):
        self.visiting.clear()
        AREA_SIZE /= 2
        for i in xrange(self.mapsize/AREA_SIZE):
          for j in xrange(self.mapsize/AREA_SIZE):
            self.to_visit.add((i*AREA_SIZE,j*AREA_SIZE))

      min_dist = 10000000000
      min_pos = None
      for pos in self.to_visit:
        if pos in self.visiting:
          continue
        cur_dist = unit.calcDistance(pos)
        if cur_dist < self.mapsize / AREA_SIZE:
          return pos

        if min_dist > cur_dist:
          min_pos = pos
          min_dist = cur_dist

      return min_pos

    def explore_position(self, unit):

      # If we see any visible enemies and there is more than one or we are
      # aggressive, attack them.
      ve = unit.in_range_enemies
      for e in ve:
        if e.position == unit.position or self.aggressive[unit] or len(ve) > 1:
          unit.shoot(e.position)
          return


      for b in unit.visible_buildings:
        if not b.team == self.team:
          self.capture_building(unit, b)
          return

      if not unit in self.destinations or\
        unit.position == self.destinations[unit]:

        destination = self.next_destination(unit)
        if not destination:
          self.capture_building(unit,
            random.choice(self.buildings.values()))
          self.aggressive[unit] = True
          return
        else:
          self.destinations[unit] = destination
          self.visiting[destination] = unit

      unit.move(self.destinations[unit])

    def capture_building(self, unit, b):
      if not unit.position == b.position:
        unit.move(b.position)
      else:
        unit.capture(b)
        if unit in self.explorers: del self.explorers[unit]
        self.aggressive[unit] = False
        self.defenders[unit] = b.position
        self.positions[b.position].add(unit)

    def capture_position(self, units, position):
      for unit in units:
        x,y = fuzz_position(position, unit.sight, self.mapsize)
        unit.move((x,y))
        self.aggressive[unit] = True
        self.explorers[unit] = True
        self.destinations[unit] = (x,y)

    def surround_position(self, units, position):
      for unit in units:
        x,y = fuzz_position(position, unit.sight, self.mapsize)
        unit.move((x,y))
        self.aggressive[unit] = True
        self.defenders[unit] = position
        self.destinations[unit] = (x,y)


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

            x,y = fuzz_position((x,y), sight, self.mapsize)
            unit.move((x,y))
      else:
        ve = unit.in_range_enemies
        if ve:
          unit.shoot(ve[0].position)
        else:
          unit.move(position)


    def _unit_died(self, unit):
      if unit in self.explorers:
        del self.explorers[unit]
        self.explorer_death_positions[unit.position] += 1

      if unit in self.defenders:
        del self.defenders[unit]

      if unit in self.destinations:
        dest = self.destinations[unit]
        if dest in self.visiting:
          del self.visiting[dest]

      for pos in self.positions:
        if unit in self.positions[pos]:
          self.positions[pos].remove(unit)

