import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-10))
r=w0.sketch().segment((-85,7),(-13,-35)).segment((13,-35)).segment((85,7)).segment((72,34)).segment((0,-8)).segment((-72,34)).close().assemble().finalize().extrude(19).cut(cq.Workplane('XY').box(8,200,8).translate((-23,0,10))).cut(cq.Workplane('XY').box(3,200,12).translate((-40,0,10)))