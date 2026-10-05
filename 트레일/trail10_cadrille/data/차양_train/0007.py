import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-57,17),(-13,-34)).segment((13,-34)).segment((57,17)).segment((44,44)).segment((0,-7)).segment((-44,44)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(4,200,6).translate((0,0,14)))