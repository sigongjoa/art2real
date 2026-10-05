import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-7))
r=w0.sketch().segment((-84,20),(-5,-51)).segment((5,-51)).segment((84,20)).segment((70,48)).segment((0,-23)).segment((-70,48)).close().assemble().finalize().extrude(13).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(7,200,12).translate((-30,0,7)))