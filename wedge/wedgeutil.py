def calc_distance(a, b):
  return ( abs(a[0] - b[0]) + abs(a[1] - b[1]) )

def closest_thing(position, things):
  closest = 100000
  found = None
  
  for t in things:
    distance = calc_distance( position, t.position )

    if distance < closest:
      closest = distance
      found = t

  return found
