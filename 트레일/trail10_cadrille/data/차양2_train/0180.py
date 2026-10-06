import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-22))
r=w0.sketch().segment((-96,-1),(-13,-68)).segment((13,-68)).segment((96,-1)).segment((82,28)).segment((0,-39)).segment((-82,28)).close().assemble().finalize().extrude(44).cut(cq.Workplane('XY').box(9,200,20).translate((0,0,22)))