"""Blender headless: 角色 FBX + Mixamo 動作 FBX → 單一 GLB(每個動作一個 animation clip)。
用法: blender -b -P build_glb.py -- <character.fbx> <anim_dir> <out.glb> [tex_size]
"""
import bpy, sys, os, glob

argv = sys.argv[sys.argv.index('--') + 1:]
char_fbx, anim_dir, out_glb = argv[0], argv[1], argv[2]
tex_size = int(argv[3]) if len(argv) > 3 else 1024

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.fbx_import(filepath=char_fbx, use_anim=False)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
arm.name = 'Player'
if arm.animation_data is None:
    arm.animation_data_create()
# 角色檔自帶的動作(Mixamo 角色常附一段 T-pose)不要
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)

clips = []
for f in sorted(glob.glob(os.path.join(anim_dir, '*.fbx'))):
    name = os.path.splitext(os.path.basename(f))[0]
    before = set(bpy.data.objects)
    bpy.ops.wm.fbx_import(filepath=f, use_anim=True)
    new = set(bpy.data.objects) - before
    src = next((o for o in new if o.type == 'ARMATURE' and o.animation_data and o.animation_data.action), None)
    if src is None:
        print('!! no action in', f)
    else:
        act = src.animation_data.action
        act.name = name
        act.use_fake_user = True
        track = arm.animation_data.nla_tracks.new()
        track.name = name
        track.strips.new(name, int(act.frame_range[0]), act)
        track.mute = True
        clips.append((name, tuple(act.frame_range)))
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)

for img in bpy.data.images:
    if img.size[0] > tex_size:
        img.scale(tex_size, tex_size)

bpy.ops.export_scene.gltf(
    filepath=out_glb, export_format='GLB', export_animations=True,
    export_animation_mode='NLA_TRACKS', export_skins=True, export_morph=False,
    export_image_format='JPEG', export_jpeg_quality=85, export_apply=False)
print('CLIPS', clips)
print('DONE', out_glb, os.path.getsize(out_glb))
