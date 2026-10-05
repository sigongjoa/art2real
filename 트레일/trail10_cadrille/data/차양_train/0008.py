import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-67,12),(-10,-42)).segment((10,-42)).segment((67,12)).segment((59,29)).segment((0,-25)).segment((-59,29)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(5,200,26).translate((0,0,13)))