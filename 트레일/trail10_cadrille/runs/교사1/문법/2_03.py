import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-13,0))
w1=cq.Workplane('YZ',origin=(73,0,0))
w2=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().arc((-60,-100),(-64,-99),(-65,-95)).segment((-65,95)).arc((-64,99),(-60,100)).segment((52,100)).segment((52,73)).segment((-35,73)).arc((-40,71),(-42,65)).segment((-42,-65)).arc((-40,-71),(-35,-73)).segment((52,-73)).segment((52,-100)).close().assemble().push([(-42,-60),(-42,-49),(-42,-38),(-42,-27),(-42,-16),(-42,-5),(-42,5),(-42,16),(-42,27),(-42,38),(-42,49),(-42,60)]).rect(2,3,mode='s').push([(52,-86),(52,86)]).circle(3,mode='s').finalize().extrude(26).union(w1.sketch().push([(0,52)]).circle(13).circle(3,mode='s').finalize().extrude(27)).union(w2.sketch().push([(0,52)]).circle(13).circle(3,mode='s').finalize().extrude(27))
