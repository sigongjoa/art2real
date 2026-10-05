import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-61,20),(-6,-26)).segment((6,-26)).segment((61,20)).segment((52,39)).segment((0,-7)).segment((-52,39)).close().assemble().finalize().extrude(12).cut(cq.Workplane('XY').box(8,200,10).translate((0,0,6)))