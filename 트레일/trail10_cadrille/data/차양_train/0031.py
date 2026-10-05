import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-71,20),(-12,-31)).segment((12,-31)).segment((71,20)).segment((60,43)).segment((0,-8)).segment((-60,43)).close().assemble().finalize().extrude(25).cut(cq.Workplane('XY').box(4,200,14).translate((0,0,13)))