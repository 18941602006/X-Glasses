# Phase 1 检索与审核摘要

使用 Search/Exa 按开源底座、LocateAnything 部署、USB/硬件三组定向检索，共请求 15 条候选结果；按仓库/模块归并，剔除非原作者聚合页，最终以官方固定提交、HF revision、包元数据和厂商资料核验。请求数不是独立已核实来源数。查询不按“最近”筛选，审核日期为 2026-09-05。

Exa 部分抓取返回截断内容，涉及许可/清单/源码时用官方 raw/API 或浏览器定点补读；未以搜索索引旧许可证替代固定 revision 原文。已发现旧许可路径失效及两处描述不一致。

关键成果：

- [旧底座固定提交](https://github.com/AI-FanGe/OpenAIglasses_for_Navigation/tree/46d90ab778e7503559a4d165e6659f7426207d95) 的帧桥/录制模式可适配，主程序与拿取/过街流程不能直接搬入；已给逐文件改造边界。
- [LocateAnything 许可文件](https://huggingface.co/nvidia/LocateAnything-3B/blob/c32291ca5e996f5a7a485845b4f57a233936bba0/LICENSE) 与模型卡的用途描述有差异，用户随后明确非商业测试，按固定 LICENSE 的评测范围改为 evaluation_only，保留说明差异。尚未下载权重。独立 Python 环境和 Android 专项验证不可省略。
- USB 固件候选版本已核对清单声明，尚未解析全部传递锁或编译。ToF 候选库仍需移植 Arduino 平台层；具体模块按 3.3V I²C 核验，供电实测未完成。

完整结果见 [审核入口](../../docs/dependencies/README.md)。当前来源质量为原作者源码/清单及厂商文档；性能说明属于作者/厂商数据，不是本机实测。无新业务实现、无采购、无权重或采集数据下载。
