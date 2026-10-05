import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-90,18),(-10,-44)).segment((10,-44)).segment((90,18)).segment((83,32)).segment((0,-30)).segment((-83,32)).close().assemble().finalize().extrude(26).cut(cq.Workplane('XY').box(3,200,20).translate((0,0,13)))