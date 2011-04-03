
import ai
import random
import math
import itertools
from collections import defaultdict
AIClass = "SearchAI"

class SearchAI(ai.AI):
    def _init(self):
        self.liveUnits = {}
        self.scouts = {}
        self.defenders = {}
        self.wasSquareExplored = []
        for y in xrange(0, self.mapsize+1):
          row = []
          for x in xrange(0, self.mapsize+1):
            row.append(False)
          self.wasSquareExplored.append(row)
        self.regions = []
        self.scoutsByRegion = []
        self.sight = None
        self.speed = None
        self.scoutSpeed = None
        self.scoutViewWidth = None

    def initUnit(self, unit):
        if self.sight == None:
          self.sight = unit.sight
        if self.speed == None:
          self.speed = unit.speed
        if self.scoutSpeed == None:
          # Compute the maximum reasonable speed a scout should go
          # so that it doesn't move too fast to see everything
          maxScoutSpeed = 2.0 * self.sight * math.cos(30.0 * 3.141592/180.0)
          self.scoutSpeed = self.speed if (self.speed <= maxScoutSpeed) else \
              maxScoutSpeed
        if self.scoutViewWidth == None:
          # Now that we have computed the speed at which the scout should move,
          # compute the "width" of the scout's view as it moves
          self.scoutViewWidth = 2.0 * \
              math.sqrt((self.sight**2) - 0.25*(self.scoutSpeed**2))

    def destroyUnit(self, unit):
        if unit in self.liveUnits:
          del self.liveUnits[unit]
        if unit in self.defenders:
          del self.defenders[unit]
        if unit in self.scouts:
          del self.scouts[unit]

    def account(self, unit):
        if not getattr(unit,'inited',False):
          self.initUnit(unit)
          unit.inited = True
        if not unit.is_alive:
          if not getattr(unit,'destructed',False):
            self.destroyUnit(unit)
            unit.destructed = True
          return
        for pos in unit.visible_squares: 
          x,y = pos
          self.wasSquareExplored[x][y] = True

    def search(self, unit):
        if not unit in self.liveUnits:
          if len(self.defenders) == 0:
            self.liveUnits[unit] = "D";
          else:
            self.liveUnits[unit] = "S";

        hittableEnemies = self.wt.inRange(unit)
        if len(hittableEnemies) != 0:
          numEnemies = len(hittableEnemies)
          i = random.randint(0,numEnemies-1)
          unit.shoot(hittableEnemies[i].position)
          return

        if self.liveUnits[unit] == "D" and not unit in self.defenders:
          self.defenders[unit] = True

        if self.liveUnits[unit] == "S" and not unit in self.scouts:
          # If no regions have been built, determine the
          # initial quadrants
          if len(self.regions) == 0:
            self.regions = []
            self.scoutsByRegion = []
            xDelta = self.mapsize / 4.0
            yDelta = self.mapsize / 4.0
            x = 0.0
            for i in xrange(0,4):
              y = 0.0
              for j in xrange(0,4):
                self.regions.append((x,y,x+xDelta,y+yDelta))
                self.scoutsByRegion.append({})
                y += yDelta
              x += xDelta

          # If there are more explorers than regions, rebalance the regions
          #if len(self.scouts) >= len(self.regions): 
          
          # If this scout does not have a dedicated region, choose one
          if getattr(unit,'scoutRegion',None) == None:
            bestRegion = None
            bestScore = None  # lower score is better
            for i in xrange(0,len(self.regions)):
              score = len(self.scoutsByRegion[i])
              if bestScore == None or score < bestScore:
                bestScore = score
                bestRegion = i
            self.scoutsByRegion[bestRegion][unit] = True;
            unit.scoutRegion = bestRegion
          
          x,y = unit.position
          choices = []
          xRangeMin,yRangeMin,xRangeMax,yRangeMax = \
              self.regions[unit.scoutRegion]
          for i in xrange(0,100):
            x0 = random.randint(int(xRangeMin), int(xRangeMax))
            y0 = random.randint(int(yRangeMin), int(yRangeMax))
            if not self.wasSquareExplored[x0][y0]:
              choices.append((x0,y0))
          bestSqDist = None
          bestPos = None
          for pos in choices:
            x0,y0 = pos
            sqDist = ((x-x0)*(x-x0) + (y-y0)*(y-y0))
            if (bestSqDist == None or sqDist < bestSqDist):
              bestSqDist = sqDist
              bestPos = pos
          if (bestPos != None):
            x,y = bestPos
          self.scouts[unit] = (x,y)

        if unit in self.scouts:
          pos = unit.position
          x,y = pos
          end_pos = self.scouts[unit]
          if (pos != end_pos):
            unit.move(end_pos)
          else:
            choices = []
            xRangeMin,yRangeMin,xRangeMax,yRangeMax = \
                self.regions[unit.scoutRegion]
            for i in xrange(0,100):
              x0 = random.randint(int(xRangeMin), int(xRangeMax))
              y0 = random.randint(int(yRangeMin), int(yRangeMax))
              if not self.wasSquareExplored[x0][y0]:
                choices.append((x0,y0))
            xB, yB = x0, y0
            if (len(self.my_buildings) != 0):
              xB, yB = self.my_buildings[0].position
            bestSqDist = None
            bestPos = None
            for pos in choices:
              x0,y0 = pos
              sqDist = ((x-x0)*(x-x0) + (y-y0)*(y-y0)) * 3.0 + \
                       ((xB-x0)*(xB-x0) + (yB-y0)*(yB-y0)) * 1.0
              if (bestSqDist == None or sqDist < bestSqDist):
                bestSqDist = sqDist
                bestPos = pos
            if (bestPos != None):
              end_pos = bestPos
              self.scouts[unit] = end_pos
              unit.move(end_pos)

    def _spin(self):
        for unit in self.my_units:
          self.account(unit)
        for unit in self.my_units:
          self.search(unit)

    def _unit_spawned(self, unit):
        pass
