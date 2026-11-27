"""새 슈트 시트(GPT 2x2) → 게임 몸 시트 칸(220x320)에 맞춘 시트 + 검수 이미지
- 원본 몸 시트(hair_kit body_*.png)의 프레임마다 발 위치·키를 기준으로 크기와 위치를 맞춘다
- 배경(흰색·투명)을 지우고, 걷기 오른쪽은 걷기 왼쪽을 좌우로 뒤집어 만든다
사용: python3 -I suit_kit.py <새 시트 폴더> <원본 몸 시트 폴더> <출력 폴더>
새 시트 폴더 파일 이름: walk_front, walk_back, walk_left, sit_front, sit_back, wave, ok, jump, photo (.png)
"""
import sys, os, zlib, struct

CW, CH = 220, 320
# (새 시트 이름, 격자, 원본 시트, 원본 줄, 출력 줄)  출력 줄은 게임 몸 시트 순서 (walk 0~3, sit 4~5, emote 6~8, photo 9)
JOBS = [('walk_front', (2, 2), 'walk', 0, 0), ('walk_left', (2, 2), 'walk', 1, 1), ('walk_left', (2, 2), 'walk', 2, 2),
        ('walk_back', (2, 2), 'walk', 3, 3), ('sit_front', (2, 2), 'sit', 0, 4), ('sit_back', (2, 2), 'sit', 1, 5),
        ('wave', (2, 2), 'emote', 0, 6), ('ok', (2, 2), 'emote', 1, 7), ('jump', (2, 2), 'emote', 2, 8), ('photo', (2, 1), 'photo', 0, 9)]
MIRROR = {2}  # 출력 줄 2(걷기 오른쪽)는 걷기 왼쪽을 뒤집어 만든다


def load(p):
    b = open(p, 'rb').read(); i = 8; idat = b''
    while i < len(b):
        n = struct.unpack('>I', b[i:i + 4])[0]; t = b[i + 4:i + 8]; d = b[i + 8:i + 8 + n]; i += 12 + n
        if t == b'IHDR': W, H, bd, ct = struct.unpack('>IIBB', d[:10])
        elif t == b'IDAT': idat += d
    bpp = {6: 4, 2: 3}[ct]; raw = zlib.decompress(idat); st = W * bpp; px = bytearray(H * st); prev = bytearray(st); p = 0
    for y in range(H):
        f = raw[p]; p += 1; line = bytearray(raw[p:p + st]); p += st
        if f == 1:
            for x in range(bpp, st): line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(st): line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(st): line[x] = (line[x] + (((line[x - bpp] if x >= bpp else 0) + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(st):
                a = line[x - bpp] if x >= bpp else 0; c = prev[x - bpp] if x >= bpp else 0; u = prev[x]
                pa = abs(u - c); pb = abs(a - c); pc = abs(a + u - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (u if pb <= pc else c))) & 255
        px[y * st:(y + 1) * st] = line; prev = line
    if bpp == 3:
        q = bytearray(W * H * 4)
        for k in range(W * H): q[k * 4:k * 4 + 3] = px[k * 3:k * 3 + 3]; q[k * 4 + 3] = 255
        px = q
    return W, H, px


def save(p, W, H, px):
    def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    raw = b''.join(b'\x00' + bytes(px[y * W * 4:(y + 1) * W * 4]) for y in range(H))
    open(p, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))


def clear_bg(W, H, px):
    """테두리에 닿은 흰 배경을 투명하게"""
    seen = bytearray(W * H); stack = [x for x in range(W)] + [(H - 1) * W + x for x in range(W)] + [y * W for y in range(H)] + [y * W + W - 1 for y in range(H)]
    while stack:
        n = stack.pop()
        if seen[n]: continue
        seen[n] = 1; o = n * 4
        if px[o + 3] > 30 and not (px[o] > 225 and px[o + 1] > 225 and px[o + 2] > 225): continue
        px[o + 3] = 0; x = n % W; y = n // W
        if x > 0: stack.append(n - 1)
        if x < W - 1: stack.append(n + 1)
        if y > 0: stack.append(n - W)
        if y < H - 1: stack.append(n + W)


def bbox(W, px, x0, y0, x1, y1, th=40):
    bx0 = by0 = 10 ** 9; bx1 = by1 = -1
    for y in range(y0, y1):
        r = y * W
        for x in range(x0, x1):
            if px[(r + x) * 4 + 3] > th:
                if x < bx0: bx0 = x
                if x > bx1: bx1 = x
                if y < by0: by0 = y
                if y > by1: by1 = y
    return (bx0, by0, bx1 + 1, by1 + 1) if bx1 >= 0 else None


def figures(W, H, px, k):
    """캐릭터 덩어리 k개를 찾아 (위→아래, 왼→오른) 순서의 상자로. 격자로 자르면 칸을 넘은 발이 잘려 남는다"""
    lab = [0] * (W * H); comps = []
    for start in range(W * H):
        if lab[start] or px[start * 4 + 3] <= 40: continue
        cid = len(comps) + 1; lab[start] = cid; st = [start]; x0 = y0 = 10 ** 9; x1 = y1 = -1; n = 0
        while st:
            q = st.pop(); x = q % W; y = q // W; n += 1
            if x < x0: x0 = x
            if x > x1: x1 = x
            if y < y0: y0 = y
            if y > y1: y1 = y
            for nb in ((q - 1) if x > 0 else -1, (q + 1) if x < W - 1 else -1, q - W, q + W):
                if 0 <= nb < W * H and not lab[nb] and px[nb * 4 + 3] > 40: lab[nb] = cid; st.append(nb)
        comps.append([n, x0, y0, x1 + 1, y1 + 1])
    comps.sort(key=lambda c: -c[0]); seeds = [c[1:] for c in comps[:k]]
    for c in comps[k:]:
        if c[0] < 30: continue  # 먼지 같은 점은 버림
        cx = (c[1] + c[3]) / 2; cy = (c[2] + c[4]) / 2
        best = min(seeds, key=lambda s: max(0, s[0] - cx, cx - s[2]) ** 2 + max(0, s[1] - cy, cy - s[3]) ** 2)
        best[0] = min(best[0], c[1]); best[1] = min(best[1], c[2]); best[2] = max(best[2], c[3]); best[3] = max(best[3], c[4])
    rows = sorted(seeds, key=lambda s: (s[1] + s[3]) / 2)
    out = []
    per = k if k <= 2 else 2
    for i in range(0, k, per): out += sorted(rows[i:i + per], key=lambda s: s[0])
    return [tuple(s) for s in out]


def foot_cx(W, px, b):
    """발 부분(아래 12%)의 가로 중심"""
    x0, y0, x1, y1 = b; ys = y1 - max(2, (y1 - y0) * 12 // 100); s = n = 0
    for y in range(ys, y1):
        for x in range(x0, x1):
            if px[(y * W + x) * 4 + 3] > 40: s += x; n += 1
    return s / n if n else (x0 + x1) / 2


def resample(W, px, b, s, flip=False):
    """b 영역을 s배로 줄여 새 RGBA (상자 평균, 알파 곱셈)"""
    x0, y0, x1, y1 = b; tw = max(1, round((x1 - x0) * s)); th = max(1, round((y1 - y0) * s)); out = bytearray(tw * th * 4)
    for ty in range(th):
        sy0 = y0 + ty / s; sy1 = min(y1, y0 + (ty + 1) / s)
        for tx in range(tw):
            sx0 = x0 + tx / s; sx1 = min(x1, x0 + (tx + 1) / s); r = g = bl = a = w = 0.0
            yy = int(sy0)
            while yy < sy1:
                wy = min(yy + 1, sy1) - max(yy, sy0); xx = int(sx0)
                while xx < sx1:
                    wx = min(xx + 1, sx1) - max(xx, sx0); o = (yy * W + xx) * 4; al = px[o + 3] / 255 * wx * wy
                    r += px[o] * al; g += px[o + 1] * al; bl += px[o + 2] * al; a += al; w += wx * wy; xx += 1
                yy += 1
            ox = (tw - 1 - tx) if flip else tx; o = (ty * tw + ox) * 4
            if a > 0: out[o] = int(r / a); out[o + 1] = int(g / a); out[o + 2] = int(bl / a); out[o + 3] = min(255, int(a / w * 255 + .5))
    return tw, th, out


def blit(W, dst, sw, sh, src, dx, dy):
    for y in range(sh):
        for x in range(sw):
            o = (y * sw + x) * 4
            if src[o + 3] == 0: continue
            X = dx + x; Y = dy + y
            if 0 <= X < W and 0 <= Y < len(dst) // (W * 4):
                p = (Y * W + X) * 4; a = src[o + 3] / 255
                for k in range(3): dst[p + k] = int(src[o + k] * a + dst[p + k] * (1 - a))
                dst[p + 3] = max(dst[p + 3], src[o + 3])


def main(newdir, origdir, outdir):
    os.makedirs(outdir, exist_ok=True)
    orig = {k: load(os.path.join(origdir, 'body_%s.png' % k)) for k in ('walk', 'sit', 'emote', 'photo')}
    SW, SH = 4 * CW, 10 * CH; sheet = bytearray(SW * SH * 4); check = bytearray(SW * SH * 4)
    for i in range(0, len(check), 4): check[i:i + 4] = b'\xff\xff\xff\xff'
    cache = {}; report = []
    for name, (gc, gr), ok, orow, outrow in JOBS:
        if name not in cache:
            W, H, px = load(os.path.join(newdir, name + '.png')); clear_bg(W, H, px)
            frames = figures(W, H, px, gc * gr)
            cache[name] = (W, px, frames)
        W, px, frames = cache[name]; OW, OH, opx = orig[ok]
        ob = [bbox(OW, opx, f * CW, orow * CH, (f + 1) * CW, (orow + 1) * CH) for f in range(4)]
        # 시트 하나의 배율은 첫 프레임 키로 정한다 (브이·하트는 두 칸 평균)
        if name == 'photo': s = ((ob[0][3] - ob[0][1]) / (frames[0][3] - frames[0][1]) + (ob[1][3] - ob[1][1]) / (frames[1][3] - frames[1][1])) / 2
        else: s = (ob[0][3] - ob[0][1]) / (frames[0][3] - frames[0][1])
        flip = outrow in MIRROR
        for f, b in enumerate(frames):
            if not b or not ob[f]: continue
            tw, th, img = resample(W, px, b, s, flip)
            # 발 위치: 원본 프레임의 발 가로 중심·바닥 줄에 맞춤
            ofx = foot_cx(OW, opx, ob[f]) - f * CW; obot = ob[f][3] - orow * CH
            nfx = foot_cx(W, px, b); nfx = (b[2] - nfx) if flip else (nfx - b[0]); nfx *= s
            dx = f * CW + round(ofx - nfx); dy = outrow * CH + obot - th
            blit(SW, sheet, tw, th, img, dx, dy)
            # 검수: 원본을 연한 빨강으로 뒤에, 그 위에 새 슈트, 바닥 줄은 하늘색
            for y in range(orow * CH, (orow + 1) * CH):
                for x in range(f * CW, (f + 1) * CW):
                    o = (y * OW + x) * 4
                    if opx[o + 3] > 40:
                        p = ((y - orow * CH + outrow * CH) * SW + x) * 4; check[p:p + 3] = b'\xff\xb8\xb8'
            blit(SW, check, tw, th, img, dx, dy)
            for x in range(f * CW, (f + 1) * CW):
                p = ((outrow * CH + obot) * SW + x) * 4; check[p:p + 4] = b'\x30\xb0\xe0\xff'
            report.append('%-10s 줄%d 칸%d 배율 %.3f' % (name + ('(뒤집기)' if flip else ''), outrow, f, s))
    save(os.path.join(outdir, 'suit_sheet.png'), SW, SH, sheet)
    save(os.path.join(outdir, 'suit_check.png'), SW, SH, check)
    print('\n'.join(report))


if __name__ == '__main__':
    main(*sys.argv[1:4])
