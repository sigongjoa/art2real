import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-88,20),(-14,-27)).segment((14,-27)).segment((88,20)).segment((79,38)).segment((0,-9)).segment((-79,38)).close().assemble().finalize().extrude(13).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(8,200,6).translate((34,0,7)))