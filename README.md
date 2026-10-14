# zoom-transcribe

Zoom会議の音声（PCから出ている音）を、研究室サーバーのGPU（faster-whisper large-v3）でリアルタイムに文字起こしする。

- `server.py` … サーバー側。WebSocketで音声を受け取り、文字起こしした結果を返す（ポート18765）
- `client.py` … Windows PC側。WASAPIループバックでPCの出力音を取り込み、5秒ごとにサーバーへ送る。結果は `~/授業録音/日時.txt` に保存する

## セットアップ（初回のみ）

サーバー:
```
python3 -m venv .venv
.venv/bin/pip install faster-whisper websockets numpy
```

Windows PC:
```
pip install pyaudiowpatch numpy scipy websockets
```

## 毎回の手順

1. サーバーで `tmux new -s whisper` → `cd ~/zoom-transcribe` → `CUDA_VISIBLE_DEVICES=0 .venv/bin/python server.py`。`ready` が出たら `Ctrl+B` → `D`
2. VS Code の「ポート」タブで 18765 を転送する（または PC の PowerShell で `ssh -L 18765:localhost:18765 <user>@<server>`）
3. Zoom に入ってから、PC の PowerShell で `python client.py`
4. 終わったら PC で `Ctrl+C`、サーバーで `tmux attach -t whisper` → `Ctrl+C`（GPUメモリを解放）

## 注意

- Zoom のスピーカー設定を Windows の既定の出力デバイスと同じにする
- GPU が使用中なら `nvidia-smi` で空きを確認し、`CUDA_VISIBLE_DEVICES` を変える
