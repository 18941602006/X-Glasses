# Phase 1 来源与复用审核

审核日期：2026-09-05。成果是可追溯的审核快照与进入实施前的检查项，不是可直接安装的完整依赖锁，也不意味着实机或全部许可证已通过。

后续真实安装单独追加：[Phase 2A 输入运行依赖](INPUT_RUNTIME.md)；pyserial 3.5 已以官方 wheel 哈希安装并通过内存回环。下文“本轮未安装”指 Phase 1 历史审核，不抹去当时事实。

- [机器可读快照](sources.audit.json)：17 条来源，记录精确 Git/HF revision 或 PyPI 版本、许可证据、复用状态和未通过项。
- [底座复用评审](REUSE_REVIEW.md)：具体文件的可复用内容和必须改造处。
- [环境与许可关卡](ENVIRONMENT_GATES.md)：隔离环境、许可差异和放行边界。
- [硬件接口评审](../hardware/INTERFACE_REVIEW.md)：设计级模块/接线与上电前检查。
- [手机迁移风险](../android-migration/PHASE1_RISKS.md)：尚未实测的迁移路线。
- [研究摘要](../../exa-results/phase1-audit-2026-09-05/README.md)：三组检索与主要发现。

状态含义：adapt_candidate 可进入抽取/适配设计；manifest_candidate 只核对版本/清单；reference_only 留待对应阶段；blocked_use 未获放行不得使用；evaluation_only 仅允许用户已明确的非商业测试，不能扩大为产品/商业运行。所有本轮条目 runtime_verified=false、imported=false。本轮未下载模型、未安装新包、未导入第三方业务源码。

必须区分根许可证与第三方依赖/权重/数据许可；未做完整 CVE 扫描，不能据此称依赖无漏洞。后续实际安装须生成带传递依赖/来源/哈希的环境锁，固件须生成并审查 dependencies.lock，不以本快照代替。
