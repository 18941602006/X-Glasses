# server/perception/assist

Phase 5 起：OCR、信号灯状态、AI 对话、地图事件适配；先审核开源可复用模块。只产出结构化事件，不提供通行许可或直接输出。

`contracts.py` 实现模型/供应商无关的严格事件边界与响应解析。2026-10-21 新增 `deepseek.py` 和 `tools.dialogue_pc` 官方实际调用入口；Key 从本机环境/忽略配置读取，默认只发文字，图片需要显式授权。未配置时明确失败，OCR/灯模型仍未接通。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
