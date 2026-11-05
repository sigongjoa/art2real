import cadquery as cq
w0=cq.Workplane('YZ',origin=(30,0,0))
w1=cq.Workplane('YZ',origin=(29,0,0))
r=w0.sketch().segment((92,32),(93,31)).segment((93,32)).close().assemble().finalize().extrude(-120).union(w0.sketch().segment((92,30),(93,30)).segment((93,31)).close().assemble().finalize().extrude(29)).union(w1.sketch().arc((100,11),(99,12),(100,13)).arc((98,13),(100,11)).assemble().finalize().extrude(-109))