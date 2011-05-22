import random
import ai
import math
from collections import defaultdict
import itertools
AIClass="Wedge"
import logging
log = logging.getLogger(AIClass)

class Base(object):
    def __init__(self, b):
      self.building = b
      self.capturing = False
      self.defenders = 0

    @property
    def capturing(self):
      return self.capturing

    @property
    def building(self):
      return self.building

class Wedge(ai.AI):
    def _init(self):
      log.info("Initializing: Current Turn: %s", self.current_turn)
      self.preferred_defenders = 1
      self.perimeter_distance = 6
      self.perimeters = {}
      self.perimeter_cyclers = {}
      self.defense_assignments = {}
      self.defenders = []
      
      # attackers
      self.attackers = []
      self.attacker_position = (0,0)
      self.attacker_distance = (8,4)     
      self.wander_radius = 35 
       
      # dummy units
      self.drones = []

      # scouting
      self.scouts = []
      self.do_scouting = True
      self.scout_waypoints = []      
      self.prev_waypoint = 0
      self.waypoint_distance = 1
      self.tries = 0 # tries before moving to next waypoint
      
      # buildings
      self.targets = []
      self.bases = []

    def setup_waypoints(self, unit):
      self.waypoint_distance = math.floor(unit.sight * 1.8)
      distance = self.waypoint_distance
      compass = ["west","south","east","north"]
      compass_cycler = itertools.cycle(compass) 
      cx = int(self.mapsize / 2)
      cy = int(self.mapsize / 2)
      self.scout_waypoints.append((cx,cy))
      x = cx
      y = cy
      create = True
      while(create):
        c = compass_cycler.next()
        if c == "west":
          x = x + distance
        elif c == "south":
          y = y + distance
          distance = distance + self.waypoint_distance
        elif c == "east":
          x = x - distance
        else:
          y = y - distance
          distance = distance + self.waypoint_distance

        create = self.valid_position(x,y)
        if create == False:
          if x < 1:
            x = 1
          if y < 1:
            y = 1
          if x > self.mapsize:
            x = self.mapsize -1
          if y > self.mapsize:
            y = self.mapsize -1

        self.scout_waypoints.append((x,y))
  
      # Add a loop around the outer border
      y = self.mapsize -1
      self.scout_waypoints.append((x,y))
      
      x = 1
      self.scout_waypoints.append((x,y))

      y = 1
      self.scout_waypoints.append((x,y))

      x = self.mapsize -1
      self.scout_waypoints.append((x,y))
      
    def defend(self, unit):
      if(self.attack(unit)):
        return True
    
      buildings = unit.visible_buildings
      if unit.is_capturing:
        return True

      for b in buildings:
        if b.team == self.team:
          continue

        if not unit.is_capturing:
          if unit.position == b.position:
            unit.capture(b)
          else:
            unit.move(b.position)

        return True

      self.attack(unit)

    def wander(self, unit):
      if not unit.is_moving:  
        unit.move(self.position_on_circle(self.wander_radius, unit.position[0], unit.position[1]))

    def position_on_circle(self, radius, cx, cy):
      x,y = -1,-1

      while(self.valid_position(x,y) == False):
        angle = random.randint(0,360)
        x = cx + radius * math.sin(angle)
        y = cy + radius * math.cos(angle)
      return (x,y)        

    def valid_position(self, x, y):
      if x < 0:
        return False
      if x >= self.mapsize:
        return False
      if y < 0:
        return False
      if y >= self.mapsize:
        return False

      return True
      
    def seek_and_capture(self, unit, building):
      if not self.attack(unit):
        if not self.capture_target(unit, building):      
          unit.move(building.position)

    def capture_target(self, unit, building):
      if unit.is_capturing:
        return True

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
      victims = unit.visible_enemies
      if victims:
        unit.shoot(victims[0].position)
        return True

    def scout(self, unit):
      if self.do_scouting == False:
        self.attackers.append(unit)
        self.scouts.remove(unit)
        return True

      if unit.is_moving:
        return True

      if self.prev_waypoint >= len(self.scout_waypoints):
        self.do_scouting = False
        return True

      if (unit.position == self.scout_waypoints[self.prev_waypoint]):
        self.prev_waypoint = self.prev_waypoint + 1

      unit.move(self.scout_waypoints[self.prev_waypoint])

    def establish_perimeter(self, building):
      perimeter = []      
      for i in range(0, self.preferred_defenders):
        x = -1
        y = -1
        while(self.valid_position(x,y) == False):
          x = random.randint(building.position[0] - self.perimeter_distance, building.position[0] + self.perimeter_distance)
          y = random.randint(building.position[1] - self.perimeter_distance, building.position[1] + self.perimeter_distance)
        
        perimeter.append((x,y))
      
      self.perimeters[building] = perimeter
      self.perimeter_cyclers[building] = itertools.cycle(self.perimeters[building])

    def assign_base(self, unit):    
      if (len(self.scouts) == 0):
        return False
      if (len(self.bases) <= 0):
        return False
  
      if (len(self.defenders) < len(self.bases) * self.preferred_defenders):
        counters = defaultdict(int)
        for building in self.bases:
          counters[building] = 0
          for k,v in self.defense_assignments.iteritems():
            if (v == building):
              counters[building] = counters[building] + 1

        assign_to = min(counters, key = lambda x: counters.get(x))
        self.defense_assignments[unit] = assign_to
        return True
      
      return False

    def assign_scout(self, unit):
      if (len(self.scouts) == 0 and self.do_scouting == True):
        if (len(self.scout_waypoints) == 0):
          self.setup_waypoints(unit)
        self.scouts.append(unit)
        return True
    
    def _unit_spawned(self, unit):
      self.drones.append(unit)
      
    def _unit_died(self, unit):
      if unit in self.drones:
        self.drones.remove(unit)
      if unit in self.defenders:
        self.defenders.remove(unit)
        del self.defense_assignments[unit]
      if unit in self.attackers:
        self.attackers.remove(unit)
      if unit in self.scouts:
        self.scouts.remove(unit)
        if(self.prev_waypoint > 0):
          self.tries = self.tries + 1
          if(self.tries >= 2):
            self.prev_waypoint = self.prev_waypoint + 1
          else: 
            self.prev_waypoint = self.prev_waypoint - 1
          

    def _spin(self):      
      self.clearHighlights()
      if (len(self.scout_waypoints) > 0):
        prev_waypoint = self.scout_waypoints[0]
        for waypoint in self.scout_waypoints:
          self.highlightLine(prev_waypoint, waypoint)
          prev_waypoint = waypoint

      if (self.current_turn % 250 == 0):
        self.preferred_defenders = self.preferred_defenders + 1
        self.perimeter_distance = self.preferred_defenders * 3
        for b in self.bases:
          self.establish_perimeter(b)
      
      if self.visible_buildings:
        for b in self.visible_buildings:
          if b in self.bases:
            if not b.team == self.team:
              self.bases.remove(b)
              #del self.perimeters[b]
              #del self.perimeter_cyclers[b]
              self.targets.append(b)
          elif b in self.targets:
            if b.team == self.team:
              self.establish_perimeter(b)
              self.bases.append(b)
              self.targets.remove(b)
          else:
            if b.team == self.team:
              self.establish_perimeter(b)
              self.bases.append(b)
            else:
              self.targets.append(b)
    
      for unit in self.my_units:
        if unit in self.drones:
          if self.assign_base(unit):
            self.defenders.append(unit)
          else:
            if not self.assign_scout(unit):
              self.attackers.append(unit)
              self.attacker_position
          self.drones.remove(unit)

        if unit in self.scouts:
          if not self.capture(unit):
            self.scout(unit)

        if unit in self.defenders:
          if not self.defend(unit):
            if not unit.is_moving:
              unit.move(self.perimeter_cyclers[self.defense_assignments[unit]].next())

        if unit in self.attackers:
          if not self.attack(unit):
            if not self.capture(unit):
              if len(self.targets) > 0:
                self.capture_target(unit, self.targets[0])
              elif len(self.visible_enemies) > 0:
                enemies = list(self.visible_enemies)
                unit.move(enemies[0].position)
              else:
                self.wander(unit)
