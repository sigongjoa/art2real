import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-96,4),(-9,-48)).segment((9,-48)).segment((96,4)).segment((79,38)).segment((0,-14)).segment((-79,38)).close().assemble().finalize().extrude(32).edges('>Z').chamfer(10)