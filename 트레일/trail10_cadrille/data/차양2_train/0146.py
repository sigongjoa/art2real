import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-98,20),(-12,-64)).segment((12,-64)).segment((98,20)).segment((81,55)).segment((0,-29)).segment((-81,55)).close().assemble().finalize().extrude(36)