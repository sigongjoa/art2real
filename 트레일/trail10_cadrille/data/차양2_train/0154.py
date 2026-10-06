import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-85,8),(-14,-55)).segment((14,-55)).segment((85,8)).segment((71,37)).segment((0,-26)).segment((-71,37)).close().assemble().finalize().extrude(25).cut(cq.Workplane('XY').box(8,200,12).translate((-20,0,13))).cut(cq.Workplane('XY').box(7,200,24).translate((-29,0,13)))