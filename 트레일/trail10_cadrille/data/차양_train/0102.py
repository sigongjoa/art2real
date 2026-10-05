import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-90,12),(-9,-31)).segment((9,-31)).segment((90,12)).segment((80,32)).segment((0,-11)).segment((-80,32)).close().assemble().finalize().extrude(11)