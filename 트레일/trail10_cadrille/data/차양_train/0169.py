import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-55,19),(-5,-32)).segment((5,-32)).segment((55,19)).segment((41,47)).segment((0,-4)).segment((-41,47)).close().assemble().finalize().extrude(26)