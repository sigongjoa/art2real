import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-94,-4),(-13,-69)).segment((13,-69)).segment((94,-4)).segment((75,34)).segment((0,-31)).segment((-75,34)).close().assemble().finalize().extrude(35).edges('>Z').chamfer(12).cut(cq.Workplane('XY').box(7,200,18).translate((-5,0,18)))