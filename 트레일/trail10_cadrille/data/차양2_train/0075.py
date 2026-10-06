import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-89,5),(-10,-70)).segment((10,-70)).segment((89,5)).segment((76,31)).segment((0,-44)).segment((-76,31)).close().assemble().finalize().extrude(25)