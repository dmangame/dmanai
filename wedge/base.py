import random
import ai
import math
from collections import defaultdict
from heapq import merge
import itertools
from world import isValidSquare

AIClass="Wedge"

import sys
import os
sys.path.append(os.path.dirname(__file__))
import buildinginfo
import mapsearch
from wedgeutil import closest_thing

class Wedge(ai.AI):
    def _init(self):
      # config
      self.perimeter_distance = 3
      self.wander_radius = 25      
      self.search_until = 200     # number of turns to search without fighting and without assisting other drones      

      # status
      self.setup_complete = False  # set to True when we get our first unit, we need info on sight etc from units

      # our default units
      self.drones = []
            
      # map info
      self.map = mapsearch.MapSearch()
      
      # buildings
      self.buildings = defaultdict(buildinginfo.BuildingInfo)

    def wander(self, unit):
      if not unit.is_moving:  
        unit.move(self.position_on_circle(self.wander_radius, unit.position))

    def position_on_circle(self, radius, center):
      x,y = -1,-1

      while not isValidSquare( (x,y), self.mapsize):
        angle = random.randint(0,360)
        x = center[0] + radius * math.sin(angle)
        y = center[1] + radius * math.cos(angle)
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

        friend_capturing = False
        for friend in self.my_units:
          if friend != unit:
            if friend.is_capturing and friend.position == building.position:
              friend_capturing = True

        if friend_capturing:
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

    def explore(self, unit):
      point = self.map.nearest(unit.position)
      if point == None:
        self.wander(unit)
      else:
        unit.move(point)

    def highlight(self):
      # draw map search coords
      self.clearHighlights()
      for p in self.map.points:
        self.highlightLine( p, (p[0] + 1, p[1] + 1) )
    
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
      # run setup if needed
      if not self.setup_complete:
        if len(self.drones) > 0:
          self.map.setup( self.mapsize, self.drones[0].sight )
          self.setup_complete = True

      # print out highlights & debug info if needed
      self.highlight()
 
      # create lists 
      enemies = list(self.visible_enemies)
      targets = []  # list of building we don't own that we know about
      bases = []    # list of building we own
                     
      # update our map
      self.map.update(self.my_units)      
      
      # Check for perimeter distance increase
      if self.current_turn % 250 == 0:
        self.perimeter_distance += 2  
        
      # Add new buildings we discover
      for building in self.visible_buildings:
        if not building in self.buildings:
          self.buildings[building] = buildinginfo.BuildingInfo(self, building)
          self.buildings[building].establish_perimeter(self.perimeter_distance)
          self.map.building(building)
         
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
                  try:
                    defender.move( value.perimeter_cycler.next() )
                  except StopIteration:
                    self.wander(defender)
        
        # else building not on our team
        else:
          targets.append(key)
    
      # Loop through our drones
      for unit in self.drones:
        # Attempt to attack any enemies in range
        if not self.attack(unit):
          # Attempt to capture any building in range
          if not self.capture(unit):
            # Either: Explore map or assist other drones
            if self.current_turn <= self.search_until:
              self.explore(unit)
            else:
              # this area needs a lot of work, target selection is the weakest link right now
              target = closest_thing( unit.position, list(merge(targets, enemies)) )
              
              if target == None:
                self.explore(unit)
              else:
                unit.move( self.position_on_circle( unit.sight - 1, target.position ) )
