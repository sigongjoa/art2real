import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-46))
w1=cq.Workplane('ZX',origin=(0,35,0))
r=w0.sketch().segment((6,-55),(17,-66)).segment((88,-66)).segment((98,-55)).segment((98,25)).segment((90,35)).segment((14,35)).segment((6,25)).close().assemble().reset().face(w0.sketch().segment((-6,-55),(-17,-66)).segment((-88,-66)).segment((-98,-55)).segment((-98,25)).segment((-90,35)).segment((-14,35)).segment((-6,25)).close().assemble()).push([(55,-24),(-55,-24)]).circle(17,mode='s').finalize().extrude(92).union(w1.sketch().push([(-14,53),(-14,-53)]).rect(56,40).finalize().extrude(35))
