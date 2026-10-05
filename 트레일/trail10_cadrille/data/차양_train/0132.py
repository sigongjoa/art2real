import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-70,5),(-7,-35)).segment((7,-35)).segment((70,5)).segment((58,29)).segment((0,-11)).segment((-58,29)).close().assemble().finalize().extrude(24).cut(cq.Workplane('XY').box(8,200,12).translate((0,0,12)))