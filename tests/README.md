# tests

当前 Python unittest 共 92 项，包含基础/来源/协议回放/控制传感器/串口、7 项固件静态合同和 6 项 localhost API。执行 `.venv/Scripts/python.exe -m unittest discover -s tests -v`。前端另有 3 项 Vitest 交互测试以及 typecheck/build。串口只做内存回环；未运行固件编译、真实串口或模型，JPEG 标记帧不保证可解码，最大帧不是吞吐指标。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
