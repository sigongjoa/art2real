import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-93,5),(-16,-56)).segment((16,-56)).segment((93,5)).segment((75,41)).segment((0,-20)).segment((-75,41)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(11,200,24).translate((-9,0,13)))