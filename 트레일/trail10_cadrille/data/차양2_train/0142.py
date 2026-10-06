import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-86,18),(-12,-66)).segment((12,-66)).segment((86,18)).segment((74,43)).segment((0,-41)).segment((-74,43)).close().assemble().finalize().extrude(38).edges('>Z').chamfer(7).cut(cq.Workplane('XY').box(10,200,18).translate((6,0,19)))