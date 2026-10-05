import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-58,6),(-6,-47)).segment((6,-47)).segment((58,6)).segment((47,29)).segment((0,-24)).segment((-47,29)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(6,200,10).translate((0,0,14)))