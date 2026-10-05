import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-67,11),(-13,-47)).segment((13,-47)).segment((67,11)).segment((55,36)).segment((0,-22)).segment((-55,36)).close().assemble().finalize().extrude(27).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(7,200,26).translate((-19,0,14))).cut(cq.Workplane('XY').box(6,200,8).translate((-28,0,14)))