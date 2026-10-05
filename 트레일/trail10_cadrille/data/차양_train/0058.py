import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-86,2),(-14,-48)).segment((14,-48)).segment((86,2)).segment((74,26)).segment((0,-24)).segment((-74,26)).close().assemble().finalize().extrude(19).cut(cq.Workplane('XY').box(4,200,16).translate((37,0,10))).cut(cq.Workplane('XY').box(5,200,18).translate((7,0,10)))