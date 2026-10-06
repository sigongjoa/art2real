import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-90,-4),(-7,-50)).segment((7,-50)).segment((90,-4)).segment((73,31)).segment((0,-15)).segment((-73,31)).close().assemble().finalize().extrude(43).edges('>Z').chamfer(8)