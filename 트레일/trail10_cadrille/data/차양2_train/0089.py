import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-90,7),(-16,-58)).segment((16,-58)).segment((90,7)).segment((74,40)).segment((0,-25)).segment((-74,40)).close().assemble().finalize().extrude(24)