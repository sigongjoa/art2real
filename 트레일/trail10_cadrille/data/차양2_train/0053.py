import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-91,8),(-11,-63)).segment((11,-63)).segment((91,8)).segment((73,44)).segment((0,-27)).segment((-73,44)).close().assemble().finalize().extrude(43).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(9,200,6).translate((-15,0,22))).cut(cq.Workplane('XY').box(7,200,30).translate((6,0,22)))