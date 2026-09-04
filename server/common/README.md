# server/common

Phase 2A：protocol.py 包头/CRC/有界解析；sensors.py 归一化 ToF/IMU/按键；clock.py 四时间戳与误差/过期；control.py 命令/ACK 线格式。不依赖模型或业务层。全为主机模拟验证，实际设备归一化/晶振/执行机构未验证。布局见 [USB v1](../../docs/protocol/USB_V1.md) 与 [控制合同](../../docs/protocol/CONTROL_V1.md)。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
