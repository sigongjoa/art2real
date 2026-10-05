import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-13))
r=w0.sketch().segment((-100,16),(-10,-40)).segment((14,-40)).segment((100,17)).segment((78,40)).segment((-4,-16)).segment((-77,39)).close().assemble().finalize().extrude(21).union(w0.sketch().segment((-11,-39),(-10,-40)).segment((83,39)).segment((82,40)).close().assemble().finalize().extrude(26))