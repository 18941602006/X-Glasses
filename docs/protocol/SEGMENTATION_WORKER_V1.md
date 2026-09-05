# 分割隔离 worker v1

主服务不直接导入 Paddle/ONNX/远程代码。`IsolatedSegmentationAdapter` 通过受控 transport 发送单帧请求，由独立进程返回二值候选区域；transport 的具体进程生命周期在接入实际运行时时实现，必须有强制超时/终止、单请求或有界队列和 stderr 限制。

请求 schema `xg.segment.request.v1`：uint64 session_id 十进制字符串、uint32 frame_id、最大 256KiB 且带 SOI/EOI 的 JPEG base64。响应必须恰好包含 schema/session/frame/model_id/width/height/quality/rle；身份须精确回显且 model_id 必须为启动时预期固定版本。RLE 为 `[0|1,count]` 数组，总像素必须严格匹配，最大 1920×1080，不接受额外字段、非有限质量或超时结果。

worker 不得覆写 capture/uncertainty/received/calibration/source，这些可信元数据只由主服务附回 `WalkableMask`。response 的 mask 仍需通过 Phase 3 融合门槛。当前只实现/测试 adapter 与假 transport，没有 Paddle 进程、权重或真实图像推理。
