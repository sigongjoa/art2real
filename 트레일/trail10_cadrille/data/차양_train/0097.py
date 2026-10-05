import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-5))
r=w0.sketch().segment((-56,-3),(-5,-53)).segment((5,-53)).segment((56,-3)).segment((42,25)).segment((0,-25)).segment((-42,25)).close().assemble().finalize().extrude(10).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(8,200,10).translate((-5,0,5)))