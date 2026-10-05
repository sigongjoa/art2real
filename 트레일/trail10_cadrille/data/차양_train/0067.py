import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-74,7),(-5,-49)).segment((5,-49)).segment((74,7)).segment((66,24)).segment((0,-32)).segment((-66,24)).close().assemble().finalize().extrude(16).cut(cq.Workplane('XY').box(4,200,12).translate((0,0,8)))