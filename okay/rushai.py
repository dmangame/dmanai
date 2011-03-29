
import ai
import random
import itertools
from operator import attrgetter
from collections import defaultdict
from world import isValidSquare

AIClass = "RushAI"
EXPLORER_RATIO=3
AREA_SIZE = 8

def to_area((x,y)):
   return x/AREA_SIZE*AREA_SIZE, y/AREA_SIZE*AREA_SIZE

class RushAI(ai.AI):
    def __init__(self, *args, **kwargs):
        ai.AI.__init__(self, *args, **kwargs)

    def _init(self):
      self.defenders = {}
      self.explorers = {}
      self.positions = defaultdict(set)
      self.to_visit = set()
      self.destinations = {}
      self.buildings = {}
      for i in xrange(self.mapsize/AREA_SIZE):
        for j in xrange(self.mapsize/AREA_SIZE):
          self.to_visit.add((i*AREA_SIZE,j*AREA_SIZE))


    def _spin(self):
      visible_areas = map(to_area, map(attrgetter('position'), self.my_units))
      self.to_visit.difference(visible_areas)

#      for p in self.buildings:
#        if self.buildings[p] not in self.visible_buildings:
#          # Pick an explorer at random
#          if self.explorers:
#            e = random.choice(self.explorers.keys())
#            self.defenders[e] = p
#            self.defend_position(e, p)
#            del self.explorers[e]

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
              for unit in leave:
                self.defenders[unit] = p
                self.defend_position(unit, p)
                p_set.remove(unit)

      for unit in self.explorers:
        self.explore_position(unit)

      if not self.defenders and self.buildings:
        for unit in self.explorers:
          b = random.choice(self.buildings.values())
          self.defenders[unit] = b.position

    def _unit_spawned(self, unit):
      if self.current_turn == 1:
        self.defenders[unit] = unit.position
        return

      if len(self.explorers) < len(self.my_buildings):
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
        p = random.choice(list(self.to_visit))
        return p

      rx,ry = random.randint(0, self.mapsize), random.randint(0, self.mapsize)
      return rx,ry


    def explore_position(self, unit):
      if unit.visible_enemies:
        for e in unit.visible_enemies:
          if e.position == unit.position:
            unit.shoot(unit.position)
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
        destination = self.next_destination(unit)
        self.destinations[unit] = destination
      else:
        unit.move(self.destinations[unit])

    def capture_building(self, unit, b):
      if not unit.position == b.position:
        unit.move(b.position)
      else:
        unit.capture(b)

    def defend_position(self, unit, position):
      b = self.buildings[position]
      if unit.is_capturing:
        return


      if b in self.visible_buildings:
        if unit.visible_enemies:
          for e in unit.visible_enemies:
            ff = False
            for vunit in unit.calcVictims(e.position):
              if vunit.team == self.team:
                ff = True
                break

            if not ff:
              unit.shoot(e.position)
              return
        else:
          if unit.is_capturing:
            return
          if not b.team == self.team:
            self.capture_building(unit, b)
            return

          if unit.position == b.position:
            x,y = b.position
            sight = unit.sight - 2

            dx = int((sight - random.randint(1, 5)) * random.choice([-1, 1]))
            dy = sight - abs(dx) * random.choice([-1, 1])

            x += dx
            y += dy
            while not isValidSquare((x,y), self.mapsize):
              x,y = b.position
              dx = int((sight - random.randint(1, 5)) * random.choice([-1, 1]))
              dy = sight - abs(dx) * random.choice([-1, 1])
              x += dx
              y += dy
            unit.move((x,y))
      else:
        if unit.is_capturing:
          return
        unit.move(position)


    def _unit_died(self, unit):
      if unit in self.explorers:
        del self.explorers[unit]
      if unit in self.defenders:
        del self.defenders[unit]

      for pos in self.positions:
        if unit in self.positions[pos]:
          self.positions[pos].remove(unit)

