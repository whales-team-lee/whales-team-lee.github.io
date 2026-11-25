# 헤어 키트 (2026-11-25)

프리다이빙리조트 메타버스 캐릭터 헤어 제작용 기준 그림, 최종 프롬프트, 헤어 목록입니다.

## 폴더 구성

| 폴더 | 내용 |
|---|---|
| `reference/base_female_head_grey.png` | 기준 머리 (남녀 공통). GPT에 이 파일을 첨부합니다. |
| `female/` | 확정된 여자 헤어 9종 (회색 원본, 2×2) |
| `body/` | 머리를 뗀 슈트 몸 시트 5장 (걷기·앉기·요가·인사·사진) |

## 제작 규칙

- 남녀 얼굴은 동일합니다. 기준 머리 하나로 남녀 헤어를 모두 만듭니다.
- 남자 헤어는 붙일 때 얼굴·귀 피부색만 남자 몸 피부색으로 코드에서 바꿉니다.
- 헤어는 회색으로만 받고, 색은 게임에서 코드로 입힙니다.
- 몸에 붙일 때: 턱을 몸의 원래 턱 위치에 맞추고 2px 더 내립니다. 옆모습은 턱 뒤쪽 선이 목폴라에 닿을 때까지 내립니다.
- 턱 아래 머리(목 옆)는 몸 뒤에 그립니다.

## 최종 프롬프트 — 여자

`reference/base_female_head_grey.png` 첨부, `[HAIR]`만 바꿉니다.

```
Use the attached image as the exact template: same 2x2 layout, same head size, same face, same eyes, same skin, same outline thickness, same position in every cell. HEAD ONLY: no neck, no body — the face ends at the chin outline exactly like the template.

DO NOT redraw the face. In the side view, keep exactly the same jaw angle, jaw length and chin position as the template.

Change ONLY the hairstyle: [HAIR]

The hair must have a thick, smooth black outline on every edge, the same thickness as the template.

Hair length must be the SAME in all four views: long hair, ponytails and braids hang down to the same length in front, side and back views. Draw the full length of the hair; never crop or cut it flat. All hair must fit completely inside each cell with white space around it.

Hair color rule: neutral grey only, exactly like the template — dark grey shadows, medium grey (#9A9A9A) base, light grey lit areas, near-white glossy highlight streaks. No other hair color, no colored tint. Hair accessories (ties, clips) also in grey.

Cell 1 (top-left): front view, eyes open, smiling.
Cell 2 (top-right): side view facing right.
Cell 3 (bottom-left): back view.
Cell 4 (bottom-right): exact copy of Cell 1, only the eyes are closed (happy smile). No hands.

Pure white background, no body, no text, no shadows.
```

## 최종 프롬프트 — 남자

같은 기준 머리 첨부, `[HAIR]`만 바꿉니다.

```
Use the attached image as the exact template: same 2x2 layout, same head size, same face, same eyes, same skin, same outline thickness, same position in every cell. HEAD ONLY: no neck, no body — the face ends at the chin outline exactly like the template.

DO NOT redraw the face. In the side view, keep exactly the same jaw angle, jaw length and chin position as the template.

Change ONLY the hairstyle to a MALE hairstyle: [HAIR]

The hair must have a thick, smooth black outline on every edge, the same thickness as the template.

Hair length must be the SAME in all four views. Draw the full hair; never crop or cut it flat. All hair must fit completely inside each cell with white space around it.

Hair color rule: neutral grey only, exactly like the template — dark grey shadows, medium grey (#9A9A9A) base, light grey lit areas, near-white glossy highlight streaks.

Cell 1 (top-left): front view, eyes open, smiling.
Cell 2 (top-right): side view facing right.
Cell 3 (bottom-left): back view.
Cell 4 (bottom-right): exact copy of Cell 1, only the eyes are closed (happy smile). No hands.

Pure white background, no text, no shadows.
```

## 여자 헤어 9종 (확정)

| 번호 | 한글 | 영어 이름 (파일명) | [HAIR] 문구 |
|---|---|---|---|
| 01 | 포니테일 | ponytail | high ponytail with straight bangs, tail reaching the shoulder blades |
| 02 | 긴 웨이브 | long_wavy | long soft wavy hair down past the shoulders, side-swept bangs |
| 03 | 긴 생머리 | long_straight | long straight hair down to the shoulder blades with straight bangs |
| 04 | 레이어드 | layered | shoulder-length layered hair with flipped-out ends and wispy bangs |
| 05 | 단발 | bob | chin-length straight bob with straight bangs |
| 06 | 하프업 | half_up | half-up hairstyle: top half tied in a small bun, rest long and straight down the back |
| 07 | 뿌까머리 | double_buns | two round buns on both sides of the top of the head (Chinese-style double buns), each bun tightly wrapped, straight blunt bangs, no loose strands hanging down |
| 08 | 숏컷 | pixie_cut | short pixie cut with side-swept bangs, ears visible |
| 09 | 똥머리 | messy_bun | messy bun on top of the head with a few loose strands and short bangs |

제외: 사이드 땋기(side_braid), 양갈래 땋기(twin_braids), 양갈래 묶음(twin_tails)

## 남자 헤어 9종 (제작 예정)

| 번호 | 한글 | 영어 이름 | [HAIR] 문구 |
|---|---|---|---|
| 01 | 모히칸 | mohawk | short mohawk, spiky strip on top, very short buzzed sides |
| 02 | 투블럭 | two_block | two-block cut: longer straight hair on top falling to the forehead, short buzzed sides |
| 03 | 댄디컷 | dandy_cut | neat short dandy cut with soft straight bangs covering the forehead |
| 04 | 리프컷 | leaf_cut | side-parted leaf cut, bangs swept to one side like a leaf, ears partly covered |
| 05 | 스포츠머리 | crew_cut | very short crew cut, even length all over |
| 06 | 반삭 | buzz_cut | buzz cut, almost shaved, visible scalp shape |
| 07 | 포마드 | pompadour | slicked-back pompadour, hair combed up and back with volume on top, short sides |
| 08 | 곱슬 파마 | curly_perm | short curly perm, fluffy round curls all over |
| 09 | 장발 묶음 | low_ponytail | shoulder-length hair tied in a small low ponytail at the back of the neck |

## 남자 예비 3종

| 번호 | 한글 | 영어 이름 | [HAIR] 문구 |
|---|---|---|---|
| 10 | 가르마 펌 | curtain_perm | middle part with soft wavy curtain bangs on both sides |
| 11 | 스파이키 | spiky | short spiky hair, spikes pointing upward and outward |
| 12 | 남자 똥머리 | man_bun | man bun: hair tied in a small bun on top of the head, short sides |
