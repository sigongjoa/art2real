import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-94,7),(-10,-73)).segment((10,-73)).segment((94,7)).segment((79,37)).segment((0,-43)).segment((-79,37)).close().assemble().finalize().extrude(27)