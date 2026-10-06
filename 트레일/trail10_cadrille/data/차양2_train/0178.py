import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-90,0),(-9,-74)).segment((9,-74)).segment((90,0)).segment((77,27)).segment((0,-47)).segment((-77,27)).close().assemble().finalize().extrude(26).cut(cq.Workplane('XY').box(9,200,16).translate((-10,0,13))).cut(cq.Workplane('XY').box(11,200,20).translate((2,0,13)))