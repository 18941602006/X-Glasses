# server/input

Phase 2A：frames/stream/recording 提供有限组帧、单次消费、会话隔离、短读写及显式录制回放；link.py 提供握手/心跳、源时间/误差筛选、传感器和 ACK 生命周期；serial_port.py 显式本地端口适配，不自动打开或接受网络 URL。只有模拟/内存回环测试，未连接硬件；不加载模型或播放告警。合同见 [USB v1](../../docs/protocol/USB_V1.md) 与 [控制合同](../../docs/protocol/CONTROL_V1.md)。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
