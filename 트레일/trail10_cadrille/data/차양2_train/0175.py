import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-85,-3),(-9,-63)).segment((9,-63)).segment((85,-3)).segment((66,35)).segment((0,-25)).segment((-66,35)).close().assemble().finalize().extrude(31)