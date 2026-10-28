import cadquery as cq
w0=cq.Workplane('YZ',origin=(50,0,0))
w1=cq.Workplane('YZ',origin=(30,0,0))
r=w0.sketch().segment((55,1),(56,1)).arc((56,3),(55,5)).close().assemble().finalize().extrude(-120).union(w0.sketch().segment((55,20),(55,21)).arc((54,21),(55,20)).assemble().finalize().extrude(19)).union(w1.sketch().arc((-53,55),(-47,56),(-41,56)).arc((-46,58),(-53,55)).assemble().finalize().extrude(-120))