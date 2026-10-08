import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-24,0))
w1=cq.Workplane('XY',origin=(0,0,-100))
w2=cq.Workplane('YZ',origin=(40,0,0))
w3=cq.Workplane('YZ',origin=(-70,0,0))
w4=cq.Workplane('YZ',origin=(-18,0,0))
w5=cq.Workplane('XY',origin=(0,0,38))
r=w0.sketch().segment((-100,44),(-37,86)).segment((-20,95)).segment((0,98)).segment((100,98)).segment((100,78)).segment((72,49)).segment((100,18)).segment((100,-18)).segment((72,-49)).segment((100,-78)).segment((100,-98)).segment((0,-98)).segment((-20,-95)).segment((-37,-86)).segment((-100,-44)).close().assemble().finalize().extrude(52).cut(w5.sketch().segment((-61,0),(61,0)).segment((82,28)).segment((-82,28)).close().assemble().finalize().extrude(62)).cut(w1.sketch().segment((55,-20),(100,15)).segment((100,-30)).segment((55,-30)).close().assemble().reset().face(w1.sketch().segment((-55,-20),(-100,15)).segment((-100,-30)).segment((-55,-30)).close().assemble()).finalize().extrude(200)).union(w2.sketch().segment((28,-37),(72,2)).segment((72,38)).segment((28,38)).close().assemble().finalize().extrude(30)).union(w3.sketch().segment((28,-37),(72,2)).segment((72,38)).segment((28,38)).close().assemble().finalize().extrude(30)).union(w4.sketch().segment((0,100),(-50,100)).segment((-72,41)).segment((-42,28)).segment((-42,0)).segment((0,0)).close().assemble().finalize().extrude(35)).union(w1.workplane(offset=76).moveTo(0,-20).box(62,30,19))
