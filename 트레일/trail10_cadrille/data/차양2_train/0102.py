import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-93,-4),(-11,-49)).segment((11,-49)).segment((93,-4)).segment((73,36)).segment((0,-9)).segment((-73,36)).close().assemble().finalize().extrude(40).cut(cq.Workplane('XY').box(12,200,36).translate((0,0,20)))