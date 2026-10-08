import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-44,0))
r=w0.sketch().segment((-37,-78),(-45,-60)).segment((-48,-20)).segment((-46,0)).segment((-30,20)).segment((-15,40)).segment((3,45)).segment((11,60)).segment((21,80)).segment((26,100)).segment((40,100)).segment((45,60)).segment((47,20)).segment((45,-20)).segment((38,-60)).segment((30,-78)).close().assemble().finalize().extrude(88)