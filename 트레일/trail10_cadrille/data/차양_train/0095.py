import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-90,11),(-12,-34)).segment((12,-34)).segment((90,11)).segment((80,31)).segment((0,-14)).segment((-80,31)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(4,200,22).translate((0,0,13)))