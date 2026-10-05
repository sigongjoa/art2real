import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-63,12),(-6,-52)).segment((6,-52)).segment((63,12)).segment((51,37)).segment((0,-27)).segment((-51,37)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(3,200,14).translate((0,0,8)))