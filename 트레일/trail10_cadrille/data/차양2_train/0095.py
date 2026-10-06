import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-86,14),(-14,-58)).segment((14,-58)).segment((86,14)).segment((74,39)).segment((0,-33)).segment((-74,39)).close().assemble().finalize().extrude(30).edges('>Z').chamfer(10)