import ai
import time
import copy
AIClass="SystematicSearcher"

#just a merge of expanding-blob then searcher if more than N units

class LocationHistory:
    area_size = 15
    def __init__(self, size):
      areas = [(x*self.area_size,y*self.area_size) for x in xrange((size+10)/self.area_size) for y in xrange((size+10)/self.area_size)]
      self.visit_time_positions = {0: areas}
      self.position_visit_times = dict((area,0) for area in areas)
      self.duplicates = {}
      self.duplicated = {}

    def get_least_recently_visited_area(self, my_location, exclude):
      visit_times = sorted(self.visit_time_positions.keys())
      min_distance = float('inf')
      min_location = my_location #stay put if everything is already excluded, we probably won
      for visit_time in visit_times:
        for area in self.visit_time_positions[visit_time]:
          if area in exclude and area in self.duplicates:
            self.duplicates[area] -= 1
            self.duplicated.setdefault(area,0)
            self.duplicated[area] += 1
            if self.duplicates[area] == 1:
              del self.duplicates[area]
          elif area in exclude:
            continue
          distance = (my_location[0]-area[0])**2+(my_location[1]-area[1])**2
          if distance < min_distance:
            min_location = area
            min_distance = distance
        if min_distance != float('inf'):
          break
      return min_location

    def visited(self, positions, now=None, duplicate=1):
      if now is None:
        now = int(time.time()*10000)
      if now not in self.visit_time_positions:
        self.visit_time_positions[now] = []
      for rpos in positions:
        position = (int(rpos[0]/self.area_size)*self.area_size,int(rpos[1]/self.area_size)*self.area_size)
        if position in self.duplicated:
          self.duplicated[position] -= 1
          if self.duplicated[position] == 0:
            del self.duplicated[position]
          continue
        if duplicate > 1:
          self.duplicates[position] = duplicate
        self.visit_time_positions[now].append(position)
        previous = self.position_visit_times[position]
        self.position_visit_times[position] = now
        self.visit_time_positions[previous].remove(position)
        if len(self.visit_time_positions[previous]) == 0:
          del self.visit_time_positions[previous]


def distance(a,b):
  return (a[0]-b[0])**2+(a[1]-b[1])**2

class SystematicSearcher(ai.AI):

    def _init(self):
      self.guards           = set()
      self.known_buildings  = set()
      self.building_guards  = {}
      self.guard_buildings  = {}
      self.recently_visited = []
      self.location_history = LocationHistory(self.mapsize)
      self.building_patrollers = {}
      self.potential_base     = {}

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

    def determine_potential_bases(self):
      bases = set()
      for location in self.potential_base:
        if self.potential_base[location] >= 3:
          self.potential_base[location] = 1
          self.location_history.visited( [location], now=-1, duplicate=4 )
      return bases

    def choose_troop_locations(self):
      locations = {}

      # get some help over to troops under attack -- probably usually useless
      under_attack = [unit.position for unit in self.my_units if unit.is_under_attack]
      if len(under_attack) > 0:
        self.location_history.visited( under_attack, now=-2 )

      for building in self.known_buildings:
        if building.team != self.team:
          self.location_history.visited( [building.position], now=-2, duplicate=5 )

      potential_bases = self.determine_potential_bases()

      for unit in self.my_units:
        if unit in self.guards:
          locations[unit] = self.guard_buildings[unit].position
        else:
          locations[unit] = self.location_history.get_least_recently_visited_area( unit.position, exclude=locations.values() )
      return locations

    def attack_or_move_troops(self, locations):
      for unit in locations:
        capture = None
        for building in unit.visible_buildings:
          if building.team != unit.team and unit.position == building.position:
            capture = building

        max_victims  = 0, 0
        max_unit     = None
        for enemy in unit.visible_enemies:
          if enemy.position == unit.position:
            max_victims  = 1
            max_unit     = enemy
            break # definitely kill this guy
          elif not enemy.is_moving:
            max_victims  = 4
            max_unit     = enemy
            # we may want to shoot, but its not likely, and if we are on someone, we have to kill them
          victims = unit.calcVictims(enemy.position)
          num_victims = len(victims), 10*len(victims)-sum(victim.energy for victim in victims)
          if (num_victims) > max_victims:
            max_victims  = num_victims
            max_unit     = enemy

        if max_victims > (0,0):
          if not max_unit.is_moving and max_unit.position != unit.position:
              unit.move(max_unit.position)
          else:
            unit.shoot(max_unit.position)
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

    def _unit_died(self,unit):
      rpos = (unit.position[0]/15, unit.position[1]/15)
      self.potential_base.setdefault(rpos, 0)
      self.potential_base[rpos] += 1
