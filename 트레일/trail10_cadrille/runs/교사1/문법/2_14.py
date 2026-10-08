import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-25))
w1=cq.Workplane('XY',origin=(0,0,-19))
w2=cq.Workplane('XY',origin=(0,0,-12))
w3=cq.Workplane('XY',origin=(0,0,-5))
w4=cq.Workplane('XY',origin=(0,0,5))
w5=cq.Workplane('XY',origin=(0,0,12))
w6=cq.Workplane('XY',origin=(0,0,19))
r=w0.sketch().push([(56,0),(-51,0)]).circle(78).circle(43,mode='s').finalize().extrude(6).union(w1.sketch().push([(56,0),(-51,0)]).circle(81).circle(41,mode='s').finalize().extrude(7)).union(w2.sketch().push([(56,0),(-51,0)]).circle(81).circle(35,mode='s').finalize().extrude(7)).union(w3.sketch().push([(56,0),(-51,0)]).circle(81).circle(29,mode='s').finalize().extrude(10)).union(w4.sketch().push([(56,0),(-51,0)]).circle(81).circle(35,mode='s').finalize().extrude(7)).union(w5.sketch().push([(56,0),(-51,0)]).circle(81).circle(41,mode='s').finalize().extrude(7)).union(w6.sketch().push([(56,0),(-51,0)]).circle(78).circle(43,mode='s').finalize().extrude(6)).cut(w0.sketch().segment((56,0),(146,97)).segment((146,-97)).close().assemble().reset().face(w0.sketch().segment((-51,0),(-141,97)).segment((-141,-97)).close().assemble()).push([(120,0),(-120,0)]).rect(40,200).finalize().extrude(50))