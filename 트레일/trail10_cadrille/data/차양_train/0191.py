import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-62,20),(-7,-27)).segment((7,-27)).segment((62,20)).segment((49,46)).segment((0,-1)).segment((-49,46)).close().assemble().finalize().extrude(19).cut(cq.Workplane('XY').box(4,200,16).translate((24,0,10))).cut(cq.Workplane('XY').box(8,200,10).translate((-29,0,10)))