import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-90,5),(-10,-65)).segment((10,-65)).segment((90,5)).segment((76,34)).segment((0,-36)).segment((-76,34)).close().assemble().finalize().extrude(39).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(6,200,14).translate((12,0,20)))