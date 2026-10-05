import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-66,18),(-8,-45)).segment((8,-45)).segment((66,18)).segment((53,45)).segment((0,-18)).segment((-53,45)).close().assemble().finalize().extrude(13).cut(cq.Workplane('XY').box(8,200,8).translate((31,0,7))).cut(cq.Workplane('XY').box(5,200,12).translate((5,0,7)))