import cadquery as cq
w0=cq.Workplane('YZ',origin=(-72,0,0))
w1=cq.Workplane('ZX',origin=(0,-86,0))
w2=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((-83,-57),(83,-57)).segment((52,52)).arc((0,100),(-52,52)).close().assemble().finalize().extrude(144).cut(w1.sketch().rect(240,240).reset().face(w1.sketch().segment((-57,-66),(-57,72)).segment((52,48)).arc((100,3),(52,-42)).close().assemble(),mode='s').finalize().extrude(172)).union(w2.sketch().push([(3,0)]).circle(62).finalize().extrude(45)).cut(w2.sketch().push([(3,0)]).circle(53).finalize().extrude(60)).cut(w2.workplane(offset=60).sketch().push([(3,0)]).circle(47).finalize().extrude(60)).cut(w2.workplane(offset=120).sketch().push([(3,0)]).circle(40).finalize().extrude(40)).cut(w2.workplane(offset=160).sketch().push([(3,0)]).circle(30).finalize().extrude(25)).cut(w0.workplane(offset=-8).sketch().push([(-12,65),(12,65),(-12,30),(12,30),(-12,-10),(12,-10)]).circle(6).finalize().extrude(50))
