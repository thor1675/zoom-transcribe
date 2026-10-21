# zoom-transcribe

Zoom会議の音声（PCから出ている音）を、研究室サーバーのGPU（Qwen3-ASR-1.7B）でリアルタイムに文字起こしする。

- `server.py` … サーバー側（Qwen3-ASR-1.7B）。WebSocketで音声を受け取り、文字起こしした結果を返す（ポート18765）。`terms.txt` の専門用語をヒントとして渡す。無音区間はSilero VADで落とす（無音のまま渡すと用語リストをそのまま出力するため）
- `server_whisper.py` … 旧版のサーバー（faster-whisper large-v3、ポート18766）。比較用に残している
- `terms.example.txt` … 専門用語ファイルの例。`cp terms.example.txt terms.txt` してから授業や会議に合わせて書き換える（`terms.txt` はgit管理外）
- `client.py` … Windows PC側。WASAPIループバックでPCの出力音を取り込み、10秒ごとにサーバーへ送る。起動しているサーバー（qwen・whisper）すべてに同じ音声を送り、結果はモデルごとに `~/documents/zoom-transcribe/録音/日時_モデル名.txt` に保存する

## セットアップ（初回のみ）

サーバー:
```
python3 -m venv .venv-qwen
.venv-qwen/bin/pip install qwen-asr websockets faster-whisper
```

Windows PC:
```
pip install pyaudiowpatch numpy scipy websockets
```

## 毎回の手順

1. サーバーで `tmux new -s whisper` → `cd ~/zoom-transcribe` → `CUDA_VISIBLE_DEVICES=0 .venv-qwen/bin/python server.py`。`ready` が出たら `Ctrl+B` → `D`
2. PC の PowerShell で `ssh -N -L 28765:127.0.0.1:18765 -L 28766:127.0.0.1:18766 <user>@<server>` を実行し、開いたままにする（VS Code のポート転送は宛先が IPv6 になってつながらないことがあるので使わない）
3. Zoom に入ってから、PC の PowerShell で `python client.py`
4. 終わったら PC で `Ctrl+C`、サーバーで `tmux attach -t whisper` → `Ctrl+C`（GPUメモリを解放）

## 両方のモデルで同時に文字起こしする

別のtmuxで `CUDA_VISIBLE_DEVICES=1 .venv/bin/python server_whisper.py` も起動する。`client.py` は両方につなぎ、片方しか起動していなければそちらだけ使う。

## Slack通知

`notify.py` の `KEYWORDS`（小テスト・課題・提出など）が文字起こしに出てきたら、Slack に通知する。Qwen と Whisper のどちらかに出てくれば通知する。同じ言葉は2分間続けて通知しない。
PC の `client.py` と同じフォルダに `slack_webhook.txt` を置き、Slack の Incoming Webhook の URL を1行だけ書く（git管理外）。ファイルがなければ通知しない。

## 注意

- `terms.txt` を変えたらサーバーを再起動する

- Zoom のスピーカー設定を Windows の既定の出力デバイスと同じにする
- GPU が使用中なら `nvidia-smi` で空きを確認し、`CUDA_VISIBLE_DEVICES` を変える
