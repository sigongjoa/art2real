import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-87,10),(-10,-53)).segment((10,-53)).segment((87,10)).segment((80,25)).segment((0,-38)).segment((-80,25)).close().assemble().finalize().extrude(26).cut(cq.Workplane('XY').box(5,200,20).translate((-39,0,13))).cut(cq.Workplane('XY').box(4,200,14).translate((-44,0,13)))