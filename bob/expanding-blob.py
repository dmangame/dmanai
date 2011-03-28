import ai
import copy
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
        elif unit in self.unit_locations and self.unit_locations[unit] != unit.position and self.unit_locations[unit] is not None:
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
          print unit,'is holding',building
          #rpos = building.position
          #position = (int(rpos[0]/self.area_size)*self.area_size,int(rpos[1]/self.area_size)*self.area_size)
          self.unit_locations[unit] = building.position
          self.location_units[building.position] = unit
          return
      locations = set(self.locations).difference(set(self.location_units.keys()))
      min_pos  = unit.position
      min_dist = float('inf')
      for building in self.visible_buildings:
        for location in locations:
          dist = distance(building.position,location)
          if dist < min_dist:
            min_dist = dist
            min_pos  = location
      self.unit_locations[unit] = min_pos
      self.location_units[min_pos] = unit

    def _unit_died(self, unit):
      del self.location_units[self.unit_locations[unit]]
      del self.unit_locations[unit]
      guarded_copy = copy.copy(self.guarded)
      for building in guarded_copy:
        if unit.position == building.position:
          print 'we lost a guard!!'
          self.guarded.remove(building)
          min_dist = float('inf')
          min_unit = None
          for xunit in self.my_units:
            dist = distance(xunit.position,building.position) #TODO make sure this one isn't guarding something else
            if xunit != unit and xunit.is_alive and dist < min_dist:
              min_unit = xunit
              min_dist = dist
          if min_unit is not None:
            self.guarded.add(building)
            location = self.unit_locations[min_unit]
            del self.location_units[location]
            self.unit_locations[min_unit] = building.position
            self.location_units[building.position] = min_unit
            print 'moving',min_unit,'to become a guard of',building.position
