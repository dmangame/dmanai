import random
import ai
import math
from collections import defaultdict
import itertools
from world import isValidSquare

AIClass="Wedge"

def calc_distance(a, b):
  x1,y1 = a[0], a[1]
  x2,y2 = b[0], b[1]
  return ( abs(x1 - x2) + abs(y1 - y2) )

class BuildingInfo(object):
    def __init__(self, ai, b):      
      self.ai = ai
      self.building = b
      
      # Each building has 1 defender, he patrols the perimeter and alerts when threatened
      self.defender = None
      
      # Number of friends and enemies in the area
      self.friends = 0
      self.enemies = 0
      
      # Perimeter coordinates
      self.perimeter_distance = 10
      self.perimeter = []
      self.perimeter_cycler = itertools.cycle(self.perimeter)
      
      # Capture variables
      self.capturing = False        # Do we have a unit capturing this building?
      self.attempt_capture = False  # Should we attempt to capture this building?
      
    def establish_perimeter(self, distance):
      self.perimeter_distance = distance
      self.perimeter = [] 
      
      # center
      cx = self.building.position[0]
      cy = self.building.position[1]
      
      # upper left
      x = cx - distance
      y = cy - distance
      while not isValidSquare( (x,y), self.ai.mapsize ):
        x += 1
        y += 1
      self.perimeter.append( (x, y) )
      
      # upper right
      x = cx + distance
      y = cy - distance
      while not isValidSquare( (x,y), self.ai.mapsize ):
        x -= 1
        y += 1
      self.perimeter.append( (x, y) )
      
      # lower right
      x = cx + distance
      y = cy + distance
      while not isValidSquare( (x,y), self.ai.mapsize ):
        x -= 1
        y -= 1
      self.perimeter.append( (x, y) )
      
      # lower left
      x = cx - distance
      y = cy + distance
      while not isValidSquare( (x,y), self.ai.mapsize ):
        x -= 1
        y += 1
      self.perimeter.append( (x, y) )
           
      self.perimeter_cycler = itertools.cycle(self.perimeter)
      
class UnitInfo(object):
    def __init__(self, ai, unit):
      self.ai = ai
      self.unit = unit
      
class MapSearch(object):
    def __init__(self, size):
      self.mapsize = size   # size of map
      self.points = []      # (x,y) coords we need to explore
      self.sight = 20       # how far can our units see?
      
    def setup(self):
      for y in range(0, self.mapsize, self.sight):
        for x in range(0, self.mapsize, self.sight):
          self.points.append( (x,y) )
    
    # returns nearest point on map to unit
    def nearest(self, position):
      closest = self.mapsize
      point_found = None
      
      for p in self.points:
        distance = calc_distance( p, position )
        if distance < closest:
          closest = distance
          point_found = p
          
      return point_found
      
    def update(self, units):
      for p in self.points[:]:
          for unit in units:
            if unit.calcDistance( p ) < unit.sight / 2:
              self.points.remove(p)
              break

class Wedge(ai.AI):
    def _init(self):
      self.perimeter_distance = 6
       
      # our default units
      self.drones = []
      self.wander_radius = 25

      # scouting
      self.map = MapSearch(self.mapsize)
      self.map.setup()
      
      # buildings
      self.buildings = defaultdict(BuildingInfo)

    def wander(self, unit):
      if not unit.is_moving:  
        unit.move(self.position_on_circle(self.wander_radius, unit.position[0], unit.position[1]))

    def position_on_circle(self, radius, cx, cy):
      x,y = -1,-1

      while not isValidSquare( (x,y), self.mapsize):
        angle = random.randint(0,360)
        x = cx + radius * math.sin(angle)
        y = cy + radius * math.cos(angle)
      return (x,y)        

    def capture_target(self, unit, building):
      if unit.is_capturing:
        return True

      for friend in self.my_units:
        if friend != unit:
          if friend.is_capturing and friend.position == building.position:
            return False

      if unit.position == building.position:
        unit.capture(building)
      else:
        unit.move(building.position)

      return True

    def capture(self, unit):
      if unit.is_capturing:
        return True

      for building in unit.visible_buildings:
        if building.team == self.team:
          continue
  
        if unit.position == building.position:
          unit.capture(building)
        else:
          unit.move(building.position)
        return True

    def attack(self, unit):
      if unit.in_range_enemies:
        unit.shoot(unit.in_range_enemies[0].position)
        return True
    
    def scout(self, unit):
      if not self.capture(unit):
        waypoint = self.map.nearest( unit.position )
        if waypoint == None:
          self.wander( unit )
        else:
          unit.move( waypoint )
    
    def _unit_spawned(self, unit):
      self.drones.append(unit)
      
    def _unit_died(self, unit):
      if unit in self.drones:
        self.drones.remove(unit)
        return
        
      for key, value in self.buildings.iteritems():
        if unit == value.defender:
          value.defener = None
          
    def _spin(self):      
      # draw our waypoints, for debugging
      self.clearHighlights()
      for p in self.map.points:
        self.highlightLine( (p[0],p[1]), (p[0]+1, p[1]+1) )
        
      # update our map
      self.map.update(self.my_units)      

      # Check for perimeter distance increase
      if self.current_turn % 250 == 0:
        self.perimeter_distance += 5  
        
      # Add new buildings we discover
      for building in self.visible_buildings:
        if not building in self.buildings:
          self.buildings[building] = BuildingInfo(self, building)
          self.buildings[building].establish_perimeter(self.perimeter_distance)
         
      # Loop through all known buildings: 
      # value = BuildingInfo instance for the key = building
      for key, value in self.buildings.iteritems():
        if len(value.perimeter) == 0:
          value.establish_perimeter(self.perimeter_distance)
          
        print len(value.perimeter)
        
        # update perimeter if the distance has changed
        if self.perimeter_distance != value.perimeter_distance:
          value.establish_perimeter(self.perimeter_distance)

        # our buildings require specific actions
        if key.team == self.team:
        
          # if the building has no defender, request one (preferably closest available unit)
          if value.defender == None:
            closest = self.mapsize
            drone_assigned = None
            
            # loop through drones, find closest one
            for drone in self.drones:
              distance = drone.calcDistance(value.building.position)
              
              if distance < closest:
                closest = distance
                drone_assigned = drone
            
            # assign drone to defend & remove from drone pool
            if drone_assigned != None:
              value.defender = drone_assigned
              self.drones.remove(drone_assigned)
          # if we have a defender on this building, make sure its alive
          else:
            if not value.defender.is_alive:
              value.defender = None
              continue
            
          # Defender patrols the base perimeter
          defender = value.defender
          if defender != None:
            if not self.attack(defender):
              if not self.capture(defender):
                if not defender.is_moving:
                  defender.move( value.perimeter_cycler.next() )
    
      # Loop through our drones
      for unit in self.drones:
        if not self.attack(unit):
          if not self.capture(unit):
            if self.visible_enemies:
              unit.move( self.visible_enemies[0].position )
            else:
              self.wander(unit)
