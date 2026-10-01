import bpy, os, sys
S=os.path.dirname(os.path.abspath(__file__)); sc=bpy.context.scene
sc.render.engine="BLENDER_WORKBENCH"; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="SINGLE"; sc.display.shading.single_color=(0.8,0.8,0.8); sc.render.film_transparent=True; sc.render.use_freestyle=False
for n in ("02_정면","02_옆","02_3-4"):
    cam=bpy.data.objects["카메라_"+n]; sc.camera=cam; sc.render.resolution_x, sc.render.resolution_y=cam["W"],cam["H"]; sc.render.filepath=S+"/cut/shade_%s.png"%n.split("_")[1]; bpy.ops.render.render(write_still=True)
