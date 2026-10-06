import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-95,11),(-6,-64)).segment((6,-64)).segment((95,11)).segment((81,39)).segment((0,-36)).segment((-81,39)).close().assemble().finalize().extrude(34).cut(cq.Workplane('XY').box(12,200,34).translate((32,0,17)))