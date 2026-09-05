# server/perception/navigation

Phase 3 模型无关核心已实现：`WalkableMask`、统一时序 `TimedTof`、逐区外参投影 `FusionProfile` 和有限期 `NavigationEvent`。`evaluate_navigation` 只输出短期候选方向、停止或未知；无标定/时序错位/过期/低有效性时不输出前进候选。

没有分割模型或权重，测试掩码均为 synthetic。真实适配器必须实现 `SegmentationAdapter` 并保留 model_id/quality/frame/session/calibration，不能绕开融合门槛。禁止盲道/斑马线专项、SLAM 与通行许可，不直接驱动输出。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
