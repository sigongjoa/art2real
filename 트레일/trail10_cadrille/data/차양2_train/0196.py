import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-98,17),(-6,-60)).segment((6,-60)).segment((98,17)).segment((83,48)).segment((0,-29)).segment((-83,48)).close().assemble().finalize().extrude(44).edges('>Z').chamfer(6)