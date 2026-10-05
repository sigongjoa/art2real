import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-11))
r=w0.sketch().segment((-71,10),(-5,-29)).segment((5,-29)).segment((71,10)).segment((58,36)).segment((0,-3)).segment((-58,36)).close().assemble().finalize().extrude(22).cut(cq.Workplane('XY').box(6,200,6).translate((-25,0,11)))