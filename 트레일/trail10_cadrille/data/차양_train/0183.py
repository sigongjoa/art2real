import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-95,-2),(-7,-40)).segment((7,-40)).segment((95,-2)).segment((84,20)).segment((0,-18)).segment((-84,20)).close().assemble().finalize().extrude(18).edges('>Z').chamfer(3)