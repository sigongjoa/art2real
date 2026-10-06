import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-93,6),(-7,-75)).segment((7,-75)).segment((93,6)).segment((79,35)).segment((0,-46)).segment((-79,35)).close().assemble().finalize().extrude(25).cut(cq.Workplane('XY').box(10,200,14).translate((0,0,13)))