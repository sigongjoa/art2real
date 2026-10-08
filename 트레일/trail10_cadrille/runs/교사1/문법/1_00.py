import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-63,0))
w1=cq.Workplane('ZX',origin=(0,0,0))
w2=cq.Workplane('XY',origin=(0,0,-41))
r=w0.sketch().arc((40,-97),(-1,-81),(-33,-39)).arc((-38,0),(-33,39)).arc((-1,81),(40,97)).segment((40,92)).arc((-3,74),(-28,36)).arc((-32,0),(-28,-36)).arc((-3,-74),(40,-92)).close().assemble().finalize().extrude(63).union(w1.sketch().arc((40,-89),(1,-74),(-29,-36)).arc((-34,0),(-29,36)).arc((1,74),(40,89)).segment((40,85)).arc((0,68),(-25,33)).arc((-28,0),(-25,-33)).arc((0,-68),(40,-85)).close().assemble().finalize().extrude(63)).cut(w2.sketch().segment((-110,64),(-88,64)).segment((-99,-62)).arc((0,-46),(99,-62)).segment((88,64)).segment((110,64)).segment((110,-70)).segment((-110,-70)).close().assemble().finalize().extrude(82))
