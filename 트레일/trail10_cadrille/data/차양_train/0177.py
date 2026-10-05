import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-58,7),(-9,-34)).segment((9,-34)).segment((58,7)).segment((51,21)).segment((0,-20)).segment((-51,21)).close().assemble().finalize().extrude(20).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(3,200,8).translate((-8,0,10)))