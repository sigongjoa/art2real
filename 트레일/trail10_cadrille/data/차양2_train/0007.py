import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-97,12),(-12,-51)).segment((12,-51)).segment((97,12)).segment((82,43)).segment((0,-20)).segment((-82,43)).close().assemble().finalize().extrude(40).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(5,200,30).translate((-15,0,20))).cut(cq.Workplane('XY').box(7,200,38).translate((45,0,20)))