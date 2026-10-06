import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-89,10),(-12,-49)).segment((12,-49)).segment((89,10)).segment((76,37)).segment((0,-22)).segment((-76,37)).close().assemble().finalize().extrude(44)