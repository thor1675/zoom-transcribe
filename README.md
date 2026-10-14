# zoom-transcribe

Zoom会議の音声（PCから出ている音）を、研究室サーバーのGPU（Qwen3-ASR-1.7B）でリアルタイムに文字起こしする。

- `server.py` … サーバー側（Qwen3-ASR-1.7B）。WebSocketで音声を受け取り、文字起こしした結果を返す（ポート18765）。`terms.txt` の専門用語をヒントとして渡す。無音区間はSilero VADで落とす（無音のまま渡すと用語リストをそのまま出力するため）
- `server_whisper.py` … 旧版のサーバー（faster-whisper large-v3）。比較用に残している
- `terms.example.txt` … 専門用語ファイルの例。`cp terms.example.txt terms.txt` してから授業や会議に合わせて書き換える（`terms.txt` はgit管理外）
- `client.py` … Windows PC側。WASAPIループバックでPCの出力音を取り込み、10秒ごとにサーバーへ送る。結果は `~/授業録音/日時.txt` に保存する

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
2. VS Code の「ポート」タブで 18765 を転送する（または PC の PowerShell で `ssh -L 18765:localhost:18765 <user>@<server>`）
3. Zoom に入ってから、PC の PowerShell で `python client.py`
4. 終わったら PC で `Ctrl+C`、サーバーで `tmux attach -t whisper` → `Ctrl+C`（GPUメモリを解放）

## 注意

- `terms.txt` を変えたらサーバーを再起動する

- Zoom のスピーカー設定を Windows の既定の出力デバイスと同じにする
- GPU が使用中なら `nvidia-smi` で空きを確認し、`CUDA_VISIBLE_DEVICES` を変える
