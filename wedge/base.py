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
            
class MapSearch(object):
    def __init__(self, size):
      self.mapsize = size   # size of map
      self.points = []      # (x,y) coords we need to explore
      self.sight = 20       # how far can our units see?
      
    def setup(self):
      self.width = 0
      self.height = 0
      start = int(self.sight / 2)
      for y in range(start, self.mapsize, self.sight):
        self.height += 1
        self.width = 0
        for x in range(start, self.mapsize, self.sight):
          self.points.append( (x,y) )
          self.width += 1

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

class Pather(object):
    def __init__(self, ai, unit):
      self.ai = ai
      self.unit = unit
      self.path = None      
      self.node = 0
      
    def setup(self, position, length = 75, node = 0):
      self.path = self.create_path(length, position)
      self.node = node
      
    def update(self):
      if self.path == None:
        return
        
      if self.unit == None:
        return
        
      if self.unit.is_alive:
        if not self.ai.capture(self.unit):
          if self.unit.calcDistance(self.path[self.node]) < 2:
            self.node += 1
            if self.node >= len(self.path):
              self.node = 0
            
          self.unit.move( self.path[self.node] )
      else:
        pass
        
    # create a path of points length long, will generate with points starting closest to position
    def create_path(self, length, position):
      # figure out the order we want to travel... could be up -> left -> down -> right or up -> right -> down -> left or down -> left ... etc
      # we lean towards exploring the center of the board first
      down = True
      if position[1] > self.ai.mapsize / 2:
        down = False # if we are on the bottom half, go up instead
        
      right = True
      if position[0] > self.ai.mapsize / 2:
        right = False # if we are on the right side, go left instead
      
      if down and right:
        compass = ["down", "right", "up", "left"]
      elif down and not right:
        compass = ["down", "left", "up", "right"]
      elif not down and right:
        compass = ["up", "right", "down", "left"]
      else:
        compass = ["up", "left", "down", "right"]      
      
      waypoints = []
      waypoints.append(position)
      x = position[0]
      y = position[1]
      
      direction = 0             # direction to start in
      steps_in_direction = 0    # steps taken in current direction
      steps_to_take = 1         # steps to take before changing direction
      steps_prev_taken = 0      # stores number of steps actually taken on previous leg
      turns = 0                 # number of turns taken
      tries = 0                 # number of tries at isValidSquare
      
      while len(waypoints) < length:        
        mx, my = x,y
        if compass[direction] == "down":
          y += self.unit.sight
        elif compass[direction] == "up":
          y -= self.unit.sight
        elif compass[direction] == "left":
          x -= self.unit.sight
        elif compass[direction] == "right":
          x += self.unit.sight
        else:
          return
          
        if isValidSquare( (x, y), self.ai.mapsize ):
          waypoints.append( (x, y) )
          
          steps_in_direction += 1
          
          if steps_in_direction >= steps_to_take:
            turns += 1
            steps_in_direction = 0
            direction += 1
            
            if direction >= len(compass):
              direction = 0
              
            if (direction == 0 or direction == 2) and turns >= 2:
              steps_to_take += 1
              
        else:
          x, y = mx, my
          
          # hit a wall, we need to turn outward and reverse the compass
          direction -= 1
          if direction < 0:
            direction = 3
            
          compass = self.swap_compass(compass, direction)
          steps_in_direction = steps_to_take # the next valid square will cause a natural turn
          
          tries += 1
          if tries > 4:
            return waypoints        
          
      return waypoints
      
    def swap_compass(self, compass, direction):
      if direction == 1 or direction == 3:
        if compass[0] == "up":
          compass[0] = "down"
          compass[2] = "up"
        else:
          compass[0] = "up"
          compass[2] = "down"
      else:
        if compass[1] == "left":
          compass[1] = "right"
          compass[3] = "left"
        else:
          compass[1] = "left"
          compass[3] = "right"
        
      return compass    

class Wedge(ai.AI):
    def _init(self):
      self.perimeter_distance = 6
       
      # our default units
      self.drones = []
      self.wander_radius = 25

      # scouting
      self.scout = None
      
      # map info
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
      targets = list(self.visible_enemies)
                     
      # update our map
      self.map.update(self.my_units)      
      
      if self.scout == None:
        if len(self.drones) > 0:
          self.scout = Pather(self, self.drones[0])
          self.drones.remove(0)
      else:
        if self.scout.path == None:
          if self.my_buildings:
            self.scout.setup(self.my_buildings[0].position)
        else:
          if not self.scout.unit.is_alive:
            if len(self.drones) > 0:
              self.scout = Pather(self, self.drones[0])
              self.drones.remove(0)
            
          self.scout.update()
        
          # draw our waypoints, for debugging
          self.clearHighlights()
          last_point = self.scout.path[0]
          for p in self.scout.path:
            self.highlightLine( last_point, p )
            last_point = p        

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
              
              if distance < closest and drone != self.scout.unit:
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
        
        # else building not on our team
        else:
          targets.append(key)
    
      # Loop through our drones
      for unit in self.drones:
        if unit == self.scout.unit:
          continue
        if not self.attack(unit):
          if not self.capture(unit):
            if len(targets) == 0:
              self.wander(unit)
            else:
              # find closest target & move towards
              closest = self.mapsize * 2
              target = None
              
              for t in targets:
                distance = unit.calcDistance(t.position)
                
                if distance < closest:
                  closest = distance
                  target = t
              
              unit.move(target.position)
