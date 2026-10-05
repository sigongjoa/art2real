import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-90,8),(-14,-46)).segment((14,-46)).segment((90,8)).segment((77,35)).segment((0,-19)).segment((-77,35)).close().assemble().finalize().extrude(13).cut(cq.Workplane('XY').box(8,200,6).translate((0,0,7)))