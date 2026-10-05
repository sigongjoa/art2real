import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-92,7),(-13,-38)).segment((13,-38)).segment((92,7)).segment((83,26)).segment((0,-19)).segment((-83,26)).close().assemble().finalize().extrude(28)