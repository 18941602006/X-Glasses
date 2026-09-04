# 从这里接续

先读根 AGENTS.md 指定的完整顺序，最后以 HANDOFF 最新条目判断当前真实状态。不要把旧日志中的阻塞当作仍存在，也不要把方案指标当已测结果。

1. 核对路径、Git 身份、SSH 账号、origin、分支/HEAD/status 与未完成修改。
2. 在 DEV_PROGRESS 和当前层追加计划，复用现有实现，不创建重复工程。
3. 新轮真实施工前建立唯一远端备份并核验；备份只覆盖已提交文件。
4. 按 CONSTRUCTION_PLAN 当前阶段实施，执行 TEST_METRICS 的检查，记录失败复测。
5. 同步 LOG、HANDOFF、层进度、MEMORY；审查后交付 A/审计 B 并核验。

当前有协议/回放、主机控制和串口适配；入口见根 README、docs/protocol/{USB_V1,CONTROL_V1}.md、docs/dependencies/INPUT_RUNTIME.md。下一子任务 ESP-IDF 固件/互通与编译；尚无固件/HTTP 服务/App。用户要求连续全项目施工，不在小检查点停等，硬件缺失单独标未测。LocateAnything 非商业测试用途已确认，其他代码/环境关卡未自动解除。
