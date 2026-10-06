import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-94,10),(-14,-47)).segment((14,-47)).segment((94,10)).segment((81,36)).segment((0,-21)).segment((-81,36)).close().assemble().finalize().extrude(38).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(8,200,14).translate((-1,0,19)))