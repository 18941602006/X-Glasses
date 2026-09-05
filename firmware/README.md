# X-Glasses ESP32-S3 固件

当前为 Phase 2A 协议固件：ESP-IDF 5.5.4，精确组件 esp_tinyusb 2.2.1 / esp32-camera 2.1.7。实现 CDC 二进制解析、握手/心跳、CLOCK 四时间戳响应、session/sequence 过滤、命令参数/截止/去重与 ACK。默认只声明 CLOCK 能力；相机、ToF、IMU、按键和震动均未启用，START_STREAM/HAPTIC 会拒绝，STOP/CANCEL 只改变安全子集状态。不能把编译成功写成传感器或整机成功。

不经 CDC 输出文本日志，ESP-IDF 日志走 USB Serial/JTAG 控制台。USB OTG CDC 与下载口的实际切换、恢复模式及 DTR 行为尚未上板。默认描述符为总线供电；未完成峰值电流测量前不连接手机做负载测试。

协议：[USB v1](../docs/protocol/USB_V1.md)、[控制与传感器](../docs/protocol/CONTROL_V1.md)。固件不做 SLAM、盲道/斑马线、视觉/导航决策，也没有伪造模拟传感器为有效值。

## 构建

使用官方 ESP-IDF 环境：

```powershell
idf.py -C firmware set-target esp32s3
idf.py -C firmware build
```

当前仓库路径含非 ASCII，Espressif 不保证 Windows 下可用；团队编译时应将仓库复制到明确的短 ASCII 路径，并在该副本中构建。当前施工机按用户决定跳过本机 ESP-IDF 配置和编译。烧写必须由团队成员明确指定已识别的 XIAO 端口后单独执行，禁止无端口自动探测烧写。VS Code 可以使用 Espressif IDF 扩展调用同一 SDK，见 [VS Code 说明](../docs/construction/VSCODE.md)。
