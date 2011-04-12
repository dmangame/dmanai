
# x = cx + r * cos(a)
# y = cy + r * sin(a)
import math
import ai
AIClass="CircleBlaster"
import random
from collections import defaultdict
from world import isValidSquare
import sys
import os
sys.path.append(os.path.dirname(__file__))
import okay

THIRTY_DEGREES=(180 / math.pi) * 30

class CircleBlaster(okay.OkayAI):
    def _init(self):
      self.cluster_size = 5
      self.expansion_phase = 0

    def _spin(self):
      # Want functions to move the units as a whole.
      available_units = filter(lambda x: not x.is_capturing, self.my_units)


      for building in self.visible_buildings:
        self.buildings[building.position] = building

      rotation_offset = 0


      main_circle_size = len(available_units)


      radius_m = 1
      if self.expansion_phase:
        self.expansion_phase -= 1
        radius_m = random.randint(5, 15)
      else:
        if len(self.my_units) > 10 and random.random() > 0.95:
          self.expansion_phase = random.randint(5, 10)

      if self.explorers:
        is_moving = False
        for unit in self.explorers:
          if unit.is_moving:
            is_moving = True
            break

        if not is_moving:
          unit = self.explorers.keys()[0]
          self.searcher.assign_next_destination(unit)

          self.form_circle(self.explorers, self.searcher.destinations[unit], main_circle_size)

        for cunit in self.explorers:
          available_units.remove(cunit)


      for i in xrange(len(available_units)/self.cluster_size+2):
        rotation_offset += THIRTY_DEGREES
        unit_cluster = available_units[:(i+1)*self.cluster_size]
        available_units = available_units[(i+1)*self.cluster_size:]

        radius = math.log(self.mapsize)*main_circle_size / 2
        pos = random.choice(self.buildings.keys())
        if not self.my_buildings:
          radius = 1

        for unit in unit_cluster:
          if unit.visible_enemies:
            vunit = random.choice(unit.visible_enemies)
            self.form_circle(unit_cluster, vunit.position, 3, rotation_offset)
            break

        # Radius = 1/2 diameter
        try:
          x_pos = random.randint(0, main_circle_size/2)*unit_cluster[0].sight
          y_pos = (main_circle_size/2) - x_pos

          x_pos *= random.choice([-1, 1, 0.5, -0.5])
          y_pos *= random.choice([-1, 1, 0.5, -0.5])
          pos  = (x_pos+pos[0],y_pos+pos[1])
        except:
          pass

        self.form_circle(unit_cluster, pos, radius*radius_m, rotation_offset)

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

    def _unit_spawned(self, unit):
      if not self.explorers or len(self.my_units) / len(self.explorers) >= self.cluster_size:
        self.explorers[unit] = True
        self.form_circle(self.explorers, unit.position, 5)
