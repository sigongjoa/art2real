import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-18))
r=w0.sketch().segment((-86,4),(-9,-66)).segment((9,-66)).segment((86,4)).segment((70,36)).segment((0,-34)).segment((-70,36)).close().assemble().finalize().extrude(36)