import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-74,5),(-4,-38)).segment((4,-38)).segment((74,5)).segment((67,19)).segment((0,-24)).segment((-67,19)).close().assemble().finalize().extrude(19).cut(cq.Workplane('XY').box(4,200,10).translate((0,0,10)))