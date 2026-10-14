import queue, datetime, pathlib, time
import numpy as np
import pyaudiowpatch as pyaudio
from scipy.signal import resample_poly
from websockets.sync.client import connect

CHUNK_SEC = 10
OUT = pathlib.Path.home() / "授業録音"; OUT.mkdir(exist_ok=True)
txt = open(OUT / f"{datetime.datetime.now():%Y%m%d_%H%M}.txt",
           "a", encoding="utf-8")
ws = connect("ws://localhost:18765", max_size=None)

p = pyaudio.PyAudio()
dev = p.get_default_wasapi_loopback()
ch, rate = dev["maxInputChannels"], int(dev["defaultSampleRate"])
q = queue.Queue()

def cb(data, n, t, s):
    q.put(data); return (None, pyaudio.paContinue)

def send(buf):
    a = np.frombuffer(buf, np.int16).reshape(-1, ch).mean(axis=1)
    a = np.clip(resample_poly(a, 16000, rate), -32768, 32767)
    ws.send(a.astype(np.int16).tobytes())
    text = ws.recv()
    if text:
        el = time.strftime("%H:%M:%S", time.gmtime(time.time() - start))
        print(f"[{el}] {text}")
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
    ws.close(); txt.close()
    print("■ 停止しました")
