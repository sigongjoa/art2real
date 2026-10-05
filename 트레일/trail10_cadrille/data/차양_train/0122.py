import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-68,20),(-9,-40)).segment((9,-40)).segment((68,20)).segment((55,47)).segment((0,-13)).segment((-55,47)).close().assemble().finalize().extrude(21).cut(cq.Workplane('XY').box(6,200,20).translate((0,0,11)))