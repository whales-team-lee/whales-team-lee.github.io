"""파도 소리 원본(직접 제작) → 게임용 무한반복 음원 wave.m4a
- 끝 2초와 처음 2초를 겹쳐(이퀄 파워 크로스페이드) 반복할 때 이음새가 들리지 않게 한다
- AAC로 압축. 압축 때 앞뒤에 붙는 빈 소리는 게임 코드가 재생 시 잘라낸다(loopStart/loopEnd)
사용: python3 -I build_wave.py <원본.wav> <출력.m4a> <작업폴더>   (macOS afconvert 필요)
"""
import sys, os, struct, math, aifc, subprocess

src, dst, work = sys.argv[1:4]
R, XF = 44100, 2.0                      # 작업 샘플레이트, 크로스페이드 길이(초)
pcm = os.path.join(work, 'wave_pcm.aif')   # 스테레오 WAV는 확장 형식이라 파이썬 wave가 못 읽어 AIFF(빅엔디언)로 작업
loop = os.path.join(work, 'wave_loop.aif')
subprocess.run(['afconvert', '-f', 'AIFF', '-d', 'BEI16@%d' % R, '-c', '2', src, pcm], check=True)

w = aifc.open(pcm)
ch, n = w.getnchannels(), w.getnframes()
raw = w.readframes(n)
w.close()
x = int(XF * R)
fb = 2 * ch                              # 한 프레임 바이트 수

head = struct.unpack('>%dh' % (x * ch), raw[:x * fb])
tail = struct.unpack('>%dh' % (x * ch), raw[(n - x) * fb:])
mix = []
for i in range(x):
    t = i / x
    a, b = math.cos(t * math.pi / 2), math.sin(t * math.pi / 2)   # 끝은 줄고 처음은 커짐
    for c in range(ch):
        v = tail[i * ch + c] * a + head[i * ch + c] * b
        mix.append(max(-32768, min(32767, int(round(v)))))
# 결과: 원본[x : n-x] + (끝 x프레임 ⨉ 처음 x프레임 겹침). 마지막이 원본 처음 x 지점으로 바로 이어진다
body = raw[x * fb:(n - x) * fb] + struct.pack('>%dh' % len(mix), *mix)
o = aifc.open(loop, 'wb')
o.setnchannels(ch); o.setsampwidth(2); o.setframerate(R)
o.writeframes(body)
o.close()

subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '64000', loop, dst], check=True)
print('loop %.1fs (원본 %.1fs - 겹침 %.1fs) → %s %d bytes' % ((n - x) / R, n / R, XF, os.path.basename(dst), os.path.getsize(dst)))
