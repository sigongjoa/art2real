import cadquery as cq
w0=cq.Workplane('YZ',origin=(53,0,0))
w1=cq.Workplane('YZ',origin=(21,0,0))
r=w0.sketch().segment((17,15),(21,15)).arc((20,17),(19,19)).close().assemble().finalize().extrude(-153).union(w0.sketch().segment((19,15),(21,15)).arc((20,17),(19,19)).close().assemble().finalize().extrude(-107)).union(w1.sketch().arc((19,15),(20,17),(21,19)).segment((19,19)).close().assemble().finalize().extrude(7))