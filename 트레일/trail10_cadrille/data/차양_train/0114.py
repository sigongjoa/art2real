import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-95,5),(-13,-52)).segment((13,-52)).segment((95,5)).segment((86,23)).segment((0,-34)).segment((-86,23)).close().assemble().finalize().extrude(26).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(3,200,14).translate((0,0,13)))