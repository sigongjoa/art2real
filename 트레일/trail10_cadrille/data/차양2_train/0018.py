import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-95,8),(-13,-73)).segment((13,-73)).segment((95,8)).segment((80,38)).segment((0,-43)).segment((-80,38)).close().assemble().finalize().extrude(27).cut(cq.Workplane('XY').box(12,200,6).translate((-11,0,14))).cut(cq.Workplane('XY').box(11,200,14).translate((-7,0,14)))