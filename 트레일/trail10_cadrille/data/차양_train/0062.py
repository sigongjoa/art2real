import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-70,5),(-5,-53)).segment((5,-53)).segment((70,5)).segment((61,23)).segment((0,-35)).segment((-61,23)).close().assemble().finalize().extrude(12).cut(cq.Workplane('XY').box(7,200,6).translate((0,0,6)))