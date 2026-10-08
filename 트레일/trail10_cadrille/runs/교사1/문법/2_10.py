import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
w1=cq.Workplane('XY',origin=(0,0,-45))
w2=cq.Workplane('ZX',origin=(0,-40,0))
w3=cq.Workplane('XY',origin=(0,0,40))
w4=cq.Workplane('XY',origin=(0,0,-90))
w5=cq.Workplane('XY',origin=(0,0,-78))
r=w0.sketch().push([(2,7)]).circle(30).rect(120,40,mode='s').finalize().extrude(10).union(w4.sketch().push([(2,7)]).circle(41).rect(120,40,mode='s').finalize().extrude(12)).union(w5.sketch().push([(2,7)]).circle(47).finalize().extrude(33)).union(w1.sketch().push([(2,4)]).rect(106,109).push([(2,7)]).rect(59,40,mode='s').finalize().extrude(50)).union(w1.sketch().push([(-37,7)]).rect(33,107).push([(33,-28)]).rect(30,64).finalize().extrude(93)).union(w2.sketch().segment((40,-50),(64,-50)).segment((98,-35)).segment((100,-8)).segment((100,15)).segment((84,40)).segment((48,40)).segment((48,16)).segment((72,16)).segment((76,8)).segment((76,-8)).segment((72,-19)).segment((58,-26)).segment((40,-26)).close().assemble().finalize().extrude(95)).cut(w3.sketch().push([(0,-16)]).rect(110,3).push([(0,7)]).rect(110,3).push([(0,31)]).rect(110,3).finalize().extrude(60))