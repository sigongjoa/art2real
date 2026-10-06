import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-94,15),(-9,-52)).segment((9,-52)).segment((94,15)).segment((79,46)).segment((0,-21)).segment((-79,46)).close().assemble().finalize().extrude(36).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(5,200,24).translate((-1,0,18)))