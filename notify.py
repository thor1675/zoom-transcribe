import json, pathlib, threading, time, urllib.request

# 通知したい言葉。どれか1つでも文字起こしに出てきたらSlackに送る
KEYWORDS = ["小テスト", "確認テスト", "テスト", "試験", "課題", "提出", "締め切り", "締切",
            "レポート", "出席"]
COOLDOWN_SEC = 120  # 同じ言葉ではこの秒数のあいだ続けて通知しない

# Slack の Incoming Webhook の URL（git管理外。なければ通知しない）
_url_file = pathlib.Path(__file__).with_name("slack_webhook.txt")
WEBHOOK = _url_file.read_text(encoding="utf-8-sig").strip() if _url_file.exists() else ""
_last = {}

def _post(text):
    req = urllib.request.Request(WEBHOOK, data=json.dumps({"text": text}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        print(f"  Slack通知に失敗：{type(e).__name__} {e}")

def check(el, texts):
    """1回分の文字起こし（モデルごと）にキーワードがあればSlackに通知する"""
    if not WEBHOOK:
        return
    now = time.time()
    joined = " ".join(texts.values())
    hits = [k for k in KEYWORDS if k in joined and now - _last.get(k, 0) >= COOLDOWN_SEC]
    if not hits:
        return
    for k in hits:
        _last[k] = now
    lines = "\n".join(f"> {name}：{t}" for name, t in texts.items() if t)
    msg = f"🔔 [{el}] 「{'」「'.join(hits)}」\n{lines}"
    print(f"  → Slackに通知：{'、'.join(hits)}")
    # 通信待ちで録音が止まらないように別スレッドで送る
    threading.Thread(target=_post, args=(msg,), daemon=True).start()
