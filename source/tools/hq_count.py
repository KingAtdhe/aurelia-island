import sys; sys.path.insert(0, '/home/claude/aurelia_in/aurelia-handoff/blender')
import bpy, isle_props as KP, isle_houses, isle_props_hq as HQ
HQ.register()
lib = KP.build(names=[k + '_hq' for k in HQ.HQ])
for k, e in lib.items(): print('%-16s LOD0 %6d  LOD1 %6d' % (k, e['t0'], e['t1']))
