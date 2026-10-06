import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-90,8),(-17,-62)).segment((17,-62)).segment((90,8)).segment((75,38)).segment((0,-32)).segment((-75,38)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(9,200,16).translate((-36,0,21)))