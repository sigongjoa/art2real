import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-75,8),(-10,-29)).segment((10,-29)).segment((75,8)).segment((62,34)).segment((0,-3)).segment((-62,34)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(7,200,14).translate((0,0,8)))