# server/input

Phase 2A 第一部分：frames.py 有限 JPEG 组帧和单次消费；stream.py 会话清理/顺序过滤及可注入 ByteStream 短读写；recording.py 显式录制 API 与虚拟时间回放。无 pyserial 驱动、对时/握手/心跳或传感器解码；失效状态不直接播放告警。已做纯模拟测试，不加载模型。合同见 [USB v1](../../docs/protocol/USB_V1.md)。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
