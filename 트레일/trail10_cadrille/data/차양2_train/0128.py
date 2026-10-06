import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().segment((-95,10),(-14,-71)).segment((14,-71)).segment((95,10)).segment((83,35)).segment((0,-46)).segment((-83,35)).close().assemble().finalize().extrude(31)