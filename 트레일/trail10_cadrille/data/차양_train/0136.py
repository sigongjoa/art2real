import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-8))
r=w0.sketch().segment((-89,2),(-6,-50)).segment((6,-50)).segment((89,2)).segment((79,22)).segment((0,-30)).segment((-79,22)).close().assemble().finalize().extrude(15).edges('>Z').chamfer(3)