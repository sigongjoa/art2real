import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-73,2),(-13,-29)).segment((13,-29)).segment((73,2)).segment((63,23)).segment((0,-8)).segment((-63,23)).close().assemble().finalize().extrude(20).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(6,200,8).translate((-33,0,10)))