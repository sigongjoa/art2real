import cadquery as cq
w0=cq.Workplane('YZ',origin=(35,0,0))
w1=cq.Workplane('XY',origin=(0,0,-2))
r=w0.sketch().segment((-35,19),(35,97)).segment((35,98)).segment((34,98)).segment((34,99)).close().assemble().reset().face(w0.sketch().segment((-34,-99),(-33,-99)).segment((-33,-100)).segment((-3,-54)).segment((-3,-53)).segment((-34,-99)).close().assemble()).finalize().extrude(-27).union(w1.sketch().arc((21,-11),(34,-1),(40,13)).segment((21,13)).close().assemble().finalize().extrude(-69))