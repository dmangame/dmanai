import ai
import random
import ai_exceptions
import logging
from collections import defaultdict
log = logging.getLogger(AIClass)

AIClass="GooseAI"

require_dependency(module_name="okay")


class GooseAI(okay.OkayAI):
  PLAY_IN_LADDER=True
  def _init(self):
    self.areas = 8
    self.squads = []
    self.buildings = set()


  def to_area_square(self, (x,y)):
    area_size = self.mapsize / self.areas
    return (x/area_size*area_size, y/area_size*area_size)


  def _unit_spawned(self, unit):
    for s in self.squads:
      if len(s) < 3:
        s.add_unit(unit)
        return

    self.squads.append(okay.V(left=unit, base=unit.position, mapsize=self.mapsize))

  def _unit_died(self, unit):
    to_remove = []
    for s in self.squads:
      s.remove_unit(unit)
      if len(s) == 0:
        to_remove.append(s)

    for s in to_remove:
      self.squads.remove(s)


  def _spin(self):
    my_buildings = set(self.my_buildings)
    i = 0
    if not self.squads:
      return

    guarding = []
    buildings_covered = defaultdict(bool)
    for s in self.squads:
      if s.guarding:
        buildings_covered[s] = s.guarding
        guarding.append(s)

    for b in my_buildings:
      if i >= len(self.squads):
        break
      if not buildings_covered[b]:
        s = self.squads[i]
        s.guard(b, self.fuzz_position)
        i+=1


    # Will send all squads to capture.
    capture_buildings = set(self.buildings.values()) - my_buildings
    if capture_buildings:
      available_units = len(self.squads) - i
      squad_per_b = available_units / len(capture_buildings)
      for b in capture_buildings:
        if i >= len(self.squads):
          break
        deploy = self.squads[i:i+squad_per_b]
        i += squad_per_b
        for s in deploy:
          if s.full_squad and len(s) >= 3:
            s.capture_building(b)
          else:
            break


    for s in self.squads[i:]:
      if not s.is_moving(at_least=3):
        # Pick closest point for unit to visit
        destination = self.searcher.next_destination(s)
        self.searcher.destinations[s] = destination
        self.searcher.visiting[destination] = s

        # Go visit a new position
        s.move_to(self.searcher.destinations[s])

    for s in self.squads:
      s.spin()

