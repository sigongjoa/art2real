import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-86,12),(-17,-53)).segment((17,-53)).segment((86,12)).segment((73,38)).segment((0,-27)).segment((-73,38)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(12,200,20).translate((2,0,13)))