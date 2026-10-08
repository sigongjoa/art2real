import cadquery as cq
w0=cq.Workplane('YZ',origin=(-75,0,0))
w1=cq.Workplane('ZX',origin=(0,-100,0))
w2=cq.Workplane('XY',origin=(0,0,-73))
w3=cq.Workplane('YZ',origin=(-40,0,0))
w4=cq.Workplane('XY',origin=(0,0,74))
w5=cq.Workplane('ZX',origin=(0,10,0))
r=w0.sketch().segment((-77,-91),(-62,-91)).segment((-62,-60)).segment((-52,-46)).segment((-52,1)).segment((-56,50)).segment((-40,74)).segment((-40,91)).segment((-60,91)).segment((-75,80)).segment((-100,50)).segment((-100,10)).segment((-77,-40)).close().assemble().finalize().extrude(150).cut(w1.sketch().segment((-60,-75),(-72,-60)).segment((-80,-20)).segment((-91,0)).segment((-80,20)).segment((-72,60)).segment((-60,75)).segment((-95,80)).segment((-95,-80)).close().assemble().finalize().extrude(200)).cut(w2.sketch().segment((-76,-61),(0,-101)).segment((-76,-101)).close().assemble().reset().face(w2.sketch().segment((76,-61),(0,-101)).segment((76,-101)).close().assemble()).finalize().extrude(200)).union(w2.sketch().segment((-75,14),(75,14)).segment((75,39)).segment((26,51)).segment((-26,51)).segment((-75,39)).close().assemble().push([(0,14)]).rect(24,30,mode='s').finalize().extrude(103)).cut(w5.sketch().push([(-80,0)]).circle(44).finalize().extrude(60)).union(w3.sketch().segment((14,-7),(46,1)).segment((61,12)).segment((73,28)).segment((100,58)).segment((67,75)).segment((43,78)).segment((17,73)).segment((15,91)).segment((2,91)).segment((2,9)).segment((14,9)).close().assemble().finalize().extrude(80)).union(w4.sketch().push([(0,-15)]).rect(106,60).rect(72,42,mode='s').finalize().extrude(17))
