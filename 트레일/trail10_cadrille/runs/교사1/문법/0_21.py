import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-2))
r=w0.sketch().push([(0,-2)]).rect(7,197).push([(0,97)]).circle(3).push([(0,-2)]).rect(4,197,mode='s').push([(0,97)]).circle(2,mode='s').finalize().extrude(4)
