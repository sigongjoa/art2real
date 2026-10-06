import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-94,17),(-12,-46)).segment((12,-46)).segment((94,17)).segment((78,49)).segment((0,-14)).segment((-78,49)).close().assemble().finalize().extrude(31).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(8,200,26).translate((0,0,16)))