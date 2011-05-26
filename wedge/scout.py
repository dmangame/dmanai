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
