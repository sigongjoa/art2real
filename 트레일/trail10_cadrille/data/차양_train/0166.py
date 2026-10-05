import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-81,0),(-12,-48)).segment((12,-48)).segment((81,0)).segment((67,28)).segment((0,-20)).segment((-67,28)).close().assemble().finalize().extrude(11).cut(cq.Workplane('XY').box(4,200,6).translate((-18,0,6))).cut(cq.Workplane('XY').box(7,200,6).translate((-27,0,6)))