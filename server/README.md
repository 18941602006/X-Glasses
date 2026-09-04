# server

主机分层：input → common 数据合同 → perception → arbitration → output。Phase 0 只有目录说明；不启动 FastAPI 服务。后续审核开源通用模块后复用，LocateAnything 独立 worker。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
