import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-84,-5),(-7,-44)).segment((7,-44)).segment((84,-5)).segment((71,21)).segment((0,-18)).segment((-71,21)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(3)