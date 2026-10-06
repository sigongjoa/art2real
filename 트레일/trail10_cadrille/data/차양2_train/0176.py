import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-85,-4),(-7,-51)).segment((7,-51)).segment((85,-4)).segment((72,23)).segment((0,-24)).segment((-72,23)).close().assemble().finalize().extrude(31).cut(cq.Workplane('XY').box(5,200,28).translate((-12,0,16)))