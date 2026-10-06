import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-14))
r=w0.sketch().segment((-94,-5),(-12,-66)).segment((12,-66)).segment((94,-5)).segment((81,21)).segment((0,-40)).segment((-81,21)).close().assemble().finalize().extrude(27)