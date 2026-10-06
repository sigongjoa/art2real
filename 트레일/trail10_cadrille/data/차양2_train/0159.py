import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-92,-5),(-6,-56)).segment((6,-56)).segment((92,-5)).segment((73,34)).segment((0,-17)).segment((-73,34)).close().assemble().finalize().extrude(27).cut(cq.Workplane('XY').box(10,200,16).translate((44,0,14))).cut(cq.Workplane('XY').box(11,200,12).translate((-37,0,14)))