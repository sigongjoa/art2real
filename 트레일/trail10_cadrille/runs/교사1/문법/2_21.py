import cadquery as cq
w0=cq.Workplane('YZ',origin=(-72,0,0))
w2=cq.Workplane('YZ',origin=(-51,0,0))
w3=cq.Workplane('XY',origin=(0,0,-95))
w4=cq.Workplane('XY',origin=(0,0,-38))
w5=cq.Workplane('YZ',origin=(72,0,0))
w6=cq.Workplane('YZ',origin=(-83,0,0))
r=w0.sketch().segment((-100,-14),(-25,-89)).segment((42,-89)).segment((99,-32)).segment((99,22)).segment((97,29)).segment((37,88)).segment((32,89)).segment((-19,86)).segment((-42,65)).segment((-27,35)).segment((-35,28)).segment((-56,27)).segment((-60,26)).close().assemble().finalize().extrude(144).cut(w2.sketch().segment((-38,61),(-2,24)).segment((-22,4)).segment((-15,-2)).segment((-38,-25)).segment((-59,-17)).segment((-70,-27)).segment((-68,-30)).segment((-47,-32)).segment((-25,-54)).segment((-13,-65)).segment((12,-89)).segment((12,-100)).segment((-120,-100)).segment((-120,70)).segment((-45,70)).close().assemble().finalize().extrude(102)).cut(w3.sketch().push([(0,-2)]).circle(23).finalize().extrude(57)).cut(w4.sketch().push([(0,-2)]).circle(15).finalize().extrude(19)).union(w5.sketch().segment((35,-17),(-6,25)).segment((-47,-14)).segment((-6,-56)).close().assemble().finalize().extrude(11)).union(w6.sketch().segment((35,-17),(-6,25)).segment((-47,-14)).segment((-6,-56)).close().assemble().finalize().extrude(11))