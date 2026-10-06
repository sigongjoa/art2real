import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-97,-3),(-13,-66)).segment((13,-66)).segment((97,-3)).segment((78,36)).segment((0,-27)).segment((-78,36)).close().assemble().finalize().extrude(28).edges('>Z').chamfer(10).cut(cq.Workplane('XY').box(7,200,14).translate((-25,0,14)))