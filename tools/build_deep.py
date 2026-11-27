"""딥 리허설 원본(GPT) → 게임용 deep.html (음성 압축)
- 음성 뱅크: 16비트 PCM → IMA ADPCM 4비트 (길이·타이밍 그대로, 브라우저 코덱 의존 없음)
- 심판 카운트 미리듣기: WAV → AAC(m4a)
사용: python3 -I build_deep.py <원본.html> <출력.html> <작업폴더>
"""
import sys, json, base64, struct, subprocess, os, math

STEP = [7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767]
IDX = [-1,-1,-1,-1,2,4,6,8]

def dec_step(code, pred, idx):
    st = STEP[idx]
    d = st >> 3
    if code & 4: d += st
    if code & 2: d += st >> 1
    if code & 1: d += st >> 2
    pred = pred - d if code & 8 else pred + d
    pred = max(-32768, min(32767, pred))
    idx = max(0, min(88, idx + IDX[code & 7]))
    return pred, idx

def encode(samples):
    pred0 = samples[0] if samples else 0
    pred, idx = pred0, 0
    codes = []
    out = []
    for s in samples:
        st = STEP[idx]
        diff = s - pred
        code = 0
        if diff < 0:
            code = 8; diff = -diff
        if diff >= st: code |= 4; diff -= st
        if diff >= st >> 1: code |= 2; diff -= st >> 1
        if diff >= st >> 2: code |= 1
        pred, idx = dec_step(code, pred, idx)
        codes.append(code); out.append(pred)
    if len(codes) % 2: codes.append(0)
    body = bytes((codes[i] | (codes[i+1] << 4)) for i in range(0, len(codes), 2))
    head = struct.pack('<Ih', len(samples), pred0)
    return head + body, out

def snr(a, b):
    sig = sum(x*x for x in a) or 1
    err = sum((x-y)**2 for x, y in zip(a, b)) or 1
    return 10*math.log10(sig/err)

src, dst, work = sys.argv[1:4]
lines = open(src, encoding='utf-8').read().split('\n')

# 1) 음성 뱅크
vi = next(i for i, l in enumerate(lines) if 'id="voice-data"' in l)
l = lines[vi]
a, b = l.index('>') + 1, l.rindex('</script>')
voices = json.loads(l[a:b])
voices.pop('entry', None)  # 사용자 요청: '대회장 입장(Entry, competition area)' 음성 삭제
# 프리폴·마우스필·리필 음성은 코치(Breathe)와 같은 목소리로 교체 (macOS Daniel, say -r 225로 Breathe보다 약 20% 빠르게, tools/voices/*.wav)
import wave as _wave
for _k in ('free', 'fill', 'refill'):
    _w = _wave.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voices', _k + '.wav'))
    assert _w.getframerate() == 11025 and _w.getnchannels() == 1 and _w.getsampwidth() == 2
    voices[_k] = base64.b64encode(_w.readframes(_w.getnframes())).decode()
packed, worst = {}, (99, '')
for k, v in voices.items():
    raw = base64.b64decode(v)
    smp = list(struct.unpack('<%dh' % (len(raw)//2), raw))
    blob, dec = encode(smp)
    q = snr(smp, dec)
    if q < worst[0]: worst = (q, k)
    packed[k] = base64.b64encode(blob).decode()
lines[vi] = l[:a] + json.dumps(packed, separators=(',', ':')) + l[b:]
print('voices', len(packed), 'worst SNR %.1f dB (%s)' % worst)

# 2) 디코더 교체 (PCM 읽기 → ADPCM 풀기). 이후의 정규화(.85/peak)는 원본 그대로
js = '\n'.join(lines)
old = """    const raw=atob(voices[key]);
    samples=new Float32Array(raw.length/2);
    let peak=0;
    for(let i=0;i<samples.length;i++){
      const value=(raw.charCodeAt(i*2)|(raw.charCodeAt(i*2+1)<<8))<<16>>16;
      samples[i]=value/32768;
      peak=Math.max(peak,Math.abs(samples[i]));
    }"""
new = """    /* 음성은 IMA ADPCM으로 압축해 저장 (게임 탑재 시 용량 절감). 머리: 샘플 수(4) + 첫 값(2) */
    const raw=atob(voices[key]);
    const n=(raw.charCodeAt(0)|raw.charCodeAt(1)<<8|raw.charCodeAt(2)<<16|raw.charCodeAt(3)<<24)>>>0;
    let pred=(raw.charCodeAt(4)|raw.charCodeAt(5)<<8)<<16>>16, idx=0, peak=0;
    samples=new Float32Array(n);
    for(let i=0;i<n;i++){
      const code=(raw.charCodeAt(6+(i>>1))>>((i&1)*4))&15, st=ADPCM_STEP[idx];
      let d=st>>3; if(code&4)d+=st; if(code&2)d+=st>>1; if(code&1)d+=st>>2;
      pred=Math.max(-32768,Math.min(32767,code&8?pred-d:pred+d));
      idx=Math.max(0,Math.min(88,idx+ADPCM_IDX[code&7]));
      samples[i]=pred/32768;
      peak=Math.max(peak,Math.abs(samples[i]));
    }"""
assert js.count(old) == 1
js = js.replace(old, new)
anchor = "const buffers=new Map();"
assert js.count(anchor) == 1
js = js.replace(anchor, anchor + "\nconst ADPCM_STEP=" + json.dumps(STEP, separators=(',', ':')) + ",ADPCM_IDX=[-1,-1,-1,-1,2,4,6,8];")

# 2-1) 대회 모드 시작 콜 '대회장 입장' 삭제 (타이밍은 그대로: 0초 = 입장, 첫 심판 콜은 준비 시간 -120초)
old = "if (plan.competition) return [cue(0,'entry','대회장 입장'), ...refereeCalls.map("
assert js.count(old) == 1
js = js.replace(old, "if (plan.competition) return [...refereeCalls.map(")

# 2-2) 대회 모드 기본 준비 시간 125초 → 120초 (입장 음성이 빠져 시작하자마자 'Two minutes' 콜)
for old, new in [('name="wait" type="number" min="35" max="900" value="125"', 'name="wait" type="number" min="35" max="900" value="120"'),
                 ("form.elements.wait.min=competition?'123':'35';", "form.elements.wait.min=competition?'120':'35';")]:
    assert js.count(old) == 1, old
    js = js.replace(old, new)

# 2-3) 테마: 데모(어두운 화면) → 게임 방 화면과 같은 밝은 테마. 원본 CSS 뒤에 덮어쓰기만 한다
THEME = """
/* ---- 게임 테마 (프리다이빙리조트 방 화면과 맞춤) ---- */
:root{color-scheme:light;--bg:transparent;--panel:#fff;--edge:#D5E2EA;--text:#1B2A33;--muted:#5A6B76;--mint:#0E8FA0;--accent-bg:#E3F1FA;--accent-ink:#145A8A}
body{background:transparent;font-family:'Noto Sans KR',-apple-system,'Apple SD Gothic Neo',sans-serif;font-size:15px}
.wrap,.mobile{width:100%;max-width:540px;margin-inline:auto}
.mast{min-height:44px;border-bottom:1px solid var(--edge)}
.mast strong{font-weight:900}.symbol{font-size:22px}
.mast-label{color:var(--accent-ink)!important;font-weight:700;font-size:13px}
.intro,.mobile .intro{padding:14px 0 12px}
h1,.mobile .intro h1{font-size:24px;font-weight:900;letter-spacing:-.03em;line-height:1.3}
h2{font-weight:900}
.intro p{font-size:13px;margin-top:4px}
.panel{background:#fff;border:0;border-radius:14px;box-shadow:0 2px 10px rgba(20,60,80,.1);padding:16px}
legend,.fields label,.review label,.check{color:var(--muted)}
.mode{border:1.5px solid var(--edge);background:#fff}
.mode:has(:checked){border-color:var(--mint);background:var(--accent-bg)}
select,input[type=number],textarea{background-color:#fff;color:var(--text);border:1.5px solid var(--edge);border-radius:10px}
button{border-radius:10px;font-weight:800}
.primary{background:var(--mint);color:#fff;border:0}
.secondary{background:var(--accent-bg);color:var(--accent-ink);border:0}
button:active{transform:translateY(1px)}
:focus-visible{outline-color:var(--mint)}
.mobile a{color:var(--accent-ink)}
.mobile #now{color:var(--mint);font-weight:800}
.readouts{color:var(--muted)}.readouts strong{color:var(--text);font-weight:900}
#meter{font-weight:800;color:var(--accent-ink)}
.alarm-entry{border-top:1px solid var(--edge)}
.mobile summary{color:var(--text)}
.note{color:var(--muted)}
.viewport{border:0;border-radius:14px;color:#EFF8F7}
.viewport h2,.scene-top span{color:#EFF8F7}.scene-copy span{color:#A0F3D9}
.wrap,.mobile{padding-right:4px}
"""
old = "</style></head>"
assert js.count(old) == 1
js = js.replace(old, THEME + old, 1)
old = "<style>\n:root{color-scheme:dark;"
assert js.count(old) == 1
js = js.replace(old, "<style>\n@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@500;700;900&display=swap');\n:root{color-scheme:dark;", 1)
js = js.replace('<meta name="theme-color" content="#06171d">', '<meta name="theme-color" content="#D6EEFA">', 1)

# 2-4) 연습 모드: 드롭다운 → 한 화면 안 [대회] [트레이닝] 버튼 (원래 select는 숨겨 두고 값만 바꿈)
old = '<label>연습 모드<select name="mode"><option value="competition">대회 리허설 · 영어 음성</option><option value="training">자유 트레이닝 · 영어 다이빙 콜</option></select></label>'
new = ('<div class="modeseg" role="group" aria-label="연습 모드">'
       '<button type="button" data-mode="competition" aria-pressed="true"><b>대회</b><small>심판 콜 · 실격 규칙</small></button>'
       '<button type="button" data-mode="training" aria-pressed="false"><b>트레이닝</b><small>다이빙 콜만</small></button></div>'
       '<select name="mode" hidden aria-hidden="true" tabindex="-1"><option value="competition">대회</option><option value="training">트레이닝</option></select>')
assert js.count(old) == 1
js = js.replace(old, new)
old = "get('add').onclick=()=>addAlarm(get('kind').value);"
assert js.count(old) == 1
js = js.replace(old, """for(const b of form.querySelectorAll('.modeseg button')) b.onclick=()=>{
  form.elements.mode.value=b.dataset.mode;
  for(const x of form.querySelectorAll('.modeseg button')) x.setAttribute('aria-pressed',x===b);
  form.elements.mode.onchange();
};
""" + old)
js = js.replace(".viewport{border:0;border-radius:14px;", """.modeseg{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.modeseg button{margin:0!important;display:flex;flex-direction:column;align-items:center;gap:2px;padding:12px 6px;background:var(--accent-bg);color:var(--accent-ink);border:2px solid transparent}
.modeseg button b{font-size:17px;font-weight:900}.modeseg button small{font-size:11px;font-weight:700;opacity:.8}
.modeseg button[aria-pressed=true]{background:var(--mint);color:#fff}
.viewport{border:0;border-radius:14px;""", 1)

# 2-5) 설정 정리 (2026-11-27 사용자와 확정)
#  ① 입장 후 준비 120초 고정  ② 하강·상승은 속도(m/초) 입력, 기본 1m/초 → 시간 자동 계산
#  ③ 기본 알람: 프리폴 → 마우스필 → 턴 준비 (리필·일반 수심은 추가 선택, 턴 준비 앞에 끼움)
#  ④ 턴 준비·일반 수심은 기계음(삐빅) 고정, 프리폴·마우스필·리필은 음성/기계음 선택
#  ⑤ 실제 턴은 목표 수심에서 'turn' 음성 고정  ⑥ 수심 안내 음성은 하강·상승 모두 기본 꺼짐, 이름 변경
def rep(old, new):
    global js
    assert js.count(old) == 1, old[:80]
    js = js.replace(old, new)

rep('<label>입장 후 준비 (초)<input name="wait" type="number" min="35" max="900" value="120" required></label><label>하강 소요 (초)<input name="down" type="number" min="5" max="300" value="30" required></label><label>상승 소요 (초)<input name="up" type="number" min="5" max="300" value="30" required></label></div>',
    '<label>입장 후 준비<span class="fixed">120초 (고정)</span><input name="wait" type="hidden" value="120"></label>'
    '<label>하강 속도 (m/초)<input name="vdown" type="number" min="0.3" max="3" step="0.05" value="1" required></label>'
    '<label>상승 속도 (m/초)<input name="vup" type="number" min="0.3" max="3" step="0.05" value="1" required></label></div>'
    '<p class="note" id="timecalc"></p>')
rep('<p class="note">하강 중 알람을 개별적으로 추가하세요. 턴 알람의 기본값은 목표 수심 2m 전입니다.</p>',
    '<p class="note">프리폴·마우스필 수심을 넣으세요. 비워 두면 울리지 않습니다. 턴 준비는 항상 울리며 기본값은 목표 수심 2m 전입니다.</p>')
rep('<option value="free">프리폴</option><option value="fill">마우스필</option><option value="refill">리필 (2차 차징)</option><option value="preturn">턴 예고</option><option value="extra">일반 수심</option>',
    '<option value="refill">리필 (2차 차징)</option><option value="extra">일반 수심</option>')
rep('<label class="check"><input name="desc" type="checkbox"> 하강 수심 음성 · 20m부터 10m마다</label>',
    '<label class="check"><input name="desc" type="checkbox"> 하강 수심 안내 음성</label>')
rep('<label class="check"><input name="asc" type="checkbox" checked> 상승 수심 음성 · 10m마다, 마지막 5~1m</label>',
    '<label class="check"><input name="asc" type="checkbox"> 상승 수심 안내 음성</label>')

rep("const names = {free:'프리폴', fill:'마우스필', refill:'리필', preturn:'턴 예고', extra:'일반 수심'};",
    "const names = {free:'프리폴', fill:'마우스필', refill:'리필', preturn:'턴 준비', extra:'일반 수심'};")
rep('<select><option value="voice">남성 컴퓨터 음성</option><option value="beep">삐빅</option></select>',
    '<select><option value="voice">실제 음성</option><option value="beep">기계음 (삐빅)</option></select>')
rep("  field.required = kind !== 'preturn';", "  field.required = false;")
rep("  if(kind==='extra') { select.value='beep'; select.disabled=true; }\n  row.querySelector('button').onclick=()=>row.remove();\n  editor.append(row);",
    "  if(kind==='extra'||kind==='preturn') { select.value='beep'; select.disabled=true; }\n"
    "  if(kind==='preturn') row.querySelector('button').remove(); else row.querySelector('button').onclick=()=>row.remove();\n"
    "  const turn=editor.querySelector('[data-kind=preturn]');\n"
    "  if(turn) editor.insertBefore(row,turn); else editor.append(row);")
rep("  form.elements.wait.min=competition?'120':'35';\n}",
    "  const vd=Number(form.elements.vdown.value), vu=Number(form.elements.vup.value);\n"
    "  get('timecalc').textContent = depth>0&&vd>0&&vu>0 ? '하강 '+Math.round(depth/vd)+'초 · 상승 '+Math.round(depth/vu)+'초 · 총 '+((t)=>Math.floor(t/60)+'분 '+(t%60)+'초')(Math.round(depth/vd)+Math.round(depth/vu)) : '';\n}")
rep("addAlarm('preturn');", "addAlarm('preturn');addAlarm('free');addAlarm('fill');")
rep("    down:Number(data.get('down')),up:Number(data.get('up')),",
    "    down:Math.round(Number(data.get('depth'))/Number(data.get('vdown'))),up:Math.round(Number(data.get('depth'))/Number(data.get('vup'))),")
rep("    alarms:Array.from(editor.children,row=>({kind:row.dataset.kind,label:names[row.dataset.kind],\n      meters:Number(row.querySelector('input').value||2),sound:row.querySelector('select').value}))};",
    "    alarms:Array.from(editor.children,row=>({kind:row.dataset.kind,label:names[row.dataset.kind],\n      meters:Number(row.querySelector('input').value||(row.dataset.kind==='preturn'?2:0)),sound:row.querySelector('select').value}))\n      .filter(a=>a.kind==='preturn'||a.meters>0)};")
rep("  list.push(cue(down,'beep','턴 · 상승 시작','alarm'));", "  list.push(cue(down,'turn','턴 · 상승 시작','alarm'));")
# ⑦ 하강 수심 안내는 턴 준비 3초 전부터 빼서 턴 준비·턴 소리와 겹치지 않게
rep("  if(plan.desc) for(let m=20;m<=depth;m+=10) list.push(cue(down*m/depth,'down'+m,m+' meters down','depth'));",
    "  const turnPrep=plan.alarms.find(a=>a.kind==='preturn'), prepAt=down*Math.max(0,depth-(turnPrep?turnPrep.meters:2))/depth;\n"
    "  if(plan.desc) for(let m=20;m<=depth;m+=10) if(down*m/depth<=prepAt-3+1e-6) list.push(cue(down*m/depth,'down'+m,m+' meters down','depth'));")
js = js.replace(".viewport{border:0;border-radius:14px;", ".fields .fixed{display:flex;align-items:center;min-height:42px;margin-top:5px;padding:0 10px;border-radius:10px;background:#F1F4F6;color:var(--text);font-weight:800}\n.viewport{border:0;border-radius:14px;", 1)

# 2-6) 전체 소리 크기 절반 (휴대폰 최대 볼륨에서 너무 커서). 음성·알람·틱·미리듣기 모두
rep("  gain.gain.value=level;", "  gain.gain.value=level*0.3;  /* 게임 탑재: 원본 대비 약 -10dB (귀로 듣기에 절반) */")
rep('<audio id="countdemo" controls preload="none" src="', '<audio id="countdemo" controls preload="none" onplay="this.volume=0.3" src="')

# 3) 미리듣기 WAV → AAC
pre = 'src="data:audio/wav;base64,'
a = js.index(pre) + len(pre)
b = js.index('"', a)
wav = os.path.join(work, 'countdemo.wav'); m4a = os.path.join(work, 'countdemo.m4a')
open(wav, 'wb').write(base64.b64decode(js[a:b]))
subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '32000', wav, m4a], check=True)
js = js[:a - len(pre)] + 'src="data:audio/mp4;base64,' + base64.b64encode(open(m4a, 'rb').read()).decode() + js[b:]
print('preview wav %d → m4a %d bytes' % (os.path.getsize(wav), os.path.getsize(m4a)))

open(dst, 'w', encoding='utf-8').write(js)
print('total %d → %d bytes' % (os.path.getsize(src), os.path.getsize(dst)))
