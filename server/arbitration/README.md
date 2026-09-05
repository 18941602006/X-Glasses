# server/arbitration

接收结构化事件，按风险/失效、局部方向、地图、找物/阅读、聊天优先级仲裁，处理有效期/取消/节流。禁止读帧或加载模型；输出统一决策。

当前 `core.py` 实现固定八级优先级、同类最新替换、会话/有效期、取消和重复限频；不包含 TTS 或硬件执行。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
