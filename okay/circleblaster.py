
# x = cx + r * cos(a)
# y = cy + r * sin(a)
import math
import ai
AIClass="CircleBlaster"
import random
from collections import defaultdict
from world import isValidSquare

THIRTY_DEGREES=(180 / math.pi) * 30

class CircleBlaster(ai.AI):
    def _init(self):
      self.cluster_destination = None
      self.buildings = set()

    def _spin(self):
      # Want functions to move the units as a whole.
      available_units = filter(lambda x: not x.is_capturing, self.my_units)

      for building in self.visible_buildings:
        self.buildings.add(building)

      cluster_size = 5
      rotation_offset = 0
      for i in xrange(len(available_units)/cluster_size+1):
        rotation_offset += THIRTY_DEGREES
        unit_cluster = available_units[:(i+1)*cluster_size]
        available_units = available_units[(i+1)*cluster_size:]

        if self.my_buildings:
          pos = random.choice(self.my_buildings).position
        else:
          pos = random.choice(list(self.buildings)).position
          radius = 1
          self.form_circle(unit_cluster, pos, radius, rotation_offset)
          continue

        # [TODO] Plug in exploration code here
#        if len(available_units)*2 > math.sqrt(self.mapsize):
#          pos = random.randint(0, self.mapsize), random.randint(0, self.mapsize)


        radius = math.log(self.mapsize)*len(self.my_units) / 2
        self.form_circle(unit_cluster, pos, radius, rotation_offset)


        for unit in unit_cluster:
          if unit.visible_enemies:
            vunit = random.choice(unit.visible_enemies)
            self.form_circle(unit_cluster, vunit.position, 3, rotation_offset)
            break

      for unit in self.my_units:
        ire = unit.in_range_enemies
        hit = False
        for vunit in ire:
          ff = False
          hits = unit.calcVictims(vunit.position)
          for hit in hits:
            if hit.team == self.team:
              ff = True
              break

          if not ff:
            hit = True
            unit.shoot(vunit.position)
            break
        if not hit and ire:
          unit.shoot(ire[0].position)

        vb = unit.visible_buildings
        if vb:
          b = vb[0]
          if unit.team != b.team:
            if b.position == unit.position:
              unit.capture(b)
            else:
              unit.move(b.position)




    def form_circle(self, units, (x,y), radius, ro=0):
      if not units:
        return

      # So, use radians (2pi form a circle)
      radian_delta = (2*math.pi) / len(units)
      radian_offset = ro
      for unit in units:
        attempts = 0
        while True:
          radian_offset += radian_delta
          pos_x = x+(radius*math.cos(radian_offset))
          pos_y = y+(radius*math.sin(radian_offset))
          attempts += 1
          if isValidSquare((pos_x, pos_y), self.mapsize):
            break

          if attempts >= 3:
            return

        unit.move((pos_x, pos_y))

    def collapse_circle(self, units, (x,y)):
      # So, use radians (2pi form a circle)
      for unit in units:
        unit.move((x, y))

    def _unit_died(self, unit):
      pass

    def _unit_spawned(self, unit):
      pass
