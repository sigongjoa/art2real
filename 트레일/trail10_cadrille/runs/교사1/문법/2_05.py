import cadquery as cq
w0=cq.Workplane('YZ',origin=(-62,0,0))
w1=cq.Workplane('XY',origin=(0,0,-74))
w2=cq.Workplane('XY',origin=(0,0,5))
w3=cq.Workplane('XY',origin=(0,0,-30))
w4=cq.Workplane('ZX',origin=(0,-100,0))
w5=cq.Workplane('XY',origin=(0,0,20))
w6=cq.Workplane('XY',origin=(0,0,58))
r=w0.sketch().segment((-100,-74),(99,-74)).segment((92,-61)).segment((85,-61)).segment((77,-25)).segment((66,-15)).segment((52,10)).segment((35,14)).segment((0,12)).segment((-26,2)).segment((-40,-15)).segment((-62,-29)).segment((-70,-40)).segment((-82,-52)).segment((-86,-61)).segment((-91,-61)).close().assemble().finalize().extrude(124).union(w1.sketch().segment((-40,-100),(40,-100)).segment((65,-90)).segment((65,-5)).segment((76,0)).segment((76,90)).segment((-76,90)).segment((-76,0)).segment((-65,-5)).segment((-65,-90)).close().assemble().push([(0,9)]).rect(26,26,mode='s').finalize().extrude(13)).cut(w4.sketch().segment((-32,62),(-9,55)).segment((2,44)).segment((14,27)).segment((20,27)).segment((20,80)).segment((-32,80)).close().assemble().reset().face(w4.sketch().segment((-32,-62),(-9,-55)).segment((2,-44)).segment((14,-27)).segment((20,-27)).segment((20,-80)).segment((-32,-80)).close().assemble()).finalize().extrude(200)).union(w3.sketch().push([(0,9)]).circle(70).circle(56,mode='s').push([(0,-60)]).rect(60,40,mode='s').finalize().extrude(16)).union(w2.sketch().push([(0,19)]).circle(24).finalize().extrude(20)).union(w5.sketch().push([(0,19)]).circle(30).finalize().extrude(38)).union(w6.sketch().push([(0,19)]).circle(25).finalize().extrude(8)).union(w6.sketch().push([(0,19)]).circle(17).finalize().extrude(15))
