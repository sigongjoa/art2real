import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-86,18),(-14,-63)).segment((14,-63)).segment((86,18)).segment((74,42)).segment((0,-39)).segment((-74,42)).close().assemble().finalize().extrude(33).cut(cq.Workplane('XY').box(10,200,24).translate((0,0,17)))