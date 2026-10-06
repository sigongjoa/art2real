import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-89,-3),(-14,-71)).segment((14,-71)).segment((89,-3)).segment((76,24)).segment((0,-44)).segment((-76,24)).close().assemble().finalize().extrude(39).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(11,200,16).translate((0,0,20)))