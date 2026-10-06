import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-92,-1),(-10,-63)).segment((10,-63)).segment((92,-1)).segment((78,28)).segment((0,-34)).segment((-78,28)).close().assemble().finalize().extrude(44).edges('>Z').chamfer(11)