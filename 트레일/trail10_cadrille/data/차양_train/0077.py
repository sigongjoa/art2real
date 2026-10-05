import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-90,11),(-9,-45)).segment((9,-45)).segment((90,11)).segment((83,25)).segment((0,-31)).segment((-83,25)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(3,200,14).translate((39,0,14))).cut(cq.Workplane('XY').box(8,200,8).translate((33,0,14)))