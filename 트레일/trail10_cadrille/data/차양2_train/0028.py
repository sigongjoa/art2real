import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-85,20),(-17,-45)).segment((17,-45)).segment((85,20)).segment((69,53)).segment((0,-12)).segment((-69,53)).close().assemble().finalize().extrude(43).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(6,200,26).translate((0,0,22)))