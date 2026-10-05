import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-95,11),(-4,-44)).segment((4,-44)).segment((95,11)).segment((87,27)).segment((0,-28)).segment((-87,27)).close().assemble().finalize().extrude(20).cut(cq.Workplane('XY').box(6,200,16).translate((32,0,10)))