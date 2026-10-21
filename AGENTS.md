# X-Glasses 施工入口

项目管理员 Trollhunter；用户已明确确认 Git 提交姓名 Trollhunter，邮箱 d.o.n.0907@qq.com。只使用 git@github.com:18941602006/X-Glasses.git；不改全局 Git 配置。

优先级：用户最新明确要求 → 方案V3.md → X-Glasses施工规范V3.md → 施工主要求 → 产品要求 → 其他文档。V2 仅历史。

开工依次完整阅读：本文 → 根施工规范 V3 / docs/construction/CODEX_MASTER_REQUIREMENTS.md → docs/product/PRODUCT_REQUIREMENTS.md → DEV_PROGRESS → LOG → GITHUB_ROLLBACK → TEST_METRICS → WORKFLOW → 当前 progress/layers 文件 → HANDOFF（未带路径者均在 docs/construction 下）。按需读 ARCHITECTURE、LAYER_CONTRACT、TOOL_POLICY 和方案 V3。

当前优先 Phase 4/5 电脑样机：LocateAnything 固定权重与 DeepSeek 官方文字/公开图调用已跑通，继续真实质量评测及电脑工作台；高德/手机本地迁移按用户要求暂缓。Phase 0–6 有源码检查点，不等于模型质量、固件/硬件或 Android 实机验收。必读 LOCATE_PC_RUNTIME、PC_JOBS_V1 及最新 HANDOFF；USB/传感器仍按 USB_V1、CONTROL_V1 和 INPUT_RUNTIME。用户要求连续推进，不在小检查点后停等；仍按权限/备份/测试报备。

每轮先记计划，再在安全基线上成功 push 开发前备份并核验，才进入真实施工；明确暂存范围，交付 A/审计 B，不 force push、不覆盖未知改动。测试失败保留原因/修复/复测。记录实际状态、文档漂移和回滚点。

USB 有线；不做 SLAM、盲道/斑马线专项。手部辅助必须校准、对时、验证 ToF 距离归属并由用户确认拿取。未知不是安全；原型不作安全过街承诺。模型权重许可未确认不得下载，手机本地未验证不得宣称完成。

每次回复以“报告长官！！”开头，每完成一部分报备；每轮更新 MEMORY.md、LOG、进度及 HANDOFF。未经用户授权不使用子代理。
