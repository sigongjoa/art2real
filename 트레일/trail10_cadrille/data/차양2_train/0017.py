import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-98,25),(-8,-51)).segment((8,-51)).segment((98,25)).segment((79,63)).segment((0,-13)).segment((-79,63)).close().assemble().finalize().extrude(43).edges('>Z').chamfer(11).cut(cq.Workplane('XY').box(8,200,42).translate((0,0,22)))