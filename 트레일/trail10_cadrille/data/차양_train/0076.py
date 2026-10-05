import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-79,15),(-8,-35)).segment((8,-35)).segment((79,15)).segment((70,33)).segment((0,-17)).segment((-70,33)).close().assemble().finalize().extrude(17).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(7,200,16).translate((0,0,9)))