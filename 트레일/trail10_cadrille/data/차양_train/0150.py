import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-9))
r=w0.sketch().segment((-79,11),(-13,-46)).segment((13,-46)).segment((79,11)).segment((71,27)).segment((0,-30)).segment((-71,27)).close().assemble().finalize().extrude(18)