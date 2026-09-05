# server/perception/assist

Phase 5 起：OCR、信号灯状态、AI 对话、地图事件适配；先审核开源可复用模块。只产出结构化事件，不提供通行许可或直接输出。

当前 `contracts.py` 实现模型/供应商无关的严格事件边界与响应解析。默认没有实际 provider、模型、密钥或联网能力。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
