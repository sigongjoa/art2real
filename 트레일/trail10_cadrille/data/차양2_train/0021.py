import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-15))
r=w0.sketch().segment((-96,-3),(-8,-46)).segment((8,-46)).segment((96,-3)).segment((82,25)).segment((0,-18)).segment((-82,25)).close().assemble().finalize().extrude(29).cut(cq.Workplane('XY').box(10,200,24).translate((0,0,15)))