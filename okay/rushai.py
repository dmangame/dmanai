
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
      self.sights = {}
      self.defenders = {}
      self.explorers = {}
      self.positions = defaultdict(set)
      self.to_visit = set()
      self.visiting = {}
      self.attack = defaultdict(bool)
      self.destinations = {}
      self.buildings = {}
      for i in xrange(self.mapsize/AREA_SIZE):
        for j in xrange(self.mapsize/AREA_SIZE):
          self.to_visit.add((i*AREA_SIZE,j*AREA_SIZE))


    def _spin(self):
      positions = [to_area(u.position) for u in self.my_units]
      self.to_visit.difference_update(positions)


      for b in self.visible_buildings:
        self.buildings[b.position] = b

      for unit in self.defenders:
        self.defend_position(unit, self.defenders[unit])

      for pos in self.positions:
        p_set = self.positions[pos]
        if len(p_set) >= 2*EXPLORER_RATIO:
          ordered_list = list(p_set)
          stay = ordered_list[:EXPLORER_RATIO]
          leave = ordered_list[EXPLORER_RATIO+1:]
          for p in self.buildings:
            if self.buildings[p] not in self.visible_buildings:
              self.surround_position(leave, p)
              for unit in leave:
                if unit in p_set:
                  p_set.remove(unit)

      for unit in self.explorers:
        if self.explorers[unit]: self.explore_position(unit)

      if not self.defenders and self.buildings:
        b = random.choice(self.buildings.values())
        for unit in self.explorers:
          self.defenders[unit] = b.position

    def _unit_spawned(self, unit):
      self.sights[unit] = unit.sight

      if self.current_turn == 1:
        self.defenders[unit] = unit.position
        return

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
      if self.to_visit:
        min_dist = 1000000
        min_pos = None
        for pos in self.to_visit:
          if pos in self.visiting:
            continue
          cur_dist = unit.calcDistance(pos)
          if cur_dist < self.mapsize / 8:
            return pos

          if min_dist > cur_dist:
            min_pos = pos
            min_dist = cur_dist

        return min_pos

      rx,ry = random.randint(0, self.mapsize), random.randint(0, self.mapsize)
      return rx,ry


    def explore_position(self, unit):
      if unit.visible_enemies:
        for e in unit.in_range_enemies:
          if e.position == unit.position or self.attack[unit]:
            unit.shoot(e.position)
            return


        for b in unit.visible_buildings:
          if not b.team == self.team:
            self.capture_building(unit, b)
            return

      if unit.visible_buildings:
        for b in unit.visible_buildings:
          if not b.team == self.team:
            self.capture_building(unit, b)
            return

      if not unit in self.destinations or\
        unit.position == self.destinations[unit]:
        if self.attack[unit]:
          min_p = 1000000
          min_b = None
          for p in self.buildings:
            if min_p > p:
              min_p = p
              min_b = b

          if min_b:
            self.capture_building(unit, min_b)
            return

        destination = self.next_destination(unit)
        if not destination:
          self.capture_building(unit, random.choice(self.buildings.values()))
          return
        self.destinations[unit] = destination
        self.visiting[destination] = unit
      unit.move(self.destinations[unit])

    def capture_building(self, unit, b):
      if not unit.position == b.position:
        unit.move(b.position)
      else:
        unit.capture(b)
        self.explorers[unit] = False
        self.attack[unit] = False
        self.defenders[unit] = b.position

    def surround_position(self, units, position):
      corners = [[-1, 1], [1, 1], [-1, -1], [1, -1]]
      corner_cycler = itertools.cycle(corners)
      for unit in units:
        x,y = fuzz_position(position, unit.sight, self.mapsize)
        unit.move((x,y))
        self.attack[unit] = True
        self.explorers[unit] = True
        self.destinations[unit] = (x,y)


    def defend_position(self, unit, position):
      b = self.buildings[position]
      if unit.is_capturing:
        return


      if b in self.visible_buildings:
        if unit.visible_enemies:
          for e in unit.visible_enemies:
            if unit.calcVictims(e.position):
              unit.shoot(e.position)
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
        unit.move(position)


    def _unit_died(self, unit):
      if unit in self.explorers:
        del self.explorers[unit]

      if unit in self.defenders:
        del self.defenders[unit]

      for pos in self.positions:
        if unit in self.positions[pos]:
          self.positions[pos].remove(unit)

