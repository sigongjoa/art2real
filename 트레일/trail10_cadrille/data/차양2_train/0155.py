import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-93,18),(-13,-48)).segment((13,-48)).segment((93,18)).segment((77,50)).segment((0,-16)).segment((-77,50)).close().assemble().finalize().extrude(30).cut(cq.Workplane('XY').box(10,200,12).translate((-5,0,15)))