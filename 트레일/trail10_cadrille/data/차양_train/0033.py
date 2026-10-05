import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-57,0),(-13,-35)).segment((13,-35)).segment((57,0)).segment((48,19)).segment((0,-16)).segment((-48,19)).close().assemble().finalize().extrude(19).edges('>Z').chamfer(2)