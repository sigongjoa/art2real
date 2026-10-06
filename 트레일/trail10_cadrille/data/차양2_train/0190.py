import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-85,-4),(-13,-73)).segment((13,-73)).segment((85,-4)).segment((68,31)).segment((0,-38)).segment((-68,31)).close().assemble().finalize().extrude(41).edges('>Z').chamfer(12)