# server/output

执行仲裁后的音频/TTS、USB 震动命令并反馈执行结果。不得绕过仲裁或重新识别；断电眼镜不具备继续告警能力。

当前 `executor.py` 只接受 `OutputDecision`，执行前复核 session/期限并返回 applied/rejected/failed；实际 TTS 与震动 transport 尚未接入。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
