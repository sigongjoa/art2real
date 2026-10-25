import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
w1=cq.Workplane('XY',origin=(0,0,78))
r=w0.sketch().segment((29,32),(30,32)).arc((30,33),(29,32)).assemble().finalize().extrude(-200).union(w1.sketch().arc((-11,100),(-10,95),(-9,90)).arc((-1,93),(7,93)).arc((-1,95),(-11,100)).assemble().finalize().extrude(-178))