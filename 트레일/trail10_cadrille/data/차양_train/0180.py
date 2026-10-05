import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-55,17),(-8,-47)).segment((8,-47)).segment((55,17)).segment((43,41)).segment((0,-23)).segment((-43,41)).close().assemble().finalize().extrude(24).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(5,200,18).translate((0,0,12)))