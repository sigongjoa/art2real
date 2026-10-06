import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-89,10),(-10,-53)).segment((10,-53)).segment((89,10)).segment((73,43)).segment((0,-20)).segment((-73,43)).close().assemble().finalize().extrude(39).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(10,200,16).translate((-15,0,20))).cut(cq.Workplane('XY').box(7,200,34).translate((32,0,20)))