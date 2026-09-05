# LocateAnything 与拿取辅助合同 v1

LocateAnything 仅在隔离环境中按用户确认的 evaluation_only 用途运行。请求最大 256KiB JPEG、160 字符可打印查询，绑定十进制 session_id 和 frame_id；响应必须精确回显 session/frame/固定 model_id，最多 16 个唯一 object_id，每个仅含归一化 box 和有限 score。worker 不得提供或覆写可信采样时间/标定。当前没有 transport 实进程或权重。

拿取融合要求目标、手、ToF 同 session，目标/手同 frame，三者 calibration_id 与 FusionProfile 一致，并满足 TTL/同步/质量。二维方向按目标中心相对手框中心输出；深度仅在目标中心和手中心分别唯一关联到不同且有效的 ToF zone 时计算。相同 zone、无效距离或多重投影时 depth=unknown；遮挡直接 unknown。

手框与目标框达到显式 IoU 门槛或手中心进入目标框时，只输出 verdict=confirm 和 `requires_user_confirmation=true`，不输出深度，也不判成功。ConfirmationGate 只接受事件有效期内的物理 button 或明确 voice 确认，且单次消费；握拳、二维重叠或超时确认无效。没有机械臂或自动抓取动作。

所有阈值必须由版本化 GraspConfig 显式提供；合成测试值不允许直接用于实机。真实阶段需 MediaPipe/其他手部任务文件许可、帧同步、外参和手遮挡/多物评测。
