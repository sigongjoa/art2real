import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
w1=cq.Workplane('XY',origin=(0,0,-59))
w2=cq.Workplane('XY',origin=(0,0,-22))
w3=cq.Workplane('XY',origin=(0,0,15))
w4=cq.Workplane('XY',origin=(0,0,52))
w5=cq.Workplane('XY',origin=(0,0,77))
r=w0.sketch().push([(3,0)]).circle(61).push([(3,0)]).circle(55,mode='s').finalize().extrude(42).union(w1.sketch().segment((67,31),(29,76)).segment((-23,76)).segment((-61,31)).segment((-61,-31)).segment((-23,-76)).segment((29,-76)).segment((67,-31)).close().assemble().push([(3,0)]).circle(51,mode='s').finalize().extrude(37)).union(w2.sketch().segment((59,28),(26,67)).segment((-20,67)).segment((-53,28)).segment((-53,-28)).segment((-20,-67)).segment((26,-67)).segment((59,-28)).close().assemble().push([(3,0)]).circle(46,mode='s').finalize().extrude(37)).union(w3.sketch().segment((51,23),(23,56)).segment((-17,56)).segment((-45,23)).segment((-45,-23)).segment((-17,-56)).segment((23,-56)).segment((51,-23)).close().assemble().push([(3,0)]).circle(41,mode='s').finalize().extrude(37)).union(w4.sketch().segment((44,20),(20,47)).segment((-14,47)).segment((-38,20)).segment((-38,-20)).segment((-14,-47)).segment((20,-47)).segment((44,-20)).close().assemble().push([(3,0)]).circle(32,mode='s').finalize().extrude(25)).union(w5.sketch().segment((33,14),(15,34)).segment((-9,34)).segment((-27,14)).segment((-27,-14)).segment((-9,-34)).segment((15,-34)).segment((33,-14)).close().assemble().finalize().extrude(18))
