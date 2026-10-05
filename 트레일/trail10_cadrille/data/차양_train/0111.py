import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-63,19),(-7,-45)).segment((7,-45)).segment((63,19)).segment((50,45)).segment((0,-19)).segment((-50,45)).close().assemble().finalize().extrude(20).cut(cq.Workplane('XY').box(3,200,10).translate((10,0,10))).cut(cq.Workplane('XY').box(8,200,14).translate((-15,0,10)))