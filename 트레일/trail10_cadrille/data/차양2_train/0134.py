import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-97,-4),(-17,-66)).segment((17,-66)).segment((97,-4)).segment((85,20)).segment((0,-42)).segment((-85,20)).close().assemble().finalize().extrude(36).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(6,200,20).translate((20,0,18)))