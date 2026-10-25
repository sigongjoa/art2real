import cadquery as cq
w0=cq.Workplane('YZ',origin=(39,0,0))
w1=cq.Workplane('XY',origin=(0,0,39))
r=w0.sketch().segment((59,45),(60,45)).arc((60,46),(59,46)).close().assemble().finalize().extrude(-109).union(w1.sketch().arc((100,-24),(99,-23),(100,-22)).arc((99,-23),(100,-24)).assemble().finalize().extrude(-101))