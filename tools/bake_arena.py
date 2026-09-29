"""Blender headless:照遊戲場館尺寸重建靜態幾何，用 Cycles 烘焙地板光照貼圖(直射+間接，不含表面顏色)。
座標：遊戲/three.js (x, y 上, z 朝鏡頭) → Blender (x, -z, y)。單位沿用英尺數值。
用法: blender -b -P bake_arena.py -- <out_dir> [samples]
輸出: floor_light.png(sRGB 編碼)+ floor_light.json(區域、正規化倍率)
"""
import bpy, sys, os, json, math
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]
samples = int(argv[1]) if len(argv) > 1 else 384
REGION = {'x0': -45, 'x1': 45, 'z0': -10, 'z1': 60}      # three.js 座標
RES = (2048, 1600)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = samples
sc.render.threads_mode = 'AUTO'
world = bpy.data.worlds.new('W'); sc.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.012, 0.014, 0.022, 1)


def mat(name, color, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = 0.6
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    return m


def box(size, center, m):
    sx, sy, sz = size; cx, cy, cz = center                      # three.js 尺寸/中心
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, -cz, cy))
    o = bpy.context.object; o.scale = (sx, sz, sy)
    o.data.materials.append(m); return o


def plane(w, h, center, m, rot=(0, 0, 0)):
    cx, cy, cz = center
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, -cz, cy), rotation=rot)
    o = bpy.context.object; o.scale = (w, h, 1)
    o.data.materials.append(m); return o


M_STAND = mat('stand', (0.07, 0.08, 0.11))
M_WALL = mat('wall', (0.03, 0.035, 0.05))
M_PAD = mat('pad', (0.09, 0.1, 0.14))
M_ORANGE = mat('orange', (1.0, 0.35, 0.05))
M_LED = mat('led', (0.02, 0.02, 0.02), emit=(1.0, 0.38, 0.05), strength=6.0)
M_CROWD = mat('crowd', (0.25, 0.22, 0.22))

# 看台(與 index.html buildArena 相同尺寸)+ 一層觀眾(遮擋/反射用)
for r in range(14):
    top = (r + 1) * 1.15; z = -11 - r * 1.8
    box((120, top, 1.8), (0, top / 2, z), M_STAND)
    box((116, 1.2, 0.8), (0, top + 0.6, z), M_CROWD)
    for s in (-1, 1):
        x = s * (33 + r * 1.8)
        box((1.8, top, 64), (x, top / 2, 22), M_STAND)
        box((0.8, 1.2, 62), (x, top + 0.6, 22), M_CROWD)
box((200, 60, 1), (0, 30, -38), M_WALL)
# LED 廣告帶(會把橘光打到地板)
plane(110, 2.6, (0, 1.3, -9.6), M_LED, rot=(math.pi / 2, 0, 0))
for s in (-1, 1):
    plane(64, 2.6, (s * 31.6, 1.3, 22), M_LED, rot=(math.pi / 2, 0, s * math.pi / 2))
# 籃架
box((4.6, 3.4, 5), (0, 1.7, -7.5), M_PAD)
box((4.65, 0.5, 5.05), (0, 3.1, -7.5), M_ORANGE)
bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=9.4, location=(0, 8.2, 8.1)); bpy.context.object.data.materials.append(M_PAD)
box((0.55, 0.55, 12), (0, 11.85, -2.2), M_PAD)
box((6.3, 0.35, 0.4), (0, 9.3, 4), M_PAD)
box((6.2, 3.6, 0.15), (0, 11.25, 4), mat('board', (0.8, 0.85, 0.9)))

# 天花板燈架：與遊戲裡 7 盞燈同位置的面光源，另加一盞罩住球場的大柔光
for i in range(-3, 4):
    bpy.ops.object.light_add(type='AREA', location=(i * 14, -10, 52))
    L = bpy.context.object.data; L.shape = 'RECTANGLE'; L.size = 5; L.size_y = 2; L.energy = 90000; L.color = (1.0, 0.95, 0.86)
bpy.ops.object.light_add(type='AREA', location=(0, -22, 48))
L = bpy.context.object.data; L.shape = 'RECTANGLE'; L.size = 50; L.size_y = 40; L.energy = 260000; L.color = (1.0, 0.97, 0.92)

# 烘焙目標：地板(區域 REGION),白色漫射材質 → 只取光照
x0, x1, z0, z1 = REGION['x0'], REGION['x1'], REGION['z0'], REGION['z1']
floor = plane(x1 - x0, z1 - z0, ((x0 + x1) / 2, 0, (z0 + z1) / 2), mat('floor', (0.8, 0.8, 0.8)))
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -20, -0.05)); ap = bpy.context.object; ap.scale = (300, 300, 1)
ap.data.materials.append(mat('apron', (0.35, 0.3, 0.25)))
img = bpy.data.images.new('floor_light', RES[0], RES[1], float_buffer=True)
nt = floor.data.materials[0].node_tree
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
nt.nodes.active = tex
for o in bpy.context.scene.objects: o.select_set(False)
floor.select_set(True); bpy.context.view_layer.objects.active = floor
sc.render.bake.use_pass_direct = True
sc.render.bake.use_pass_indirect = True
sc.render.bake.use_pass_color = False
sc.render.bake.margin = 4
bpy.ops.object.bake(type='DIFFUSE')

px = np.array(img.pixels[:], dtype=np.float32).reshape(RES[1], RES[0], 4)[..., :3]
lum = px.mean(axis=2)
ref = float(np.percentile(lum, 99.5))
enc = np.clip(px / ref, 0, 1) ** (1 / 2.2)                     # sRGB 近似編碼
out = bpy.data.images.new('floor_light_8', RES[0], RES[1])
rgba = np.concatenate([enc, np.ones((RES[1], RES[0], 1), np.float32)], axis=2)
out.pixels[:] = rgba.ravel()
out.filepath_raw = os.path.join(out_dir, 'floor_light.png'); out.file_format = 'PNG'; out.save()
json.dump({'region': REGION, 'scale': ref, 'res': RES, 'samples': samples,
           'center': float(lum[RES[1] // 2, RES[0] // 2] / ref)}, open(os.path.join(out_dir, 'floor_light.json'), 'w'))
print('BAKED', out.filepath_raw, 'ref', ref, 'mean', float(lum.mean() / ref))
