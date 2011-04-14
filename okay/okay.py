import ai
import unit
import ai_exceptions
from collections import defaultdict

import random
import math

from world import isValidSquare

class NearbySearcher():

  def __init__(self, mapsize):
    self.AREA_SIZE = 32
    self.to_visit = set()
    self.visiting = {}
    self.force = defaultdict(bool)
    self.destinations = {}
    self.mapsize = mapsize


  def to_area(self, (x,y),area_size=None):
    if not area_size:
      area_size = self.AREA_SIZE

    x = x/area_size*area_size
    y = y/area_size*area_size

    return min(self.mapsize,max(0, x)), min(self.mapsize,max(0, y))


  # Searcher looking for the next place to put a unit
  def assign_next_destination(self, unit, no_destination_cb=None, arrived_cb=None):


    destination = None
    if unit in self.destinations:
      if unit.position != self.destinations[unit]:
        if self.force[unit]:
          return

        if self.destinations[unit] in self.to_visit:
          return
      else:
        if arrived_cb:
          destination = arrived_cb(unit)
        self.force[unit] = False


    if not destination:
      destination = self.next_destination(unit)

    if not destination:
      if no_destination_cb:
        destination = no_destination_cb(unit)

    if destination:
      self.destinations[unit] = destination
      self.visiting[destination] = unit

    return destination

  def next_destination(self, unit):
    if len(self.to_visit) <= len(self.visiting):
      self.visiting.clear()
      self.AREA_SIZE /= 2
      for i in xrange(self.mapsize/self.AREA_SIZE):
        for j in xrange(self.mapsize/self.AREA_SIZE):
          self.to_visit.add((i*self.AREA_SIZE,j*self.AREA_SIZE))

    min_dist = 10000000000
    min_pos = None
    tries = 15
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
    self.explorers = {}

    # Histogram of where our explorers die
    self.explorer_death_positions = defaultdict(int)

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

      if unit in self.explorers:
        del self.explorers[unit]
        self.explorer_death_positions[self.searcher.to_area(unit.position)] += 1

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


# A group of units that act as one. Sort of.
class Squad(object):
  def __init__(self, *args, **kwargs):
    self.destination = kwargs.get("base", None)
    self.mapsize = kwargs.get("mapsize", None)

    self.base = self.destination
    self.guarding = None

    self.positions = ["l", "r"]

  @property
  def position_offsets(self):
    return [(-2, 0), (2, 0)]

  def __len__(self):
    l = 0
    for p in self.positions:
      if getattr(self, p):
        l += 1
    return l

  def is_moving(self, at_least=None):
    if not at_least:
      at_least = len(self)

    count = 0
    for p in self.positions:
      unit = getattr(self, p)
      if not unit:
        continue
      if unit.is_alive and unit.is_moving:
        count += 1

    return at_least <= count

  @property
  def units(self):
    units = []
    for p in self.positions:
      unit = getattr(self, p)
      if unit:
        units.append(unit)
    return units


  @property
  def sight(self):
    try:
      return sum(map(lambda x: x.sight, self.units)) / len(self)
    except:
      return 0

  def units_in_place(self):
    for i in xrange(len(self.positions)):
      p = self.positions[i]
      unit = getattr(self, p)

      if unit and not unit.is_capturing:
        pos = self.destination or self.base
        off = self.position_offsets[i]
        d_x, d_y = (pos[0] + off[0], pos[1]+off[1])
        d_x = max(min(self.mapsize, d_x), 0)
        d_y = max(min(self.mapsize, d_y), 0)

        dest = (d_x, d_y)

        if dest != unit.position:
          try:
            unit.move(dest)
          except ai_exceptions.IllegalSquareException:
            unit.move(self.destination)
          except ai_exceptions.DeadUnitException:
            print "Tried using a dead unit"
            raise
            self.remove_unit(unit)

  def add_unit(self, unit):
    for i in xrange(len(self.positions)):
      p = self.positions[i]
      if not getattr(self, p):
        setattr(self, p, unit)
        return

    attr = "u%s"%(unit.unit_id)
    self.positions.append(attr)
    setattr(self, attr, unit)


  def capture_buildings(self):
    for p in self.positions:
      unit = getattr(self, p)
      if unit:
        vb = unit.visible_buildings
        if vb:
          for b in vb:
            if b.team != unit.team:
              self.capture_building(b)
              return

  def capture_building(self, b):
    pos = b.position
    self.destination = pos
    for p in self.positions:
      unit = getattr(self, p)
      if unit:
        if unit.position == pos:
          unit.capture(b)
          return
        else:
          unit.move(pos)

  def attack_nearby_enemies(self):
    all_attack = None
    for p in self.positions:
      unit = getattr(self, p)
      if unit:
        ire = unit.in_range_enemies
        if ire:
          all_attack = ire[0]
          break

    if all_attack:
      for p in self.positions:
        unit = getattr(self, p)
        if not unit: continue

        if all_attack in unit.in_range_enemies:
          unit.shoot(all_attack.position)
        else:
          unit.move(all_attack.position)

  def remove_unit(self, unit):
    for p in self.positions:
      if getattr(self, p) == unit:
        setattr(self, p, None)
        return

    attr = "u%s"%(unit.unit_id)
    if attr in self.positions:
      self.positions.remove(attr)

  def move_to(self, position):
    self.destination = position

  def spin(self):
    self.units_in_place()
    self.capture_buildings()
    self.attack_nearby_enemies()

  def full_squad(self):
    return len(self) == len(self.positions)

  def guard(self, building, fuzzer):
    for p in self.positions:
      unit = getattr(self, p)
      if unit:
        sight = unit.sight
        if sight:
          break

    self.destination = fuzzer(building.position, sight)
    self.guarding = building
    self.base = building.position


  def calcDistance(self, end_square):
    total_dist = 0.0
    total_units = 0
    for pos in self.positions:
      unit = getattr(self, pos)
      if unit:
        total_dist = unit.calcDistance(end_square)
        total_units += 1

    if not total_units:
      return self.mapsize ** 2
    return total_dist / total_units

class V(Squad):
  def __init__(self, *args, **kwargs):
    Squad.__init__(self, *args, **kwargs)

    self.l = kwargs.get("left", None)
    self.c = kwargs.get("center", None)
    self.r = kwargs.get("right", None)
    self.positions = ["l", "c", "r"]

  @property
  def position_offsets(self):
    return [(-5,-5), (0,0), (-5,5)]


THIRTY_DEGREES=(180 / math.pi) * 30
class CircleSquad(Squad):
  def __init__(self, *args, **kwargs):
    Squad.__init__(self, *args, **kwargs)
    self.positions = []
    self.radius = 1
    self.radian_offset = 0

  def add_unit(self, unit):
    Squad.add_unit(self, unit)

  def remove_unit(self, unit):
    Squad.remove_unit(self, unit)

  def getPositionOffsets(self):
    radian_delta = (2*math.pi) / len(self.positions)
    radian_offset = self.radian_offset
    x = 0
    y = 0
    position_offsets = []
    for i in xrange(len(self.positions)):
      radian_offset += radian_delta
      pos_x = x+(self.radius*math.cos(radian_offset))
      pos_y = y+(self.radius*math.sin(radian_offset))
      position_offsets.append((int(pos_x), int(pos_y)))

    return position_offsets

  position_offsets = property(getPositionOffsets)
