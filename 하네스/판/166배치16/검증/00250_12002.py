import cadquery as cq
w0=cq.Workplane('YZ',origin=(50,0,0))
w1=cq.Workplane('YZ',origin=(30,0,0))
r=w0.sketch().segment((53,1),(53,2)).arc((52,3),(53,4)).segment((53,5)).arc((52,3),(53,1)).assemble().finalize().extrude(-109).union(w0.sketch().segment((53,1),(53,2)).arc((52,3),(53,5)).segment((53,6)).arc((52,3),(53,1)).assemble().finalize().extrude(19)).union(w1.sketch().arc((-53,55),(-46,76),(-33,95)).arc((-46,76),(-53,55)).assemble().finalize().extrude(-120))