from world import isValidSquare
import itertools

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
        x += 1
        y -= 1
      self.perimeter.append( (x, y) )
           
      self.perimeter_cycler = itertools.cycle(self.perimeter)

