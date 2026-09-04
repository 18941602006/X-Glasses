# 开源底座复用评审

## 结论

继续采用“开源适配优先”，但不把旧主程序整体搬入。已固定 [OpenAIglasses 源码](https://github.com/AI-FanGe/OpenAIglasses_for_Navigation/tree/46d90ab778e7503559a4d165e6659f7426207d95)，根 MIT 许可已核对；实际分发还须保留声明并核查所带依赖/素材。当前没有复制其业务源码。

| 文件 / 审阅深度 | 可复用内容 | 必须处理 |
| --- | --- | --- |
| bridge_io.py / 全文 | 最新帧缓冲、线程安全回调模式 | 原接口只有接收端墙钟时间并仅返回图像，可重复取得同一旧帧；改 session/frame/采样时间/TTL/消费序号与断连清空 |
| sync_recorder.py / 全文 | 录制生命周期、音视频写入封装 | 按帧数/固定 FPS 填充音频，不能证明设备采样同步；原始 JPEG/ToF/IMU/事件和时钟映射应独立记录，AVI 仅导出产物 |
| app_main.py / imports、路由及选段 | FastAPI/WebSocket 的组织方式 | 直接导入盲道/过街/YOLO/MediaPipe/音频并承载旧流程；仅抽框架思路，USB 输入重新接入 |
| navigation_master.py / imports、状态及选段 | 节流/状态组织思路 | 状态中心就是盲道和过街，不作为新任务状态机底座 |
| yolomedia.py / imports、函数结构 | 手部可视化和方向提示思路 | YOLO 掩码、手物二维重叠、直接播音耦合；LocateAnything 没有同等目标掩码，必须改时空融合并由仲裁输出 |
| audio_player/asr_core/omni_client / 结构 | 取消/音频分块接口候选 | 原音频输出面向 ESP32 网络广播且有旧语音映射；计算端输出适配、取消/抢占、密钥/上传同意均需重新核查 |

证据：[帧桥](https://github.com/AI-FanGe/OpenAIglasses_for_Navigation/blob/46d90ab778e7503559a4d165e6659f7426207d95/bridge_io.py)、[录制器](https://github.com/AI-FanGe/OpenAIglasses_for_Navigation/blob/46d90ab778e7503559a4d165e6659f7426207d95/sync_recorder.py)、[主程序](https://github.com/AI-FanGe/OpenAIglasses_for_Navigation/blob/46d90ab778e7503559a4d165e6659f7426207d95/app_main.py)、[拿取](https://github.com/AI-FanGe/OpenAIglasses_for_Navigation/blob/46d90ab778e7503559a4d165e6659f7426207d95/yolomedia.py)。

## 禁止直接安装旧 requirements

旧清单将 fastapi 0.104.1、torch 2.0.1、numpy 1.24.3、mediapipe 0.10.8、ultralytics 8.3.200 和多种音频 SDK 放在同一环境；同时列两个提供 cv2 的 OpenCV 分发包。其 README/清单定位 Python 3.9–3.11，不能把当前 Python 3.12.14 基础环境直接当旧底座运行环境。[固定清单](https://github.com/AI-FanGe/OpenAIglasses_for_Navigation/blob/46d90ab778e7503559a4d165e6659f7426207d95/requirements.txt)

处理：不安装整份、不顺带引入 Ultralytics 或旧权重。USB 输入、调试服务、视觉 worker 分开选择最小依赖；每个环境仅保留一种 cv2 分发包。版本快照与兼容性检查不是安装/功能验证。

## 固件与算法候选

ESP-IDF 5.5.4、esp_tinyusb 2.2.1、esp32-camera 2.1.7 进入编译候选。两个组件清单分别要求 IDF >=5.0、>=5.1，在版本声明层面可配 5.5.4；TinyUSB/esp_jpeg 的传递依赖仍浮动，必须实际解析锁定后编译，不声称已兼容。esp-usb 仓库总许可识别 NOASSERTION 不等于组件无许可，已单独核对 device/esp_tinyusb 的 Apache-2.0。

ToF 没有按猜测找到 STMicroelectronics/vl53l5cx（404）；找到的 STM32duino 1.2.3 含 API 1.1.2，但使用 Arduino.h、TwoWire 和 C++ 类成员，不是现成 ESP-IDF 驱动。后续可保留适用的算法/寄存器逻辑，改平台/类耦合并逐文件核对固件数组声明；不把 Arduino 框架带回主工程。LSM6DSOX 使用 ST 独立寄存器驱动候选，增加 ESP-IDF 读写/延时适配。

LocateAnything 只做初次和失跟重定位，返回源帧后交跟踪/融合；PP-LiteSeg、PaddleOCR、MediaPipe 和 Android CDC 库仅固定源码审核快照，权重/任务文件与实际移动运行时留待各阶段。未复现、未性能比较，不承诺复用比例。
