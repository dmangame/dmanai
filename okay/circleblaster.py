
# x = cx + r * cos(a)
# y = cy + r * sin(a)
import math
import ai
AIClass="CircleBlaster"
import random
from collections import defaultdict
from world import isValidSquare

class CircleBlaster(ai.AI):
    def _init(self):
      pass

    def _spin(self):
      # Want functions to move the units as a whole.
      available_units = filter(lambda x: not x.is_capturing, self.my_units)

      cluster_size = 5
      for i in xrange(len(available_units)/cluster_size+1):
        unit_cluster = available_units[:(i+1)*cluster_size]
        available_units = available_units[(i+1)*cluster_size:]

        pos = (self.mapsize/2, self.mapsize/2)
        if self.my_buildings:
          pos = random.choice(self.my_buildings).position

        self.form_circle(unit_cluster, pos,
                        math.log(self.mapsize)*(cluster_size-1))


        for unit in unit_cluster:
          if unit.visible_enemies:
            vunit = random.choice(unit.visible_enemies)
            self.form_circle(unit_cluster, vunit.position, 3)
            break

      for unit in self.my_units:
        ire = unit.in_range_enemies
        if ire:
          unit.shoot(ire[0].position)
          continue

        vb = unit.visible_buildings
        if vb:
          b = vb[0]
          if unit.team != b.team:
            if b.position == unit.position:
              unit.capture(b)
            else:
              unit.move(b.position)




    def form_circle(self, units, (x,y), radius):
      if not units:
        return

      # So, use radians (2pi form a circle)
      radian_delta = (2*math.pi) / len(units)
      radian_offset = 0
      for unit in units:
        while True:
          radian_offset += radian_delta
          pos_x = x+(radius*math.cos(radian_offset))
          pos_y = y+(radius*math.sin(radian_offset))
          if isValidSquare((pos_x, pos_y), self.mapsize):
            break

        unit.move((pos_x, pos_y))

    def collapse_circle(self, units, (x,y)):
      # So, use radians (2pi form a circle)
      for unit in units:
        unit.move((x, y))

    def _unit_died(self, unit):
      pass

    def _unit_spawned(self, unit):
      pass
