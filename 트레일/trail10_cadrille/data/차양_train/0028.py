import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-67,20),(-10,-32)).segment((10,-32)).segment((67,20)).segment((56,43)).segment((0,-9)).segment((-56,43)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(3).cut(cq.Workplane('XY').box(3,200,12).translate((0,0,8)))