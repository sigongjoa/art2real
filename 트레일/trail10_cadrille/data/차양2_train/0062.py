import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-89,7),(-7,-69)).segment((7,-69)).segment((89,7)).segment((74,38)).segment((0,-38)).segment((-74,38)).close().assemble().finalize().extrude(30).cut(cq.Workplane('XY').box(8,200,18).translate((0,0,15)))