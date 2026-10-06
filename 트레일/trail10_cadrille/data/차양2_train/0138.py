import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-20))
r=w0.sketch().segment((-96,21),(-16,-51)).segment((16,-51)).segment((96,21)).segment((78,57)).segment((0,-15)).segment((-78,57)).close().assemble().finalize().extrude(40).edges('>Z').chamfer(9)