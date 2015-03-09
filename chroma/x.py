import random
from collections import defaultdict
import operator
from itertools import chain

import ai
from mapobject import Building

AIClass="XS"

class X(object):
    PLAY_IN_LADDER=True
    def __init__(self, ai, units=None, spread=1):
        self.ai = ai
        self.units = units or []
        self.spread = spread

    def __contains__(self, unit):
        return unit in self.units

    def __iter__(self):
        return iter(self.units)

    def __getitem__(self, item):
        return self.units[item]

    def add(self, unit):
        self.units.append(unit)

    def remove(self, unit):
        self.units.remove(unit)

    @property
    def count(self):
        return len(self.units)

    @property
    def position(self):
        return self[0].position

    def move(self, pos, formation=True):
        def limit(val):
            return max(0, min(val, self.ai.mapsize))

        d = self.spread
        if formation:
            slot = [(0,0), (d,d), (d,-d), (-d,d), (-d,-d), (0, d), (d, 0), (0, -d), (-d, 0)]
        else:
            slot = [(0,0)]*9
        for i, unit in enumerate(self):
            dest = (limit(pos[0]+slot[i][0]),
                    limit(pos[1]+slot[i][1]))
            if unit.position != dest:
                unit.move(dest)
    
    @property
    def is_moving(self):
        return all(u.is_moving for u in self.units)

    def attack(self):
        ts = defaultdict(int)
        for unit in self:
            for e in unit.in_range_enemies:
                ts[e.position] += 1
        
        ts = sorted(ts.iteritems(), key=operator.itemgetter(1), reverse=True)
        for unit in self:
            # TODO: shoot closest in range
            if ts:
                unit.shoot(ts[0][0])

    def capture(self, building):
        self.units[0].capture(building)

class XS(ai.AI):
    def _init(self):
        self.xs = []
        self.buildings = set()
        self.last_seen = list()
        self.minimum = 1

    def target(self):
        if self.last_seen:
            m = self.mapsize/2
            return (self.last_seen[0][0] + random.randint(-m, m),
                    self.last_seen[0][1] + random.randint(-m, m))
        else:
            return (random.randint(0, self.mapsize),
                    random.randint(0, self.mapsize))

    def _spin(self):
        for x in self.xs:
            for unit in x:
                for b in unit.visible_buildings:
                    self.buildings.add(b)
                
                for e in unit.visible_enemies:
                    self.last_seen.insert(0, e.position)

        targets = sorted(
            self.buildings,
            key = lambda b: 1 if b.team == self.team else 2)

        for i, x in enumerate(self.xs):
            t = hostile = None
            if i < len(targets):
                t = targets[i]
                hostile = t.team != self.team

            if x.count <= self.minimum:
                x.move(targets[0].position)
                x.attack()
                continue

            if t:
                if x.position == t.position and hostile:
                    x.move(t.position, False)
                    x.capture(t)
                    continue
                else:
                    x.move(t.position)
                    x.attack()
                    continue

            if not x.is_moving:
                x.move(self.target())
                x.attack()

    def _unit_spawned(self, unit):
        pos = unit.position
        tx = None
        print '---'
        for x in self.xs:
            size = min(9, self.minimum + len(self.xs) - 2)
            print x.count, size
            if x.count < size:
                tx = x
                break
        else:
            tx = X(self)
            self.xs.append(tx)

        tx.add(unit)

    def _unit_died(self, unit):
        for x in self.xs:
            if unit in x:
                x.remove(unit)
            
            if x.count == 0:
                self.xs.remove(x)

