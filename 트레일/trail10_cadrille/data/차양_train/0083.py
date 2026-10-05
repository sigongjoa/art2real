import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-83,12),(-13,-41)).segment((13,-41)).segment((83,12)).segment((71,37)).segment((0,-16)).segment((-71,37)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(4).cut(cq.Workplane('XY').box(6,200,22).translate((0,0,13)))