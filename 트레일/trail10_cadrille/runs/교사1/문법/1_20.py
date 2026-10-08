import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-24))
w1=cq.Workplane('XY',origin=(0,0,-10))
w2=cq.Workplane('YZ',origin=(7,0,0))
w3=cq.Workplane('YZ',origin=(3,0,0))
w4=cq.Workplane('YZ',origin=(1,0,0))
w5=cq.Workplane('YZ',origin=(23,0,0))
r=w0.sketch().segment((23,-94),(-32,-24)).segment((-33,-18)).segment((-16,48)).segment((-2,60)).segment((8,90)).segment((29,98)).segment((37,94)).segment((37,-87)).segment((27,-94)).close().assemble().finalize().extrude(14).union(w1.sketch().segment((20,-100),(-37,-26)).segment((-39,-19)).segment((-22,49)).segment((-7,61)).segment((4,91)).segment((27,100)).segment((34,95)).segment((34,-94)).segment((25,-100)).close().assemble().finalize().extrude(4)).union(w2.sketch().segment((53,-6),(54,14)).segment((56,18)).segment((60,22)).segment((70,23)).segment((74,22)).segment((78,19)).segment((92,-6)).close().assemble().finalize().extrude(15)).union(w3.sketch().push([(68,10)]).circle(6).finalize().extrude(22)).cut(w4.sketch().push([(68,10)]).circle(3).finalize().extrude(4)).cut(w5.sketch().push([(68,10)]).circle(3).finalize().extrude(4))
