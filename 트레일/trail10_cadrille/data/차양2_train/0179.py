import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-90,5),(-13,-56)).segment((13,-56)).segment((90,5)).segment((72,41)).segment((0,-20)).segment((-72,41)).close().assemble().finalize().extrude(40).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(7,200,40).translate((0,0,20)))