import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-90,5),(-9,-50)).segment((9,-50)).segment((90,5)).segment((74,38)).segment((0,-17)).segment((-74,38)).close().assemble().finalize().extrude(34).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(8,200,18).translate((0,0,17)))