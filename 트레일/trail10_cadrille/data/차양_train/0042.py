import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-94,2),(-4,-27)).segment((4,-27)).segment((94,2)).segment((84,23)).segment((0,-6)).segment((-84,23)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(6).cut(cq.Workplane('XY').box(8,200,8).translate((40,0,8))).cut(cq.Workplane('XY').box(5,200,12).translate((-17,0,8)))