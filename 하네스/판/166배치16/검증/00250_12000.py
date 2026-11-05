import cadquery as cq
w0=cq.Workplane('YZ',origin=(29,0,0))
w1=cq.Workplane('YZ',origin=(30,0,0))
r=w0.sketch().segment((26,1),(26,3)).arc((25,2),(26,1)).assemble().finalize().extrude(-100).union(w0.sketch().segment((26,1),(26,3)).arc((25,2),(26,1)).assemble().finalize().extrude(61)).union(w1.sketch().arc((-26,55),(-15,75),(2,91)).segment((-26,91)).close().assemble().finalize().extrude(-100))