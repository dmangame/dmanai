import ai
import operator
import sys
import os
sys.path.append(os.path.dirname(__file__))

from wedgeutil import calc_distance
from wedgeutil import closest_thing


# MapSearch creates a list of points for our units to search
# AI can call nearest(position_of_unit) and get a point to travel to
# nearest() weights the points based off of distance from unit and distance from buildings
class MapSearch(object):
    def __init__(self):
      self.mapsize = 10000  # size of map
      self.sight = 20       # how far can our units see?
      self.range = self.sight # how far away do units have to be before they are considered to have explored a point?      

      self.points = []      # (x,y) coords we need to explore
      self.distances = {}   # each dictionary entry contain the distances from a building to all points
                            # self.distances[building][point] = distance
      
    def setup(self, size, sight):
      self.mapsize = size
      self.sight = sight
      self.range = self.sight * 0.5

      start = int(self.sight / 2)
      for y in range(start, self.mapsize, self.sight):
        for x in range(start, self.mapsize, self.sight):
          self.points.append( (x,y) )

    # looks at 4 closest points to position & adds distance to closest building
    # returns point with combined distance closest to position
    def nearest(self, position):
      if len(self.points) == 0:
        return None

      # calc distances to our position
      distances = {}
      
      for p in self.points:
        distances[p] = calc_distance( p, position )

        # if the point we just checked is within the units sight range, return this point immediately
        if distances[p] < self.sight:
          return p

      sorted_d = sorted( distances.items(), key = lambda x: x[1] )

      building_found = closest_thing( position, self.distances.keys() )

      if building_found == None:
        return sorted_d[0][0]

      sorted_d = list(sorted_d[0:5]) # take first four sorted points
      
      for i in range( 0, len(sorted_d) ):
        sorted_d[i] = list(sorted_d[i])
        sorted_d[i][1] = calc_distance( sorted_d[i][0], building_found.position ) + sorted_d[i][1]

      sorted_d = sorted( distances.items(), key = lambda x: x[1] )

      return sorted_d[0][0]      

    # adds a building
    def building(self, b):
      if not b in self.distances:
        # ordered list of our points
        distances = {}
        for p in self.points:
          distances[p] = calc_distance( p, b.position )

        distances = sorted( distances.items(), key = lambda x: x[1] )

        #rebuild a list of points now that they are sorted
        sorted_p = []
        for i in distances:
          sorted_p.append( i[0] ) # only take the point, which is in [0], the distance is in [1]

        self.distances[b] = sorted_p
      
    def update(self, units):
      for p in self.points[:]:
        for unit in units:
          if unit.calcDistance( p ) < self.range:
            self.points.remove(p)
            for key,value in self.distances.iteritems():
              if p in self.distances[key]:
                self.distances[key].remove(p)
            break
