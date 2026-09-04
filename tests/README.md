# tests

当前标准库 unittest 共 25 项：基础检查 13 项、Phase 1 来源审核 12 项（含用户非商业测试范围），均为工具正反例，不是 USB/模型/业务单测。执行 .venv/Scripts/python.exe -m unittest discover -s tests -v。后续按 Phase 增加真实协议/业务测试。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
