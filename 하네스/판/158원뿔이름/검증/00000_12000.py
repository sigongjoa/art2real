import cadquery as cq
w0=cq.Workplane('YZ',origin=(29,0,0))
w1=cq.Workplane('YZ',origin=(30,0,0))
r=w0.sketch().segment((18,15),(20,15)).arc((21,17),(22,15)).segment((24,15)).segment((24,18)).segment((18,18)).close().assemble().finalize().extrude(-100).union(w1.sketch().arc((19,33),(21,36),(24,38)).arc((22,40),(20,42)).arc((19,38),(19,33)).assemble().finalize().extrude(70))