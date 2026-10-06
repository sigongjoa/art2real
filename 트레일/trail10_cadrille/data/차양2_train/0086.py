import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-85,25),(-17,-51)).segment((17,-51)).segment((85,25)).segment((69,58)).segment((0,-18)).segment((-69,58)).close().assemble().finalize().extrude(44).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(9,200,38).translate((-3,0,22)))