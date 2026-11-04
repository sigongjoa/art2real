import cadquery as cq
w0=cq.Workplane('YZ',origin=(31,0,0))
w1=cq.Workplane('YZ',origin=(29,0,0))
r=w0.sketch().segment((92,31),(93,31)).segment((92,32)).close().assemble().finalize().extrude(-131).union(w1.sketch().arc((92,10),(93,13),(92,16)).close().assemble().finalize().extrude(-129))