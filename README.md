# X-Glasses

USB 有线导盲眼镜研究原型：ESP32-S3 采集，电脑验证后迁移骁龙 8 系列 Android。

源码在 `development/continuous-build-20260905` 开发分支；GitHub 默认 main 仍是较早固件/协议基线。团队应明确检出开发分支。现有 USB/固件基线、React 调试台、融合/拿取/辅助合同和 Android/高德源码；尚未完成整机验收。

2026-10-21 当前工作重点转为电脑样机：LocateAnything 在电脑本地运行，DeepSeek 官方 `deepseek-flash` 提供对话；手机迁移和高德联网联调暂缓。见[电脑运行步骤](docs/dependencies/LOCATE_PC_RUNTIME.md)。真实定位结果、依赖与未验收项以[交接记录](docs/construction/HANDOFF.md)为准。

| 源码 | 入口 |
| --- | --- |
| 电脑 LocateAnything | `server/perception/locate/pc_runtime.py`、`python -m tools.locate_pc` |
| DeepSeek 文字/按需图片 | `server/perception/assist/deepseek.py`、`python -m tools.dialogue_pc` |
| 电脑工作台/API | `frontend/src/App.tsx`、`server/api/` |
| Android 与高德 | `android/app/src/main/java/com/trollhunter/xglasses/` |

Key、模型权重、环境和测试照片不随 Git 分发。克隆源码后需在本机按说明准备；没有 ToF 时距离明确为未知。

电脑页面现可选图调用本地LocateAnything、显示静态框，并显式同意后发送DeepSeek文字：根目录运行`.\.venv\Scripts\python.exe -m server.api --pc-runtime`，另一终端在frontend运行`npm run dev`，打开http://127.0.0.1:5173。需要已准备好的.venv-pc/模型/本机Key；默认API不启用真实任务。支持取消/失败/后台任务查询，不自动打开相机、不把静态框当实时引导。限制及操作见[PC任务合同](docs/protocol/PC_JOBS_V1.md)。

## 施工入口与基础检查

先读 [AGENTS](AGENTS.md) 和[接续入口](docs/construction/CODEX_START_HERE.md)。基础检查环境与模型环境分开，以下命令只安装开发检查依赖；电脑模型安装使用上述独立运行说明。

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

开发依赖 Ruff 0.12.12，核心协议使用标准库；可选 pyserial 3.5 已以 SHA256 wheel 验证。基础检查显式列出当前各层允许的运行文件；基础环境不安装模型。逐条命令成功后才进行下一条。

## USB 模拟回放

```powershell
.\.venv\Scripts\python.exe -m tools.replay_usb --demo
```

纯内存演示，不打开摄像头/串口、不写录制文件、不输出到硬件；只恢复一个 6 字节模拟标记帧，非可显示的真实 JPEG。输出带 synthetic、replay、unsynchronized 与 hardware_verified=false。协议见 [USB v1](docs/protocol/USB_V1.md)，新增主机控制见 [CONTROL v1](docs/protocol/CONTROL_V1.md)。串口安装/显式端口探针见 [输入运行台账](docs/dependencies/INPUT_RUNTIME.md)；本机枚举 []，仅软件 loopback 已测。固件、MCU 告警、真实对时误差/USB/电流未验收，Phase 2A 仍在施工。

## 现行范围

- [Phase 1 审核入口](docs/dependencies/README.md)：17 条来源快照、逐文件复用、许可及环境关卡。
- [硬件接口评审](docs/hardware/INTERFACE_REVIEW.md)：设计级模块/电平/引脚及上电前检查，未采购或实测。

- 现行技术基线：[方案 V3](方案V3.md)。
- 现行执行规则：[施工规范 V3](X-Glasses施工规范V3.md)。
- 真实进度：[DEV_PROGRESS](docs/construction/DEV_PROGRESS.md)。

不做 SLAM、盲道或斑马线专项识别；保留道路分割、ToF 避障、LocateAnything 找物拿取、信号灯状态、地图导航、OCR 和对话。原型不提供安全过街保证，只允许受控、有陪同且保留盲杖的测试。
