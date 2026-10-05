import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-93,11),(-8,-51)).segment((8,-51)).segment((93,11)).segment((83,31)).segment((0,-31)).segment((-83,31)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(3,200,12).translate((0,0,8)))