import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-6))
r=w0.sketch().segment((-66,8),(-13,-49)).segment((13,-49)).segment((66,8)).segment((54,33)).segment((0,-24)).segment((-54,33)).close().assemble().finalize().extrude(11).cut(cq.Workplane('XY').box(5,200,6).translate((-7,0,6)))