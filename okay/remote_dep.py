# Test that remote dependency / local dependency loading is working.
import ai
import random
import itertools
from operator import attrgetter
from collections import defaultdict
import sys
import os

# This loads the module 'okay' from filesystem or github, depending on how
# this module is loaded.
require_dependency(module_name="okay", rel_path="../okay")

AIClass = "RemoteDepAI"
EXPLORER_RATIO=4

# It kind of just sits there.
class RemoteDepAI(okay.OkayAI):
  pass
