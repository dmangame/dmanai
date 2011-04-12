import ai
import unit
from collections import defaultdict

import random
from world import isValidSquare

class NearbySearcher():

  def __init__(self, mapsize):
    self.AREA_SIZE = 32
    self.to_visit = set()
    self.visiting = {}
    self.force = defaultdict(bool)
    self.destinations = {}
    self.mapsize = mapsize


  def to_area(self, (x,y)):
     x = x/self.AREA_SIZE*self.AREA_SIZE
     y = y/self.AREA_SIZE*self.AREA_SIZE

     return min(self.mapsize,max(0, x)), min(self.mapsize,max(0, y))

  def assign_next_destination(self, unit, no_destination_cb=None, arrived_cb=None):
    if unit in self.destinations:
      if unit.position != self.destinations[unit]:
        if self.force[unit]:
          return

        if self.destinations[unit] in self.to_visit:
          return
      else:
        if arrived_cb: arrived_cb(unit)
        self.force[unit] = False


    destination = self.next_destination(unit)
    if not destination:
      if no_destination_cb:
        destination = no_destination_cb(unit)

    if destination:
      self.destinations[unit] = destination
      self.visiting[destination] = unit

  def next_destination(self, unit):
    if len(self.to_visit) <= len(self.visiting):
      self.visiting.clear()
      self.AREA_SIZE /= 2
      for i in xrange(self.mapsize/self.AREA_SIZE):
        for j in xrange(self.mapsize/self.AREA_SIZE):
          self.to_visit.add((i*self.AREA_SIZE,j*self.AREA_SIZE))

    min_dist = 10000000000
    min_pos = None
    tries = 10
    while tries > 0:
      pos = random.choice(list(self.to_visit))
      tries -= 1
      if pos in self.visiting:
        continue
      cur_dist = unit.calcDistance(pos)
      if cur_dist < self.mapsize / self.AREA_SIZE / 2:
        return pos

      if min_dist > cur_dist:
        min_pos = pos
        min_dist = cur_dist

    return min_pos

  def account_for(self, units):
    positions = [self.to_area(u.position) for u in units]
    self.to_visit.difference_update(positions)

class OkayAI(ai.AI):
  # We should have unit designations, like:
  # { explorers : 2, guarders : 3 }
  # And a weighting on which get fulfilled first, this should
  # allow for _unit_spawned to have easier unit creation.
  def init(self):
    ai.AI.init(self)
    self.buildings = {}
    self.searcher = NearbySearcher(self.mapsize)

  def turn(self, *args, **kwargs):
    for building in self.visible_buildings:
      if not building.position in self.buildings:
        self.buildings[building.position] = building
        self._building_sighted(building)

    for unit in self.dead_units:
      if unit in self.searcher.destinations:
        dest = self.searcher.destinations[unit]
        if dest in self.searcher.visiting:
          del self.searcher.visiting[dest]
        del self.searcher.destinations[unit]

    ai.AI.turn(self, *args, **kwargs)
    self.searcher.account_for(self.my_units)

  def _building_sighted(self, building):
    pass

  def fuzz_position(self, (x,y), sight):
    mapsize = self.mapsize
    dx = int((sight) * random.choice([-1, 1]))
    dy = int((sight) * random.choice([-1, 1]))

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
