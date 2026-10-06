import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-17))
r=w0.sketch().segment((-94,23),(-12,-66)).segment((12,-66)).segment((94,23)).segment((78,56)).segment((0,-33)).segment((-78,56)).close().assemble().finalize().extrude(34).edges('>Z').chamfer(5).cut(cq.Workplane('XY').box(6,200,28).translate((-19,0,17)))