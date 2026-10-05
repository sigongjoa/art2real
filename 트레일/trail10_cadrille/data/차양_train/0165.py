import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-90,5),(-8,-35)).segment((8,-35)).segment((90,5)).segment((76,33)).segment((0,-7)).segment((-76,33)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(3,200,16).translate((-41,0,13)))