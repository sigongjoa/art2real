import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-87,14),(-7,-46)).segment((7,-46)).segment((87,14)).segment((67,54)).segment((0,-6)).segment((-67,54)).close().assemble().finalize().extrude(29).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(9,200,22).translate((-12,0,15)))