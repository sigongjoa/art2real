import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-98,22),(-16,-56)).segment((16,-56)).segment((98,22)).segment((78,62)).segment((0,-16)).segment((-78,62)).close().assemble().finalize().extrude(35).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(9,200,34).translate((-45,0,18)))