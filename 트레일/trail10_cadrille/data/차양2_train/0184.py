import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-94,25),(-6,-67)).segment((6,-67)).segment((94,25)).segment((79,55)).segment((0,-37)).segment((-79,55)).close().assemble().finalize().extrude(31).cut(cq.Workplane('XY').box(11,200,12).translate((0,0,16)))