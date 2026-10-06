import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-86,-5),(-8,-70)).segment((8,-70)).segment((86,-5)).segment((73,21)).segment((0,-44)).segment((-73,21)).close().assemble().finalize().extrude(38).cut(cq.Workplane('XY').box(6,200,22).translate((-24,0,19)))