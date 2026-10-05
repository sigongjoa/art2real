import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-65,7),(-8,-26)).segment((8,-26)).segment((65,7)).segment((54,30)).segment((0,-3)).segment((-54,30)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(4,200,18).translate((0,0,12)))