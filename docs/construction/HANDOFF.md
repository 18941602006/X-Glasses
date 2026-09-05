# X-Glasses 交接记录（追加）

## 2026-09-05 / 最新：Phase 3 软件合同待检查点

融合核心 A = 1e6fdb44017f233cb58d685df4855f16435b3d9d；其后新增分割 worker adapter、SEGMENTATION_WORKER_V1、模型关卡和 6 项测试。PP-LiteSeg 权重未下载，模型 not_installed。完成 107 项全量后提交开发分支；随后可进入 Phase 4 找物/拿取纯核心，不把缺权重误写为 Phase 3 实机完成。

## 2026-09-05 / 最新：Phase 3 融合核心待交付

开发分支新增 server/perception/navigation/contracts.py、fusion.py、NAVIGATION_CORE_V1 和 9 项 synthetic 测试。核心严格拒绝标定/时间/质量/有效性错误，局部中央 ToF 未知不前进。没有真实模型/权重或硬件，下一步保存 A/B 后实现受审核分割模型适配器。

## 2026-09-05 / Phase 2B 已交付开发分支

A = daa4e91020bb0313829f0529f7d50af07bf92de1 已推送 development/continuous-build-20260905 并核验，main 保持 776a04a6f405b76c6a9d129a3523c3e4264ae640。下一步补审计 B 后在同一开发分支实施 Phase 3 纯核心与适配合同。

## 2026-09-05 / 分支阻塞与安全替代

平台拒绝把 Phase 2B 的 32 文件批量变更直接 push main，命令未执行。成果改存 `development/continuous-build-20260905` 并在该分支继续，不绕过 main 审查。需要用户之后明确批准合入 main；这不影响本地测试或后续独立开发。

## 2026-09-05 / 最新：Phase 2B 本地实现待交付

新增 `server/api` 与 `frontend`：localhost API 默认离线且无 dispatcher；React 调试台展示真实来源/时效/未知和命令 ACK，不直控硬件。依赖精确锁定，前端构建与 3 项交互测试通过；Python 全量 92 项通过。用户省略视觉截图，因此不要写视觉/屏幕阅读器已验收。下一步完成 A/B 后进入 Phase 3 道路分割与 ToF 避障核心，真实设备仍是独立硬件关卡。

## 2026-09-05 / 最新：固件协议基线已交付

A = 47174622f6a42cc818365796bf5851a7156bc9cd 已推送并核验远端一致，A 后工作区干净。静态软件基线通过，ESP-IDF 编译和硬件仍交团队验证。本追加为审计 B；下一任务是从最终 B 建 Phase 2B 备份并实现新的电脑调试/交互前端及本地服务接口。

## 2026-09-05 / 最新：固件协议基线待交付

当前工作区包含 ESP-IDF 固件协议/控制器、精确组件清单、主机 capability 强制检查、固件合同测试及 VS Code 团队说明。最终本地软件验收为 86 项单测、固件合同、76 文件基础范围、17 来源/6 报告、Ruff、pip 和 diff 全通过。默认固件能力只有 CLOCK，其余外设全部未启用。

用户明确允许跳过当前施工机的 ESP-IDF 安装与编译，由已有环境的团队成员完成 build/flash/真机联调。本轮没有编译成功或烧写结论；export.ps1 的一次失败已记录。收口 A/B 后直接进入 Phase 2B 前端和主机接口，实机条目保持未验收。

## 2026-09-04 / 规范 V3 对齐后

### 当前状态

用户已要求开始施工，但紧接着要求优先修正规范。已完成文档修订，Phase 0 仅做过前置检查，尚未初始化仓库；不能进入 Phase 1。

### 本轮完成

现行施工规范为根 X-Glasses施工规范V3.md；技术基线为方案V3.md。已统一 USB、无盲道/斑马线、手部融合、新前端、ESP-IDF、MCU 告警边界和 Phase 0–6。

### 未完成

提交身份确认、Python 解释器定位、远端历史检查、Bootstrap/远端备份、完整 AGENTS/施工文档体系、venv/依赖/lint/测试和所有业务代码。

### 下次优先任务

1. 重读现行规范、方案及本交接；根据用户当前指令恢复 Phase 0。
2. 核实当前 shell 的 Git user.name/user.email（此前无值）、已有 Python；缺失身份按规范询问，不凭管理员名填入。
3. 通过指定 SSH 检查目标远端历史，再按安全初始化/备份流程继续；未知或冲突停止。

### 必读文档与关键文件

- ../../X-Glasses施工规范V3.md：现行工程规则。
- ../../方案V3.md：产品及技术基线。
- DEV_PROGRESS.md、LOG.md、本文：实际执行状态。
- ../../MEMORY.md：需求和对话历史。
- 旧外部提示词仅作历史，不能恢复其 V2 模块；根 AGENTS.md 尚未建立。

### 测试基线

无代码、无依赖安装或单元测试；仅环境/SSH 及本轮文档检查。10 项文本一致性检查通过（PowerShell 退出码 0），6 个本轮文件可读。详细检查见 LOG.md。不得写成 Phase 0 通过。

### GitHub 状态

- 指定仓库：18941602006/X-Glasses。
- 指定 Remote：git@github.com:18941602006/X-Glasses.git，尚未配置。
- SSH：此前沙箱外验证为 18941602006；没有验证仓库历史/写权限。
- 当前分支/基线/备份/最新提交：无，当前不是 Git 仓库。
- 已 push：否。
- 工作区：本项目准备文档及本轮规范/记录文件；尚不可称 Git 工作树干净。

### 风险提醒

python/py/python3 在此前 PATH 中未找到；Git 配置查询无身份。不能跳过备份写业务代码。手机 LocateAnything、权重用途许可与硬件功耗仍需后续核实。

## 2026-09-04 23:58 +08:00 / Phase 0 恢复后（最新状态）

- 用户已明确要求开始并分段报备；环境/远端只读核查完成，因提交身份缺失停在安全门槛。Phase 0 仍未完成，不能进入 Phase 1。
- 已解决：Python 已定位到 C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe，--version 为 3.12.14；指定 SSH 远端 ls-remote 读取成功、未返回 refs。先前“Python 未定位/远端未读”是历史状态。
- 当前等待：用户指定 Git user.name，并确认使用 d.o.n.0907@qq.com；只在同意后配置本仓库，不改全局配置。
- 修改文件：DEV_PROGRESS、LOG、本文、MEMORY 及新增 progress/layers/00-foundation.md。仅前置计划/阻塞记录，无业务施工。
- 测试基线：解释器版本/远端读取检查成功；提交身份查询仍无值。无 venv、依赖安装、lint、单元测试，不把文档检查当 Phase 0 通过。
- GitHub：目标 18941602006/X-Glasses，指定 SSH origin 尚未配置；本地未初始化，无分支/基线/备份/A/B/最终提交，无 push。读取成功不代表写权限已验证，所有资料未被远端备份覆盖。
- 下一步：重读规范和最新记录 → 获得明确提交身份 → 复核远端仍为空及本地文件 → 最小 Bootstrap/公开推送内容审核 → 文档基线与备份 push/核验 → 完整 Phase 0 文档骨架和最小检查。每完成一部分向用户报备。
- 风险：身份硬门槛不可猜测绕过；Python 可执行不代表 venv/依赖已验证；模型许可、手机部署与硬件实测仍留待对应阶段。

## 2026-09-05 / Foundation 本地验收后（A/B 收尾前）

- 当前：Phase 0 文档、骨架说明、环境和基础检查本地通过，待 A/B 远端核验；不是业务功能完成。
- 身份已解决：Trollhunter / d.o.n.0907@qq.com，仅仓库级；SSH 账号 18941602006，origin git@github.com:18941602006/X-Glasses.git，main。
- 备份：backup/pre-phase0-foundation-20260905-0006 → 76bb6d685a02a833056515350cd0a4eccee5d4fc，远端核验；Bootstrap fb23e6fbd1b822db85160e5f641af9b0bff9b02d。备份覆盖准备资料，不包括其后 Foundation 修改。
- 文件：根 AGENTS/README/空配置/忽略换行/最小依赖、完整规范文档体系、所有层 README 和进度、检查工具/测试。最新入口 AGENTS → CODEX_START_HERE；规范 V3、产品要求、LOG、WORKFLOW、GITHUB_ROLLBACK、TEST_METRICS、00-foundation 均必读。
- 验证：.venv Python 3.12.14 + Ruff 0.12.12；pip check、lint/format、45 必需文件/配置/忽略探针、13 工具单测、diff --check 通过。首次格式失败已修复并复测；无业务/实机测试。
- 执行环境：沙箱 helper 启动故障时走受控沙箱外执行；补丁仍经 apply_patch 原生入口。不要把环境故障误报为项目代码测试失败。
- 当前工作区：Foundation 变更尚待提交；A/B 无可填哈希。收尾后以下方追加审计为准。
- 下一步：完成 A/B 交付核验后，本阶段结束；Phase 1 首先审核固定开源底座与许可/依赖/硬件 USB 兼容、LocateAnything 手机风险。每次新轮真实施工先建新备份。
- 未完成和风险：全部固件/模型/前端/手机功能未开始；LocateAnything 权重用途须使用前确认，不能预设本地 Android 已可行，不下载权重、不偷偷换识别模型。没有需执行的回滚。

## 2026-09-05 / 最新：Phase 0 已交付，审计 B 收尾

Phase 0 工程基础完成；下一阶段 Phase 1 尚未开始。Git 身份 Trollhunter / d.o.n.0907@qq.com，origin 与 main 正确。A = 66dc754444148a818beb5a06af74f6ec2f0902b4，已 push、ls-remote 完整哈希一致，A 推送后工作区干净。

本条属于审计 B，尚不在文档中预写 B 自身哈希/推送成功；最终由终端核验并回复用户，下一轮开工记录 B。备份 backup/pre-phase0-foundation-20260905-0006 仍指向 76bb6d685a02a833056515350cd0a4eccee5d4fc。

交付包括规范要求的文档/层说明、隔离环境和最小锁定依赖、45 文件基础检查及 13 项工具单测；lint/format/pip/diff 检查通过，未做业务/硬件测试。记录保留所有故障与复测，详见 LOG。

下一轮先按 AGENTS 必读顺序核查最终 HEAD/remote/status 并补记 B，再写 Phase 1 计划、创建新的远端备份。优先审核固定开源底座和代码/权重许可、USB/硬件模块/供电、手机风险；使用 LocateAnything 权重前确认用途，不把普通个人项目自动等同适用许可。持续按用户要求每完成一部分报备，无需重复确认已解决的 Git 身份。

## 2026-09-05 / 最新：Phase 1 本地审核成果，待 A/B 收尾

用户要求继续，已完成来源/许可/复用/硬件/手机预审并补记 Phase 0 B = 34fcde23e9bfa9161ff2c4175bd7c2104ac7cfb3。开工备份 backup/pre-phase1-audit-20260905-0026 已核验同一哈希，main/SSH origin/身份不变。当前本轮审核文件尚待提交，A/B 未生成，以下方审计为准。

入口：docs/dependencies/README.md → sources.audit.json / REUSE_REVIEW / ENVIRONMENT_GATES，另读 docs/hardware/INTERFACE_REVIEW.md、docs/android-migration/PHASE1_RISKS.md 和本轮 LOG/01 层记录。17 条精确来源/版本是审核快照，不是安装锁/完整 SBOM。Search 检索仅用于发现，最终固定原始来源核验。

检查：45 基础文件、17 来源/6 报告、23 工具单测、lint/format/pip/diff 全通过；首轮格式失败已修复。没有新运行依赖、第三方业务源码、模型权重、固件编译或实机测试。

重要修正：LocateAnything 固定 LICENSE 是研究/评测描述，模型卡更窄，旧根许可路径已失效；按证据保留 blocked_use，先确认用户用途，不重复错误断言只限学术/非营利，也不擅自宣称商用许可。ToF 候选库不是现成 ESP-IDF 驱动；硬件 I²C 电平和整机峰值功耗须核查。

下一步：收尾并核验 A/B 后可单独规划 Phase 2A 的不依赖模型 USB 协议/输入/回放测试，先写计划并建新备份。模型使用前确认项目实际用途与许可差异；固件安装/解析传递锁/编译和硬件到货上电仍待执行。不能把“审核交付”写成所有 Phase 1 运行/许可关卡通过。

### 最新补充：用户已明确非商业测试用途

LocateAnything 当前 evaluation_only（不再 blocked_use），用户非学术/非盈利用于测试，按固定 LICENSE 的评测范围准备。不要重复询问已回答的用途，不默认商用/生产分发；模型卡差异仍留记录。远程代码/第三方条款/隔离环境/手机迁移尚待验证，未下载权重。审核工具和文档已同步，全部测试 25 项通过。下一步仍按 Phase 2A 顺序，不因解除用途等待跳过其他安全门槛。

## 2026-09-05 / 最新交付审计

Phase 1 来源/风险审核已交付。A = fb9d88a18ed6efe9acbdca5b397754fe9e43c3c3 已 push 并核验远端 main 一致，推送后工作区干净。本次追加为 B，B 自身哈希及最终状态在终端核验、下一轮补记，不在文档内预写成功。

下一轮从最终 B 先建新的 Phase 2A 备份，再做不依赖模型的 USB 协议/输入/回放；若要解析/安装固件依赖，先固定传递锁并核验目标工具链。当前 firmware/server/frontend 仍只有说明，不能误报链路已实现。25 工具测试及基础/审核检查通过；所有 runtime_verified 仍 false。LocateAnything 已获明确非商业测试用途，不重复询问；自定义代码/第三方条款/运行环境和设备实测仍待完成。

## 2026-09-05 / 最新：Phase 2A 第一部分与持续施工授权

Phase 0/1 已交付；2A 主机协议/输入/回放核心已实现，待本次最终检查与 A/B。当前输入不连接真实串口，其他业务/固件/UI/Android 未实现。基线 08aaecc722750e59a5009a19bed8d39a099bf08c，backup/pre-phase2a-protocol-20260905-0110 已核验同值；身份/指定 SSH origin/main 不变。工作区为本轮代码与说明变更，未预写干净状态或 A/B。

必读 docs/protocol/USB_V1.md、server/common/protocol.py、server/input/{frames,stream,recording}.py、LOG 和 02 层进度。工具入口 python -m tools.replay_usb --demo；合计 57 单测（26 工具+31 模拟协议回放），最终全量结果以下方审计为准；此前全量 54 和最新 31 子集通过。未新增运行依赖、未下载模型或读取真实采集资料。

下一任务：本子项 A/B 保存后继续完善会话/握手、传感器有效性、对时估计与命令关联/超时合同；再接实际 CDC/ESP-IDF 驱动、基础告警、编译与可进行的实机验证。当前时间字段未对齐、帧仅本地 TTL、JPEG 仅标记检测，不可提前用于安全判断。2B/模型/手机仍依序实施。

用户明确要求连续工作至完整项目、一般问题自行选择。不要在小阶段收尾后发最终答复等待再次“继续”；继续分段报备和可验证的工程任务。权限依平台规则，硬件/手机缺失只标相关实测未验收，不虚报，也不阻塞完全独立的软件任务；不采购/付费/隐私上传，不默认换模型/云端。LocateAnything 非商业测试用途已确认不重复问。


## 2026-09-05 / Phase 2A 协议核心 / 交付 A 核验

A = 31577ff742ca0cd66cd8f0828b9af9ef0ac71009，27 文件 1187 增/17 删（状态摘要调整，历史保留），已 push 指定 origin main，ls-remote 完整哈希一致，A 后工作区干净。最终 Ruff check/format（11 文件）、53 必需文件、17 来源台账、57 单测（约 1.257 秒）、纯内存 demo、pip check、diff/cached diff 均通过。明确暂存清单、小于 1MiB 和常见凭据模式检查通过；这不是通用秘密审计或实机认证。

此追加为审计 B，B 不记录自身哈希，终端核验后继续下一子任务；不在此停止等待用户。下一步仍 Phase 2A 会话/传感器语义/对时/ACK，完整实机链路未验收。备份 backup/pre-phase2a-protocol-20260905-0110 仍指向 08aaecc722750e59a5009a19bed8d39a099bf08c。


## 2026-09-05 / Phase 2A 第二部分 / 连续施工记录

基线 B = a7bb773726bb6ab5a9a22bfbba9c726ee7ae933a 已核验；先写计划并 push backup/pre-phase2a-control-20260905-0200，远端哈希同值，再实施。两份开工计划未包含在该备份中。main/身份/指定 origin 不变，用户持续施工授权有效，不等重复确认。

新增 common/{sensors,clock,control}.py、input/{link,serial_port}.py，CONTROL_V1 合同、可选 requirements-input.txt、usb_probe CLI 和测试。归一化未知 ToF= None，IMU 非有限值拒绝；握手/心跳清理、四时间戳/误差/5s 过期/跳变清估计、命令 request/session/ACK/500ms 截止，所有队列有界。原 InputSession 回放保持未对时，HostLink 只输出新鲜估计帧并携带误差，不等于标定或安全认证。

pyserial 3.5 官方 wheel SHA256 固定并安装到项目 venv，内存 loop:// 回环测试通过；只读枚举端口结果 []，未打开实际设备。官方 v3.5 BSD-3-Clause 与 wheel 源码 SPDX 已核对，wheel 无独立许可证文件；运行台账 docs/dependencies/INPUT_RUNTIME.md，Phase 1 快照保留历史。Node 22.17.1/npm10.9.2、RTX4090 Laptop 16376MiB/驱动595.79 已读；PATH/常见目录未发现 JDK/IDF/Android SDK，不断言全盘不存在。

验证：控制首轮 18 项与串口 2 项通过；全量 77 项、64 必需文件/9 运行白名单、17 来源、Ruff check/format（19 文件）、pip check 通过；追加时钟跳变回归后控制 19 项通过，最终全量现为 78 项，收尾复测另记。格式化前自动修正新测试 1 处导入排序；时钟保护补丁一次上下文不匹配、未落盘，读实际行后成功重试。许可证先猜 LICENSE.txt/rst 不存在，rg 实际枚举后改查 metadata/SPDX 与官方原文，无依赖代码修改。代码审查另修复 idle 重同步丢包、结果缺会话标签和缺对时误差字段。

当前本部分 A/B 尚待提交，不预写 push/干净状态；无需回滚、无文件删除、无长期采集进程。阶段未放行实机：固件、晶振预算、传感器归一化、实际 USB/供电/30 分钟链路都未验证。下一步保存此检查点后继续 ESP-IDF 固件与跨语言协议/编译，不因无硬件停止独立软件工作。


### 第二部分交付 A 审计

A = 2c45a4839d3fd266d6bb899995601db8d0f15290，30 文件 1013 增/10 删，已 push 指定 main 且 ls-remote 完整哈希一致，A 后工作区干净。最终 78 测试（约1.532秒）、64 文件、17 来源、Ruff19文件、pip/diff/cached diff 通过，显式文件体积及常见凭据模式检查无命中。第二部分软件检查点通过，实机仍未验收。本追加为 B，自身哈希终端核验后继续固件，不停等用户。

## 2026-09-05 / 最新：Phase 4 软件核心待交付

当前开发分支基于 66eeb8ab8d95f1b8157260730067eed3b0b4a566，备份 backup/pre-phase4-locate-grasp-core-20260905 已核验。Locate worker 合同、共享矩形、手物 ToF 引导及显式确认门已实现；116 项全量测试通过、1 项可选 pyserial 跳过，110 文件基础检查、compileall 及仓库 `.venv` Ruff check/format 通过。

恢复时先核验本阶段开发分支提交/远端状态；然后进入 Phase 5 的红绿灯、导航、OCR、对话和输出仲裁软件合同。LocateAnything 与手部模型均未安装，外参和实物拿取未测；不要把合同实现写成模型或硬件完成。用户认为此前浏览器截图步骤价值不大，已省略，不要重新阻塞施工。

## 2026-09-05 / 最新：Phase 5 软件核心待交付

基线 9455b7c783fefcb1f265cde659456107384689b4，backup/pre-phase5-assist-arbitration-20260905 已核验同值。辅助事件、worker、统一候选映射、输出仲裁和执行边界已实现；23 项阶段测试与 139 项全仓测试通过，117 文件/来源/compileall/Ruff/diff 检查通过。

当前不具备真实信号灯/OCR/对话模型、地图 provider、TTS/震动 transport 或 Android 构建环境。交付检查点后进入 Phase 6 静态 Android 工程与 USB/任务状态合同；没有 SDK/JDK 时只做可验证的纯 Kotlin/文档边界，不虚报 APK。真实 provider 的地区、条款和密钥仍需后续用户/部署决策，不能擅自选云服务或上传数据。
