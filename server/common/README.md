# server/common

Phase 2A：protocol.py 实现 v1 包头/CRC/有界增量解析与重同步，不依赖具体模型或业务层。除 JPEG 外类型只定义封装，不声称传感器语义/ACK/对时已实现。实际布局见 [USB v1](../../docs/protocol/USB_V1.md)。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
