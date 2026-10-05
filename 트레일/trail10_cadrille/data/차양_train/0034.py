import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-70,-5),(-7,-32)).segment((7,-32)).segment((70,-5)).segment((57,21)).segment((0,-6)).segment((-57,21)).close().assemble().finalize().extrude(22).edges('>Z').chamfer(6)