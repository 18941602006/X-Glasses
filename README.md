# X-Glasses

USB 有线导盲眼镜研究原型：ESP32-S3 采集，电脑验证后迁移骁龙 8 系列 Android。

Phase 0 已交付，Phase 1 来源与风险审核已有成果；尚无可运行的固件、服务或 App。模型使用、实际安装/编译和实机验证仍有未通过项，不能把审核快照当产品验收。

## 施工入口与基础检查

先读 [AGENTS](AGENTS.md) 和[接续入口](docs/construction/CODEX_START_HERE.md)。firmware、server、frontend 只有职责说明；tools/check_foundation.py 和 tests 是可运行的基础检查，不是产品功能。Android 当前仅迁移文档。

Windows PowerShell 使用已有 Python 3.11+ 创建环境（本轮验证 3.12.14）。如果 PATH 无 python，用本机已有解释器绝对路径替换第一条命令的 python，不全局安装依赖。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe tools/check_foundation.py
.\.venv\Scripts\python.exe tools/check_source_audit.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

唯一开发依赖锁定为 Ruff 0.12.12，测试使用标准库；未安装模型、固件或前端依赖。基础检查限制 Phase 0 的纯说明目录，后续阶段须随实际合同升级检查，不绕过失败。逐条命令成功后才进行下一条。

## 现行范围

- [Phase 1 审核入口](docs/dependencies/README.md)：17 条来源快照、逐文件复用、许可及环境关卡。
- [硬件接口评审](docs/hardware/INTERFACE_REVIEW.md)：设计级模块/电平/引脚及上电前检查，未采购或实测。

- 现行技术基线：[方案 V3](方案V3.md)。
- 现行执行规则：[施工规范 V3](X-Glasses施工规范V3.md)。
- 真实进度：[DEV_PROGRESS](docs/construction/DEV_PROGRESS.md)。

不做 SLAM、盲道或斑马线专项识别；保留道路分割、ToF 避障、LocateAnything 找物拿取、信号灯状态、地图导航、OCR 和对话。原型不提供安全过街保证，只允许受控、有陪同且保留盲杖的测试。
