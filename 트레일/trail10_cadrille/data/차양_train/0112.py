import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-69,15),(-4,-27)).segment((4,-27)).segment((69,15)).segment((58,37)).segment((0,-5)).segment((-58,37)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(7,200,26).translate((29,0,14)))