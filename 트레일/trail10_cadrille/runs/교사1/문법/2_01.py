import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-43))
w1=cq.Workplane('ZX',origin=(0,-46,0))
r=w0.sketch().segment((-64,-100),(30,-100)).segment((30,-22)).segment((-64,-22)).close().assemble().push([(-17,-68)]).circle(24,mode='s').push([(-17,-92)]).rect(24,18,mode='s').finalize().extrude(46).union(w0.sketch().segment((-68,-22),(18,-22)).segment((18,10)).segment((-68,10)).close().assemble().finalize().extrude(26)).union(w0.sketch().push([(-61,30)]).rect(20,60).push([(-39,40)]).rect(20,76).push([(-17,50)]).rect(21,92).push([(6,46)]).rect(20,84).finalize().extrude(23)).union(w1.sketch().segment((-15,10),(-35,28)).segment((28,75)).segment((42,60)).close().assemble().finalize().extrude(32))
