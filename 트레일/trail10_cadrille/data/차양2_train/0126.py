import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-95,-3),(-8,-52)).segment((8,-52)).segment((95,-3)).segment((81,26)).segment((0,-23)).segment((-81,26)).close().assemble().finalize().extrude(36).edges('>Z').chamfer(8).cut(cq.Workplane('XY').box(5,200,18).translate((-18,0,18))).cut(cq.Workplane('XY').box(6,200,20).translate((41,0,18)))