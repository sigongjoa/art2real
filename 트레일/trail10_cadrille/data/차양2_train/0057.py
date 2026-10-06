import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-95,-5),(-14,-59)).segment((14,-59)).segment((95,-5)).segment((81,24)).segment((0,-30)).segment((-81,24)).close().assemble().finalize().extrude(29).cut(cq.Workplane('XY').box(9,200,24).translate((33,0,15))).cut(cq.Workplane('XY').box(8,200,22).translate((-10,0,15)))