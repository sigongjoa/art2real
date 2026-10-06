import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-91,25),(-12,-62)).segment((12,-62)).segment((91,25)).segment((71,65)).segment((0,-22)).segment((-71,65)).close().assemble().finalize().extrude(43).cut(cq.Workplane('XY').box(7,200,38).translate((0,0,22)))