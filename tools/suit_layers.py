"""정리된 슈트 시트(880x3200, suit_kit.py 결과) → 게임 몸 시트 hair3/body_<이름>.png (4400x3200, 5칸 레이어)
게임(hkBody)의 레이어 순서와 같다:
  0 몸 그림 (손발은 회색으로, 그 위에 1번이 덮임)
  1 피부 (흰색 계열 → 게임이 피부색을 곱해 입힘)
  2·3 색 바꾸기용 (단일 무늬 슈트라 비움)
  4 손 영역 (머리 위에 다시 그려 손이 머리를 가리도록)
사용: python3 -I suit_layers.py <suit_sheet.png> <출력 body_xxx.png>
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suit_kit import load, save


def is_skin(r, g, b, a):
    return a > 40 and r > 140 and r > g + 12 and g > b + 8 and r - b > 40


def main(src, dst):
    W, H, px = load(src)
    skin = bytearray(W * H); lums = []
    for i in range(W * H):
        o = i * 4
        if is_skin(px[o], px[o + 1], px[o + 2], px[o + 3]):
            skin[i] = 1; lums.append(.3 * px[o] + .59 * px[o + 1] + .11 * px[o + 2])
    lums.sort(); ref = lums[len(lums) * 3 // 4] if lums else 230  # 밝은 피부 기준(그림자는 더 어둡게 남음)
    OW = W * 5; out = bytearray(OW * H * 4)
    def put(L, i, rgba):
        y = i // W; x = i % W; o = (y * OW + L * W + x) * 4; out[o:o + 4] = bytes(rgba)
    # 손 영역: 피부를 2px 넓힌 곳 (테두리까지 머리 위로)
    hand = bytearray(skin)
    for _ in range(2):
        nxt = bytearray(hand)
        for i in range(W * H):
            if hand[i]: continue
            x = i % W
            if (x > 0 and hand[i - 1]) or (x < W - 1 and hand[i + 1]) or (i >= W and hand[i - W]) or (i + W < W * H and hand[i + W]): nxt[i] = 1
        hand = nxt
    for i in range(W * H):
        o = i * 4; r, g, b, a = px[o], px[o + 1], px[o + 2], px[o + 3]
        if not a: continue
        lum = .3 * r + .59 * g + .11 * b
        if skin[i]:
            v = int(min(255, lum * 238 / ref)); put(0, i, (v, v, v, a)); put(1, i, (v, v, v, a))
        else:
            put(0, i, (r, g, b, a))
        if hand[i]: put(4, i, (255, 255, 255, a))
    save(dst, OW, H, out)
    print('skin px', len(lums), 'ref lum %.0f' % ref, '->', dst)


if __name__ == '__main__':
    main(*sys.argv[1:3])
