# tests

当前 unittest 共 78 项：基础 14、来源审核 12、协议/输入 21、回放 10、控制/时钟/传感器 19、串口 2。执行 .venv/Scripts/python.exe -m unittest discover -s tests -v。安装可选 pyserial 后其内存回环测试通过；不安装时该项明确 skip。其余为标准库模拟测试，未运行固件/真实串口/模型；JPEG 标记帧不保证可解码，最大帧不是吞吐指标。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
