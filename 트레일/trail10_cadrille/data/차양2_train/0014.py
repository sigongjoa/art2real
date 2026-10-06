import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-96,0),(-17,-75)).segment((17,-75)).segment((96,0)).segment((77,38)).segment((0,-37)).segment((-77,38)).close().assemble().finalize().extrude(40).cut(cq.Workplane('XY').box(12,200,20).translate((32,0,20)))