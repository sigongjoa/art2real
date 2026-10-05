import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-57,4),(-13,-51)).segment((13,-51)).segment((57,4)).segment((50,18)).segment((0,-37)).segment((-50,18)).close().assemble().finalize().extrude(10).edges('>Z').chamfer(2)