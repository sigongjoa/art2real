import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-74,7),(-8,-26)).segment((8,-26)).segment((74,7)).segment((67,21)).segment((0,-12)).segment((-67,21)).close().assemble().finalize().extrude(20).cut(cq.Workplane('XY').box(8,200,14).translate((-23,0,10)))