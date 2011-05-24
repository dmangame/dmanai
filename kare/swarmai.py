import ai
import random
from collections import defaultdict
import itertools
AIClass = "SwarmAI"

def calculate_distance( a, b ):
  x1, y1 = a.position
  x2, y2 = b.position
  x = abs(x1-x2)
  y = abs(y1-y2)
  return x+y


class SwarmAI(ai.AI):

  def _spin(self):
      for unit in self.my_units:
        self.patrol( unit )

    

  def patrol(self, unit):
      # If we're capturing an enemy building, don't do anything.
      if unit.is_capturing:
        return

      # If any enemies are in range, try to shoot them
      if unit.in_range_enemies:
        unit.shoot( unit.in_range_enemies[0].position )
        return
      
      # Look out for any enemy buildings
      for b in unit.visible_buildings:
        if b.team == self.team:
          continue
        # If someone is already capturing the building, continue.
        # Otherwise try to capture it
        if self.capture( unit, b ):
          return
          
      # Check if there's a friend near
      friend_near = False
      for friend in self.my_units:
        if friend != unit:
          # Calculate distance to the friend
          distance = calculate_distance( unit, friend )
          # If the friend needs help and is near enough, move towards it
          if (friend.is_under_attack or friend.is_shooting) and distance < 20:
            unit.move( friend.position )
            return
          else:
            if distance < 5:
              friend_near = True

      # If a friend is near and not in need of help,
      # take a step randomly
      if friend_near:
        x, y = unit.position
        unit.move((x+2-random.randint(0, 4),
                   y+2-random.randint(0, 4)))



  def capture(self, unit, b):
    # Loop through friends
    for friend in self.my_units:
      if friend != unit:
        # If a friend is capturing the base, continue acting normally
        if friend.position == b.position and friend.is_capturing:
          return False

    # Otherwise if the unit is at the same location as the building,
    # try to capture it.
    if unit.position == b.position:
      unit.capture( b )
    # If not, move towards the base
    else:
      unit.move( b.position )
    return True

