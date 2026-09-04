# 架构 / V3

状态：目标架构；Phase 0 不含业务实现。版本选择在 Phase 1 锁定。

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

USB 合同与分层约束见 LAYER_CONTRACT；测试记录见 TEST_METRICS。地图/对话可依赖互联网，但绝不进入即时风险判断。具体二进制布局、阈值及传感器引脚仍待 Phase 1/2 冻结。
