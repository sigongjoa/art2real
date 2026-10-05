import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-74,11),(-9,-38)).segment((9,-38)).segment((74,11)).segment((62,35)).segment((0,-14)).segment((-62,35)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(5,200,14).translate((20,0,13))).cut(cq.Workplane('XY').box(6,200,16).translate((32,0,13)))