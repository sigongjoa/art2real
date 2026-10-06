import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-90,-5),(-18,-52)).segment((18,-52)).segment((90,-5)).segment((76,24)).segment((0,-23)).segment((-76,24)).close().assemble().finalize().extrude(40).cut(cq.Workplane('XY').box(11,200,32).translate((0,0,20)))