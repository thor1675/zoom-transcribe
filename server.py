import pathlib
import numpy as np, torch
from websockets.sync.server import serve
from qwen_asr import Qwen3ASRModel
from faster_whisper.vad import get_speech_timestamps

# 認識させたい専門用語（terms.txt に空白・改行区切りで書く。なければ使わない）
terms_file = pathlib.Path(__file__).with_name("terms.txt")
TERMS = " ".join(terms_file.read_text(encoding="utf-8").split()) if terms_file.exists() else ""

model = Qwen3ASRModel.from_pretrained(
    "Qwen/Qwen3-ASR-1.7B", dtype=torch.bfloat16,
    device_map="cuda:0", max_new_tokens=256)

def handler(ws):
    prev = ""
    for msg in ws:
        a = np.frombuffer(msg, np.int16).astype(np.float32) / 32768
        # 声のある区間だけを残す（無音だと用語リストをそのまま出力してしまうため）
        segs = get_speech_timestamps(a)
        if not segs:
            ws.send(""); continue
        a = np.concatenate([a[s["start"]:s["end"]] for s in segs])
        r = model.transcribe(audio=(a, 16000), language="Japanese",
                             context=TERMS + " " + prev[-100:])
        prev = r[0].text
        ws.send(prev)

with serve(handler, "localhost", 18765, max_size=None) as s:
    print("ready")
    s.serve_forever()
