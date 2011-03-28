import ai
import time

AIClass="SystematicSearcher"

class LocationHistory:
    area_size = 8
    def __init__(self, size):
      areas = [(x*self.area_size,y*self.area_size) for x in xrange((size+10)/self.area_size) for y in xrange((size+10)/self.area_size)]
      self.visit_time_positions = {0: areas}
      self.position_visit_times = dict((area,0) for area in areas)

    def get_least_recently_visited_area(self, my_location, exclude):
      visit_times = sorted(self.visit_time_positions.keys())
      min_distance = float('inf')
      min_location = my_location #stay put if everything is already excluded, we probably won
      for visit_time in visit_times:
        for area in self.visit_time_positions[visit_time]:
          if area in exclude:
            continue
          distance = (my_location[0]-area[0])**2+(my_location[1]-area[1])**2
          if distance < min_distance:
            min_location = area
            min_distance = distance
        if min_distance != float('inf'):
          break
      return min_location

    def visited(self, positions, now=None):
      if now is None:
        now = int(time.time()*10000)
      while now in self.visit_time_positions:
        now += 1
      self.visit_time_positions[now] = []
      for rpos in positions:
        position = (int(rpos[0]/self.area_size)*self.area_size,int(rpos[1]/self.area_size)*self.area_size)
        self.visit_time_positions[now].append(position)
        previous = self.position_visit_times[position]
        self.position_visit_times[position] = now
        self.visit_time_positions[previous].remove(position)
        if len(self.visit_time_positions[previous]) == 0:
          del self.visit_time_positions[previous]

class SystematicSearcher(ai.AI):
    #color = (0,1,0)
    def _init(self):
      self.guards           = set()
      self.known_buildings  = set()
      self.building_guards  = {}
      self.guard_buildings  = {}
      self.recently_visited = []
      self.location_history = LocationHistory(self.mapsize)

    def allocate_guards(self):
      non_guards = list(set(self.my_units).difference(self.guards)) #assumes my_units are all alive
      try:
        for building in self.known_buildings:
          if building not in self.building_guards or self.building_guards[building] not in self.my_units:
            guard = None
            min_distance = float('inf')
            for unit in non_guards:
              distance = (unit.position[0]-building.position[0])**2+(unit.position[1]-building.position[1])**2
              if distance < min_distance:
                min_distance = distance
                guard = unit
            if guard is None:
              continue
            non_guards.remove(guard)
            self.building_guards[building] = guard
            self.guard_buildings[guard] = building
            self.guards.add(guard)
      except KeyError:
        print 'unable to allocate enough troops for guarding known buildings'
        return

    def choose_troop_locations(self):
      locations = {}

      # get some help over to troops under attack -- probably usually useless
      under_attack = [unit.position for unit in self.my_units if unit.is_under_attack]
      if len(under_attack) > 0:
        self.location_history.visited( under_attack, now=1 )

      capturing_need_backup = set()
      for building in self.known_buildings:
        if building.team != self.team:
          capturing_need_backup.add(building) #TODO choose number of buddies (and guards) per building based on how many we have

#      wait_for_buddy = False#len(self.my_units)-len(self.guards)-len(capturing_need_backup) <= 1

      for unit in self.my_units:
        if unit in self.guards:
          locations[unit] = self.guard_buildings[unit].position
        elif len(capturing_need_backup) > 0:
          locations[unit] = capturing_need_backup.pop().position
        #TODO if we think we know where an enemy might be, we should hunt them down
#        elif wait_for_buddy:
#          min_distance = float('inf')
#          min_position = self.location_history.get_least_recently_visited_area( unit.position, exclude=locations.values() )
#          for building in self.known_buildings:
#            if building.team == self.team:
#              distance = (building.position[0]-unit.position[0])**2+(building.position[1]-unit.position[1])**2
#              if distance < min_distance:
#                min_distance = distance
#                min_position = building.position
#          locations[unit] = min_position
        else:
          locations[unit] = self.location_history.get_least_recently_visited_area( unit.position, exclude=locations.values() )
      return locations

    def attack_or_move_troops(self, locations):
      for unit in locations:
        capture = None
        for building in unit.visible_buildings:
          if building.team != unit.team and unit.position == building.position:
            capture = building

        max_victims = 0
        max_position = None
        for enemy in unit.visible_enemies:
          num_victims = len(unit.calcVictims(enemy.position))
          if num_victims > max_victims:
            max_victims = num_victims
            max_position = enemy.position

        if max_victims > 0:
          unit.shoot(max_position)
        elif capture is not None:
          unit.capture(capture)
        else:
          unit.move(locations[unit])

    def _spin(self):
      self.guards = set(guard for guard in self.guards if guard.isAlive())
      self.known_buildings = set(self.visible_buildings).union(self.known_buildings)
      if len(self.guards) < len(self.known_buildings):
        self.allocate_guards()

      self.location_history.visited( [unit.position for unit in self.my_units] )
      locations = self.choose_troop_locations()

      self.attack_or_move_troops(locations)

    def _new_unit(self, unit):
      print "Received a new unit: %s" % unit
