import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-93,-4),(-11,-49)).segment((11,-49)).segment((93,-4)).segment((80,22)).segment((0,-23)).segment((-80,22)).close().assemble().finalize().extrude(24).cut(cq.Workplane('XY').box(8,200,20).translate((-21,0,12)))