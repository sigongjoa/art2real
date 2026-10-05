import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-66,0))
r=w0.sketch().segment((37,46),(74,84)).segment((64,96)).close().assemble().finalize().extrude(29).union(w0.sketch().segment((-74,-70),(-51,-89)).arc((-59,-71),(-74,-57)).close().assemble().finalize().extrude(133))