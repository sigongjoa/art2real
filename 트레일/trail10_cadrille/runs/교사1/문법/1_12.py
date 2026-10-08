import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-41))
r=w0.sketch().push([(2,-72)]).circle(46).push([(6,-15)]).rect(92,70).reset().push([(2,-68)]).circle(24,mode='s').push([(3,-95)]).rect(22,20,mode='s').finalize().extrude(48).union(w0.sketch().push([(-19,30)]).rect(20,140).finalize().extrude(26)).union(w0.workplane(offset=60).moveTo(25,-2).box(54,66,26)).union(w0.workplane(offset=63).moveTo(-25,-20).box(40,30,32))
