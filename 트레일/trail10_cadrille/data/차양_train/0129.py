import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-94,8),(-9,-38)).segment((9,-38)).segment((94,8)).segment((84,28)).segment((0,-18)).segment((-84,28)).close().assemble().finalize().extrude(19).cut(cq.Workplane('XY').box(8,200,8).translate((0,0,10)))