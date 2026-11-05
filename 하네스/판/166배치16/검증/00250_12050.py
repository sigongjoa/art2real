import cadquery as cq
w0=cq.Workplane('YZ',origin=(63,0,0))
w1=cq.Workplane('YZ',origin=(24,0,0))
r=w0.sketch().segment((100,30),(100,31)).segment((100,30)).close().assemble().finalize().extrude(-127).union(w0.sketch().segment((100,28),(100,29)).segment((100,28)).close().assemble().finalize().extrude(-121)).union(w1.sketch().arc((100,13),(99,15),(100,17)).arc((99,15),(100,13)).assemble().finalize().extrude(-104))