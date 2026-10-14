import queue, datetime, pathlib, time
import numpy as np
import pyaudiowpatch as pyaudio
from scipy.signal import resample_poly
from websockets.sync.client import connect

CHUNK_SEC = 10
OUT = pathlib.Path.home() / "documents" / "zoom-transcribe" / "録音" ; OUT.mkdir(parents=True, exist_ok=True)
# 送り先のサーバー。起動していないものは飛ばす
SERVERS = {"qwen": "ws://localhost:18765", "whisper": "ws://localhost:18766"}

stamp = f"{datetime.datetime.now():%Y%m%d_%H%M}"
conns = {}
for name, url in SERVERS.items():
    try:
        ws = connect(url, max_size=None, open_timeout=3)
    except Exception:
        print(f"  {name}：つながらないので使わない（{url}）")
        continue
    conns[name] = (ws, open(OUT / f"{stamp}_{name}.txt", "a", encoding="utf-8"))
    print(f"  {name}：接続しました")
if not conns:
    raise SystemExit("サーバーに1つもつながりませんでした")

p = pyaudio.PyAudio()
dev = p.get_default_wasapi_loopback()
ch, rate = dev["maxInputChannels"], int(dev["defaultSampleRate"])
q = queue.Queue()

def cb(data, n, t, s):
    q.put(data); return (None, pyaudio.paContinue)

def send(buf):
    a = np.frombuffer(buf, np.int16).reshape(-1, ch).mean(axis=1)
    a = np.clip(resample_poly(a, 16000, rate), -32768, 32767)
    data = a.astype(np.int16).tobytes()
    # 先に全サーバーへ送ってから受け取る（各サーバーが並行して処理できる）
    for ws, _ in conns.values():
        ws.send(data)
    el = time.strftime("%H:%M:%S", time.gmtime(time.time() - start))
    for name, (ws, txt) in conns.items():
        text = ws.recv()
        if text:
            print(f"[{el}] {name:>7}：{text}")
            txt.write(f"[{el}] {text}\n"); txt.flush()

stream = p.open(format=pyaudio.paInt16, channels=ch, rate=rate, input=True,
                input_device_index=dev["index"], stream_callback=cb)
print(f"● 録音中：{dev['name']}（Ctrl+Cで終了）")
buf, start = b"", time.time()
try:
    while True:
        try:
            buf += q.get(timeout=1)
        except queue.Empty:
            continue
        if len(buf) >= rate * ch * 2 * CHUNK_SEC:
            send(buf); buf = b""
except KeyboardInterrupt:
    stream.stop_stream(); stream.close()
    if buf: send(buf)
    for ws, txt in conns.values():
        ws.close(); txt.close()
    print("■ 停止しました")
