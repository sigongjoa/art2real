import cadquery as cq
w0=cq.Workplane('YZ',origin=(29,0,0))
w1=cq.Workplane('XY',origin=(0,0,39))
r=w0.sketch().segment((-53,95),(-52,95)).segment((-52,94)).arc((-51,97),(-53,95)).assemble().finalize().extrude(-66).union(w1.sketch().segment((29,-29),(29,-28)).arc((27,-19),(29,-10)).segment((29,-9)).arc((27,-19),(29,-29)).assemble().finalize().extrude(-139))