# tests

当前标准库 unittest 共 57 项：基础检查 14 项、Phase 1 来源审核 12 项、USB 协议/输入/流适配 21 项、录制回放 10 项。执行 .venv/Scripts/python.exe -m unittest discover -s tests -v。USB 为纯模拟异常测试，未运行固件/真实串口/模型；测试 JPEG 标记帧不保证可解码，最大帧测试也不是吞吐指标。后续按 Phase 增加固件与实机测试。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
