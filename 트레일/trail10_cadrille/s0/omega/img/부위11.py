import cadquery as cq
w0=cq.Workplane('YZ',origin=(-78,0,0))
w1=cq.Workplane('XY',origin=(0,0,75))
r=w0.sketch().arc((-100,89),(-86,73),(-73,55)).segment((-73,53)).segment((-72,53)).arc((-55,36),(-40,17)).arc((-57,74),(-100,99)).close().assemble().finalize().extrude(40).union(w0.sketch().segment((58,-93),(62,-99)).segment((78,-86)).close().assemble().reset().face(w0.sketch().segment((86,-80),(100,-73)).segment((96,-67)).close().assemble()).finalize().extrude(156)).union(w1.sketch().arc((-55,-29),(-28,-20),(-5,-3)).arc((-33,-13),(-55,-29)).assemble().finalize().extrude(-120))