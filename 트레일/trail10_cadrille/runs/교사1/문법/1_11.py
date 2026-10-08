import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-67))
w1=cq.Workplane('YZ',origin=(-96,0,0))
w2=cq.Workplane('XY',origin=(0,0,-82))
w3=cq.Workplane('ZX',origin=(0,-62,0))
r=w0.sketch().segment((-89,-57),(89,-57)).segment((89,30)).segment((0,61)).segment((-89,30)).close().assemble().finalize().extrude(77).union(w1.sketch().push([(-3,8)]).circle(53).finalize().extrude(192)).union(w2.sketch().push([(0,5)]).circle(46).circle(30,mode='s').finalize().extrude(15)).union(w0.workplane(offset=136).moveTo(0,20).cylinder(28,24)).union(w3.sketch().push([(5,0)]).rect(46,90).push([(12,-20),(12,20)]).circle(8,mode='s').finalize().extrude(8))
