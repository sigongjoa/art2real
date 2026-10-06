import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-90,2),(-7,-70)).segment((7,-70)).segment((90,2)).segment((78,27)).segment((0,-45)).segment((-78,27)).close().assemble().finalize().extrude(43).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(5,200,10).translate((0,0,22)))