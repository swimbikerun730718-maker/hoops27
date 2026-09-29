"""CMU BVH → 遊戲用關節軌跡 JSON(公尺、Y-up、面向 +Z、30fps)。
遊戲載入時再依 Mixamo 骨架把方向「烘焙」成 AnimationClip。
用法: python3 cmu_to_json.py <out.json>
"""
import json, sys
import numpy as np
from bvh_fk import parse_bvh, fk

SRC = '../_src/cmu'
JOINTS = ['Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase',
          'Spine1', 'Neck', 'Head', 'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 'LeftFingerBase',
          'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand', 'RightFingerBase']
# 名稱: (檔案, 開始秒, 結束秒, 面向基準秒, 面向模式)
CLIPS = {
    'jumpshot': ('06_15', 2.30, 3.40, 2.80, 'shot'),
    # 防守滑步：在時間窗內自動找一個完整步伐循環(兩腳張最開 → 下一次張最開)
    'shuffle_left': ('102_28', 1.55, 2.25, 1.90, 'loop'),
}
MIRRORS = {'shuffle_right': 'shuffle_left'}   # 向右滑步 = 向左滑步左右鏡射(兩邊循環品質一致)


def find_cycle(P, k0, k1):
    d = np.linalg.norm((P['LeftFoot'] - P['RightFoot'])[:, [0, 2]], axis=1)
    peaks = [k for k in range(k0 + 1, k1 - 1) if d[k] >= d[k - 1] and d[k] >= d[k + 1] and d[k] > 0.7 * d[k0:k1].max()]
    best = None
    for i in range(len(peaks) - 1):
        a, b = peaks[i], peaks[i + 1]
        if b - a < 20:
            continue
        score = abs(P['Hips'][a, 1] - P['Hips'][b, 1])
        if best is None or score < best[0]:
            best = (score, a, b)
    return (best[1], best[2]) if best else (k0, k1)
TARGET_LEG = 0.96 - 0.08   # Mixamo Bryce 骨盆高 - 腳踝高(公尺)


def yaw_to_plus_z(P, k, mode):
    if mode == 'shot':                        # 投籃：以出手手相對頭部的水平方向當正前方
        fwd = P['RightHand'][k] - P['Head'][k]
    else:                                     # 其餘：骨盆朝向
        fwd = np.cross(P['LeftUpLeg'][k] - P['RightUpLeg'][k], [0, 1, 0])
    ang = np.arctan2(fwd[0], fwd[2])
    c, s = np.cos(-ang), np.sin(-ang)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


out = {}
for name, (f, a, b, face_t, mode) in CLIPS.items():
    J, D, ft = parse_bvh(f'{SRC}/{f}.bvh')
    P, _ = fk(J, D)
    fps_src = 1 / ft
    k0, k1, kf = int(a * fps_src), int(b * fps_src), int(face_t * fps_src)
    if mode == 'loop':
        k0, k1 = find_cycle(P, k0, k1)
        kf = (k0 + k1) // 2
    Ry = yaw_to_plus_z(P, kf, mode)
    leg = np.mean(P['Hips'][:60, 1] - (P['LeftFoot'][:60, 1] + P['RightFoot'][:60, 1]) / 2)
    scale = TARGET_LEG / leg
    origin = P['Hips'][k0].copy(); origin[1] = 0
    floor = min(P['LeftToeBase'][k0:k1, 1].min(), P['RightToeBase'][k0:k1, 1].min())
    idx = np.arange(k0, k1, fps_src / 30).astype(int)
    frames = []
    for k in idx:
        fr = []
        for j in JOINTS:
            p = (P[j][k] - origin) @ Ry.T
            p[1] -= floor
            fr += [round(float(v) * scale, 4) for v in p]
        frames.append(fr)
    # 起跳/落地：雙腳都離地的時段
    feet = np.minimum(P['LeftToeBase'][idx, 1], P['RightToeBase'][idx, 1]) - floor
    air = np.where(feet > 0.6)[0]
    t0, t1 = (air[0] / 30, air[-1] / 30) if len(air) > 2 else (0.3 * len(idx) / 30, 0.7 * len(idx) / 30)
    out[name] = {'fps': 30, 'joints': JOINTS, 'frames': frames, 't0': round(t0, 3), 't1': round(t1, 3), 'loop': mode == 'loop',
                 'speed': round(float(np.linalg.norm((P['Hips'][k1] - P['Hips'][k0])[[0, 2]]) * scale / ((k1 - k0) / fps_src)), 3),
                 'hipsRest': round(float(np.mean(P['Hips'][:60, 1]) - floor) * scale, 4)}
    print(name, f'{k0/fps_src:.2f}-{k1/fps_src:.2f}s', len(frames), 'frames', 'speed m/s', out[name]['speed'], 't0/t1', out[name]['t0'], out[name]['t1'], 'scale', round(scale, 4), 'hipsRest', out[name]['hipsRest'])
for dst, src in MIRRORS.items():
    d = out[src]
    sw = [JOINTS.index(j.replace('Left', 'TMP').replace('Right', 'Left').replace('TMP', 'Right')) for j in JOINTS]
    frames = []
    for fr in d['frames']:
        nf = []
        for j in range(len(JOINTS)):
            x, y, z = fr[sw[j] * 3:sw[j] * 3 + 3]
            nf += [-x, y, z]
        frames.append(nf)
    out[dst] = dict(d, frames=frames)
    print(dst, '= mirror of', src)
json.dump(out, open(sys.argv[1], 'w'), separators=(',', ':'))
