# server

主机分层：input → common 数据合同 → perception → arbitration → output。Phase 2A 已有协议/输入/回放标准库核心；Phase 2B 增加标准库 localhost API 状态/命令边界，不使用 FastAPI，也尚未连接真实 HostLink dispatcher。依据 Phase 1 审核，没有复用旧桥的丢失时间/重复帧行为或固定 FPS 伪同步录制。LocateAnything 独立 worker 待相应阶段。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
