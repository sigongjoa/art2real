import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-69,15),(-4,-54)).segment((4,-54)).segment((69,15)).segment((62,29)).segment((0,-40)).segment((-62,29)).close().assemble().finalize().extrude(25).edges('>Z').chamfer(4)