import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-65,19),(-9,-28)).segment((9,-28)).segment((65,19)).segment((58,33)).segment((0,-14)).segment((-58,33)).close().assemble().finalize().extrude(23).cut(cq.Workplane('XY').box(8,200,6).translate((0,0,12)))