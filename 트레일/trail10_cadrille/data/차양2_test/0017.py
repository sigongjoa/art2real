import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-98,20),(-6,-73)).segment((6,-73)).segment((98,20)).segment((82,52)).segment((0,-41)).segment((-82,52)).close().assemble().finalize().extrude(30).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(7,200,18).translate((0,0,15)))