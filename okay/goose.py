import ai
AIClass="GooseAI"
import random
import ai_exceptions
import logging
from collections import defaultdict
log = logging.getLogger(AIClass)

AREA_SIZE = 16
class V:
  def __init__(self, left=None, center=None, right=None, base=None):
    self.l = left
    self.c = center
    self.r = right
    self.base = base
    self.positions = ["l", "c", "r"]
    self.position_offsets = [(-5,-5), (0,0), (-5,5)]
    self.destination = base
    self.guarding = None

  def __len__(self):
    l = 0
    for p in self.positions:
      if getattr(self, p):
        l += 1
    return l

  @property
  def is_moving(self, at_least=1):
    count = 0
    for p in self.positions:
      unit = getattr(self, p)
      if not unit:
        continue
      if unit.is_alive and unit.is_moving:
        count += 1

    return at_least <= count

  def units_in_place(self):
    for i in xrange(len(self.positions)):
      p = self.positions[i]
      unit = getattr(self, p)
      if unit and not unit.is_capturing:
        pos = self.destination
        off = self.position_offsets[i]
        dest = (pos[0] + off[0], pos[1]+off[1])
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



    raise Exception("Assigning unit to a full squadron")


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

  def move_to(self, position):
    self.destination = position

  def spin(self):
    if len(self) < 3:
      self.destination = self.base

    self.units_in_place()
    self.capture_buildings()
    self.attack_nearby_enemies()

  def full_squad(self):
    return len(self) == len(self.positions)

  def guard(self, building):
    self.destination = building.position
    self.guarding = building
    self.base = building.position

def to_area_square((x,y)):
  return (x/AREA_SIZE*AREA_SIZE, y/AREA_SIZE*AREA_SIZE)

class GooseAI(ai.AI):
  def _init(self):
    self.squads = []
    self.buildings = set()
    self.to_visit = []


  def generate_to_visit(self):
    areas = self.mapsize / AREA_SIZE
    for x in xrange(areas):
      for y in xrange(areas):
        self.to_visit.append((x*AREA_SIZE,y*AREA_SIZE))

  def _unit_spawned(self, unit):
    for s in self.squads:
      if len(s) < 3:
        s.add_unit(unit)
        return

    self.squads.append(V(left=unit, base=unit.position))

  def _unit_died(self, unit):
    to_remove = []
    for s in self.squads:
      s.remove_unit(unit)
      if len(s) == 0:
        to_remove.append(s)

    for s in to_remove:
      self.squads.remove(s)


  def _spin(self):
    self.buildings.update(set(self.visible_buildings))
    my_buildings = set(self.my_buildings)
    i = 0
    if not self.squads:
      return

    guarding = []
    buildings_covered = defaultdict(bool)
    for s in self.squads:
      if s.guarding:
        buildings_covered[s] = s.guarding
        guarding.append(s)

    for b in self.my_buildings:
      if i >= len(self.squads):
        break
      if not buildings_covered[b]:
        s = self.squads[i]
        s.guard(b)
        i+=1


    for b in self.buildings.difference(my_buildings):
      if i >= len(self.squads):
        break
      s = self.squads[i]
      if s.full_squad:
        self.squads[i].capture_building(b)
        i += 1
      else:
        break

    # Leave one unit at the base
    for s in self.squads[i:]:
      if not s.is_moving:
        # Go visit a new position
        old_pos = to_area_square(s.destination)
        if old_pos in self.to_visit:
          self.to_visit.remove(old_pos)

        if not self.to_visit:
          global AREA_SIZE
          AREA_SIZE /= 2
          self.generate_to_visit()
        dest = random.choice(self.to_visit)

        s.move_to(dest)

    for s in self.squads:
      s.spin()

