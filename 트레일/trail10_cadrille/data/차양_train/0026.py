import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-72,4),(-12,-36)).segment((12,-36)).segment((72,4)).segment((61,27)).segment((0,-13)).segment((-61,27)).close().assemble().finalize().extrude(13).edges('>Z').chamfer(4)