import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-74,19),(-10,-43)).segment((10,-43)).segment((74,19)).segment((61,45)).segment((0,-17)).segment((-61,45)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(4)