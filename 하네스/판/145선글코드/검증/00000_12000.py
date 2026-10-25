import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,38))
w1=cq.Workplane('XY',origin=(0,0,56))
r=w0.sketch().segment((39,31),(40,31)).arc((40,32),(39,32)).close().assemble().finalize().extrude(-118).union(w1.sketch().arc((39,1),(40,1),(40,2)).segment((40,3)).close().assemble().finalize().extrude(-156))