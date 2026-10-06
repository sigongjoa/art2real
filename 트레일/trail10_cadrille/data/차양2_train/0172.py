import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-21))
r=w0.sketch().segment((-87,7),(-9,-51)).segment((9,-51)).segment((87,7)).segment((75,32)).segment((0,-26)).segment((-75,32)).close().assemble().finalize().extrude(41)