import ai
AIClass="ExpandingBlob"
def distance(a,b):
  return (a[0]-b[0])**2+(a[1]-b[1])**2
class ExpandingBlob(ai.AI):
    area_size = 8
    def _init(self):
      self.locations      = [(x*self.area_size,y*self.area_size) for x in xrange((self.mapsize+10)/self.area_size) for y in xrange((self.mapsize+10)/self.area_size)]
      self.location_units = {}
      self.unit_locations = {}
      self.guarded        = set()

    def _spin(self):
      for unit in self.my_units:
        max_victims  = 0
        max_position = None
        for enemy in unit.visible_enemies:
          num_victims = len(unit.calcVictims(enemy.position))
          if num_victims > max_victims:
            max_victims = num_victims
            max_position = enemy.position

        if max_victims > 0:
          unit.shoot(max_position)
        elif unit in self.unit_locations and self.unit_locations[unit] != unit.position:
          unit.move(self.unit_locations[unit])
        else:
          for building in unit.visible_buildings:
            if unit.position == building.position:
              unit.capture(building)
              break

    def _unit_spawned(self, unit):
      for building in self.visible_buildings:
        if building not in self.guarded:
          self.guarded.add(building)
          rpos = building.position
          position = (int(rpos[0]/self.area_size)*self.area_size,int(rpos[1]/self.area_size)*self.area_size)
          self.unit_locations[unit] = position
          self.location_units[position] = unit
          return
      locations = set(self.locations).difference(set(self.location_units.keys()))
      min_pos  = unit.position
      min_dist = float('inf')
      for location in locations:
        dist = distance(unit.position,location)
        if dist < min_dist:
          min_dist = dist
          min_pos  = location
      self.unit_locations[unit] = min_pos
      self.location_units[min_pos] = unit

    def _unit_died(self, unit):
      del self.location_units[self.unit_locations[unit]]
      del self.unit_locations[unit]
      for building in self.guarded:
        if unit.position == building.position:
          self.guarded.remove(building)
          #TODO reposition the units to take this back
