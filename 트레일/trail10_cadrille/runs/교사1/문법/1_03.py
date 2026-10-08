import cadquery as cq
w0=cq.Workplane('YZ',origin=(-58,0,0))
w1=cq.Workplane('ZX',origin=(0,-50,0))
w2=cq.Workplane('XY',origin=(0,0,-101))
w3=cq.Workplane('ZX',origin=(0,-23,0))
r=w0.sketch().segment((-48,-100),(-6,-100)).segment((-6,-66)).segment((-23,-54)).segment((-23,19)).segment((0,80)).segment((-30,100)).segment((-48,56)).close().assemble().finalize().extrude(116).cut(w1.sketch().segment((-101,43),(-101,60)).segment((101,60)).segment((101,41)).segment((65,47)).segment((40,58)).segment((-55,58)).close().assemble().reset().face(w1.sketch().segment((-101,-43),(-101,-60)).segment((101,-60)).segment((101,-41)).segment((65,-47)).segment((40,-58)).segment((-55,-58)).close().assemble()).finalize().extrude(52)).cut(w2.sketch().segment((59,-49),(61,-49)).segment((61,3)).segment((40,3)).close().assemble().reset().face(w2.sketch().segment((-59,-49),(-61,-49)).segment((-61,3)).segment((-40,3)).close().assemble()).finalize().extrude(202)).union(w3.sketch().push([(-25,0)]).circle(19).finalize().extrude(13)).union(w3.workplane(offset=19).moveTo(-25,0).cylinder(16,27)).union(w3.workplane(offset=39).moveTo(-25,0).cylinder(24,32)).union(w3.workplane(offset=59).moveTo(-25,0).cylinder(16,27))
