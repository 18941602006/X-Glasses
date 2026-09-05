# 架构 / V3

Phase 2B 新增 `server/api` 标准库回环服务和独立 React/TS/Vite 调试台。API 默认 offline 且无命令 dispatcher；uint64 标识以十进制字符串跨 JSON，命令先记 pending，只有后端收到 ACK 才转终态。前端无串口依赖、不提供任意震动入口、不加载远程资源。Android UI 仍独立实现。

第二部分最新实现：common 增加 sensors/clock/control，input 增加 HostLink 与可选 SerialPort。主机可做握手/心跳/源时间估计与误差/ACK，但未与 MCU 互通；详细合同 CONTROL_V1、INPUT_RUNTIME。此前“尚未实现”小节保留第一部分历史，当前以本条及最新 HANDOFF 为准。

状态：目标架构；Phase 2A 已实现主机分包/组帧/流接口和原始录制回放，均仅模拟验证，其余业务未实现。来源版本见 Phase 1 台账，不等于安装锁。

2026-09-05 Phase 1 补充：来源审核快照见 ../dependencies/sources.audit.json（不是传递依赖安装锁）。ESP-IDF 5.5.4 / esp_tinyusb 2.2.1 / esp32-camera 2.1.7 进入编译候选，实际解析/编译尚未进行。旧底座只能逐模块适配；LocateAnything 许可描述差异、独立推理环境及手机关卡见 ../dependencies/ENVIRONMENT_GATES.md。硬件电平/引脚见 ../hardware/INTERFACE_REVIEW.md。

数据方向：眼镜采集 → USB 输入 → 公共帧/事件 → 感知 → 仲裁 → 输出。电脑前端通过 localhost 查询状态/提交命令，不能直控固件。最终 Android 复用业务语义，不依赖常驻电脑。

| 决策 | 理由与待验证项 |
| --- | --- |
| ESP-IDF + esp_tinyusb 原生 CDC | 复用现有栈；测 S3 Full-Speed 吞吐、PHY/恢复流程，不烧 eFuse |
| JPEG 有限分片、高优先级消息插入 | 限制排队延迟；测最坏帧长、短读写、坏包与恢复 |
| Python 主机接收与推理解耦 | 独立有界队列，丢过期图像，保留传感器/失效事件 |
| LocateAnything 独立进程/venv | 首次/失跟重定位，慢调用不能阻塞实时链路；Android 风险另验 |
| 输出仲裁统一处理有效期和优先级 | 风险/失效 > 局部方向 > 地图 > 找物/阅读 > 对话 |
| React/TS/Vite 电脑新前端 | Phase 2B；Android Kotlin/Compose 仅 Phase 6 |
| 原型单前向 ToF、USB 供电 | 标定/视差/视场与功耗实测；无电由主机提示断连 |

复用来源候选：OpenAIglasses_for_Navigation 后端通用模块、LocateAnything、PaddleSeg/PP-LiteSeg、MediaPipe、PaddleOCR、usb-serial-for-android。现在没有 vendor 源码或权重；Phase 1 固定来源 commit、代码/模型许可证、依赖兼容、可抽取模块与禁用旧功能耦合清单。

USB 实施合同见 [USB_V1](../protocol/USB_V1.md)，分层约束见 LAYER_CONTRACT；测试记录见 TEST_METRICS。地图/对话可依赖互联网，但绝不进入即时风险判断。消息头/JPEG/XGR1 已冻结主机布局，传感器语义、握手/ACK/对时、告警阈值、固件及供电实测仍待 2A 后续。当前帧未对时/未标定，不进入安全相关融合。
