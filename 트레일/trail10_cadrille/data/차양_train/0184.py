import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-61,11),(-12,-44)).segment((12,-44)).segment((61,11)).segment((50,33)).segment((0,-22)).segment((-50,33)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(2)