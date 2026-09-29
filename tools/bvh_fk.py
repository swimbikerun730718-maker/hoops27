"""最小 BVH 解析 + 前向運動學：回傳每個關節每一幀的世界座標(BVH 原始單位,Y-up)。"""
import numpy as np


def parse_bvh(path):
    toks = open(path).read().split()
    i = 0
    joints, stack = [], []

    def nxt():
        nonlocal i
        i += 1
        return toks[i - 1]

    while True:
        t = nxt()
        if t in ('ROOT', 'JOINT'):
            name = nxt()
            joints.append({'name': name, 'parent': stack[-1] if stack else -1, 'chan': [], 'end': None})
            stack.append(len(joints) - 1)
        elif t == 'End':
            nxt(); nxt(); nxt()
            joints[stack[-1]]['end'] = [float(nxt()) for _ in range(3)]
            nxt()
        elif t == 'OFFSET':
            joints[stack[-1]]['offset'] = np.array([float(nxt()) for _ in range(3)])
        elif t == 'CHANNELS':
            n = int(nxt())
            joints[stack[-1]]['chan'] = [nxt() for _ in range(n)]
        elif t == '}':
            stack.pop()
        elif t == 'MOTION':
            break
    nxt(); nf = int(nxt()); nxt(); nxt(); ft = float(nxt())
    data = np.array(toks[i:i + nf * sum(len(j['chan']) for j in joints)], dtype=float).reshape(nf, -1)
    return joints, data, ft


def rotmat(axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    z, o = np.zeros_like(a), np.ones_like(a)
    if axis == 'X':
        m = [[o, z, z], [z, c, -s], [z, s, c]]
    elif axis == 'Y':
        m = [[c, z, s], [z, o, z], [-s, z, c]]
    else:
        m = [[c, -s, z], [s, c, z], [z, z, o]]
    return np.moveaxis(np.array(m), [0, 1], [-2, -1])


def fk(joints, data):
    nf = data.shape[0]
    pos = {}
    rot = {}
    col = 0
    for ji, j in enumerate(joints):
        R = np.broadcast_to(np.eye(3), (nf, 3, 3)).copy()
        t = np.broadcast_to(j['offset'], (nf, 3)).copy()
        for c in j['chan']:
            v = data[:, col]; col += 1
            if c.endswith('position'):
                t[:, 'XYZ'.index(c[0])] = v + j['offset']['XYZ'.index(c[0])] * 0
            else:
                R = R @ rotmat(c[0], v)
        if j['parent'] < 0:
            rot[ji] = R
            pos[ji] = t
        else:
            p = j['parent']
            pos[ji] = pos[p] + np.einsum('fij,fj->fi', rot[p], t)
            rot[ji] = rot[p] @ R
    names = [j['name'] for j in joints]
    return {names[k]: pos[k] for k in pos}, {names[k]: rot[k] for k in rot}
