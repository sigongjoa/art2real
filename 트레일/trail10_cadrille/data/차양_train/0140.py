import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-72,8),(-13,-48)).segment((13,-48)).segment((72,8)).segment((64,24)).segment((0,-32)).segment((-64,24)).close().assemble().finalize().extrude(14).cut(cq.Workplane('XY').box(7,200,12).translate((21,0,7)))