import numpy as np
from websockets.sync.server import serve
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cuda", compute_type="float16")

def handler(ws):
    for msg in ws:
        a = np.frombuffer(msg, np.int16).astype(np.float32) / 32768
        segs, _ = model.transcribe(a, language="ja", vad_filter=True)
        ws.send("".join(s.text for s in segs))

with serve(handler, "localhost", 18766, max_size=None) as s:
    print("ready")
    s.serve_forever()
