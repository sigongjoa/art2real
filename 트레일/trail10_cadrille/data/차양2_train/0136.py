import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-89,20),(-15,-70)).segment((15,-70)).segment((89,20)).segment((76,47)).segment((0,-43)).segment((-76,47)).close().assemble().finalize().extrude(35).cut(cq.Workplane('XY').box(10,200,10).translate((-39,0,18)))