import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-90,20),(-11,-35)).segment((11,-35)).segment((90,20)).segment((79,42)).segment((0,-13)).segment((-79,42)).close().assemble().finalize().extrude(20)