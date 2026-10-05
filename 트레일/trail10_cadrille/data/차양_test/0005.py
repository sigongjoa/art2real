import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-94,20),(-7,-42)).segment((7,-42)).segment((94,20)).segment((86,36)).segment((0,-26)).segment((-86,36)).close().assemble().finalize().extrude(17).edges('>Z').chamfer(2).cut(cq.Workplane('XY').box(7,200,16).translate((0,0,9)))