import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-97,24),(-14,-62)).segment((14,-62)).segment((97,24)).segment((81,57)).segment((0,-29)).segment((-81,57)).close().assemble().finalize().extrude(32).cut(cq.Workplane('XY').box(10,200,6).translate((0,0,16)))