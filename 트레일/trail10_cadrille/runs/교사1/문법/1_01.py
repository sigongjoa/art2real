import cadquery as cq
w0=cq.Workplane('YZ',origin=(12,0,0))
w1=cq.Workplane('YZ',origin=(-85,0,0))
w2=cq.Workplane('YZ',origin=(9,0,0))
w3=cq.Workplane('YZ',origin=(-17,0,0))
w4=cq.Workplane('XY',origin=(0,0,47))
w5=cq.Workplane('XY',origin=(0,0,-101))
w6=cq.Workplane('ZX',origin=(0,-56,0))
r=w0.sketch().segment((-19,-100),(40,-100)).segment((40,-84)).segment((37,-83)).segment((36,-50)).segment((41,0)).segment((45,76)).segment((-44,76)).segment((-40,0)).segment((-36,-50)).segment((-32,-80)).segment((-30,-90)).close().assemble().finalize().extrude(73).union(w1.sketch().segment((-19,-100),(40,-100)).segment((40,-84)).segment((37,-83)).segment((36,-50)).segment((41,0)).segment((45,76)).segment((-44,76)).segment((-40,0)).segment((-36,-50)).segment((-32,-80)).segment((-30,-90)).close().assemble().finalize().extrude(73)).union(w2.sketch().segment((-40,22),(41,22)).segment((45,76)).segment((36,76)).segment((14,100)).segment((-45,100)).segment((-44,76)).close().assemble().finalize().extrude(8)).union(w3.sketch().segment((-40,22),(41,22)).segment((45,76)).segment((36,76)).segment((14,100)).segment((-45,100)).segment((-44,76)).close().assemble().finalize().extrude(8)).cut(w4.sketch().segment((34,-7),(54,-7)).segment((54,13)).segment((44,23)).segment((34,13)).close().assemble().reset().face(w4.sketch().segment((-34,-7),(-54,-7)).segment((-54,13)).segment((-44,23)).segment((-34,13)).close().assemble()).finalize().extrude(40)).cut(w5.sketch().push([(49,-15),(-49,-15)]).rect(22,70).finalize().extrude(46)).cut(w6.sketch().push([(-74,49),(-74,-49)]).circle(16).finalize().extrude(60))
