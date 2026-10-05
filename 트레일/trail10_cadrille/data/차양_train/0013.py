import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-77,-3),(-6,-34)).segment((6,-34)).segment((77,-3)).segment((69,13)).segment((0,-18)).segment((-69,13)).close().assemble().finalize().extrude(18).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(6,200,16).translate((-2,0,9)))