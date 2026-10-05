import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-94,11),(-13,-48)).segment((13,-48)).segment((94,11)).segment((84,32)).segment((0,-27)).segment((-84,32)).close().assemble().finalize().extrude(23).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(5,200,22).translate((33,0,12)))