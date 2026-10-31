w0=cq.Workplane('YZ', 100, 0, 0))
w1=cq.Workplane('YZ', 0,0))
r=w0.workplane(offset=10/2).cylinder(10,10).union(w0.workplane(offset=10/2).cylinder(10,10)).union(w1.sketch().arc((-26,0),(-18,1),(-10,0)).arc((-18,1),(-26,0)).assemble().finalize().extrude(100))