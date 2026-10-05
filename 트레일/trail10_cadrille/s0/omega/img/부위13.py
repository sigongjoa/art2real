import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,89,0))
w1=cq.Workplane('YZ',origin=(30,0,0))
r=w0.sketch().segment((-43,-26),(-39,-30)).segment((43,10)).segment((42,12)).close().assemble().finalize().extrude(-159).union(w0.sketch().segment((-43,-29),(-29,-49)).segment((-1,-29)).close().assemble().finalize().extrude(11)).union(w1.sketch().arc((-92,-43),(-80,-50),(-67,-54)).arc((-65,-51),(-63,-54)).arc((-28,-49),(1,-27)).segment((1,-43)).close().assemble().finalize().extrude(10))