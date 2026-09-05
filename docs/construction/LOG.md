# X-Glasses 施工日志（追加记录）

## 2026-09-05 / Phase 6 地图导航开工

用户明确要求加入设定目标地点后的指引和前端调整。只读核对开发分支、Android 五任务骨架及 Phase 5 `MapInstructionEvent`：现有代码只有外部地图事件解析/仲裁，没有目的地搜索、路线请求、手机定位、偏航重算或专用界面。GitHub 原始项目调研候选包括 MapLibre Navigation Android（MIT、无内置 UI、可对接自有 Directions）、MapLibre Native（BSD-2-Clause、仅地图渲染）、Valhalla（MIT、支持 pedestrian）、GraphHopper（Apache-2.0）和 Organic Maps（Apache-2.0，但地图数据另有许可且完整应用集成过重）。地点搜索候选 Photon（Apache-2.0）/Pelias（MIT）；公共演示服务不作为生产 SLA。

决定实现 provider 可替换架构，不硬编码供应商、密钥或公共服务 URL。首个代码检查点以无额外第三方依赖的纯 Kotlin 合同和 Android SDK 定位为主，路线/搜索通过受限 HTTPS JSON provider 注入；之后由团队根据目标地区选择自托管 Valhalla/Photon 或合规国内服务适配器。导航提示优先级低于传感失效、紧急停止和局部避障。

### 地图导航第一检查点实现与验证

新增 7 个 navigation Kotlin 主文件和 1 个测试文件，修改 Manifest/BuildConfig/运行时/Activity/reducer/Compose。人工复核中主动修正：未配置 provider 不再索取位置；退后台、USB 非 READY 或全局取消立即停止路线；到达/失败回写统一任务状态；TalkBack live region 只包围稳定指令而非每秒距离；Valhalla 拒绝 status 失败与非 pedestrian 响应，并补 type 2/3 起步左右转和 verbal 指令优先。高对比 Material3 深色配色覆盖目的地输入框。

验证最终为 Android checker 27 文件通过、破坏性 Python 回归增至 9 项、全仓 148 项通过、Ruff 43 文件、compileall、124 文件基础范围和 diff 检查通过。Kotlin 测试源码 19 项（新增路线推进/到达、过期/低精度、偏航、失败安全文案、HTTPS、polyline6、任务完成），因 java/gradle/kotlinc/adb/Android Studio/SDK 均未找到而未运行。本轮没有连接公共 demo、真实 provider、GPS、USB 或硬件。

交付 A = `f0ac3596df5142a2e56142172ef9eaf9e4c6f3e3`，31 文件、1225 增/16 删，已推送 `development/continuous-build-20260905` 并以 `ls-remote` 核验远端一致；A 后只有未知 `.workbuddy/` 未跟踪。本条及 HANDOFF 追加组成审计 B，不预写 B 自身哈希。

## 2026-09-05 / Phase 3 分割 worker 与模型关卡

在核心 A = 1e6fdb44017f233cb58d685df4855f16435b3d9d 后继续。官方固定 PP-LiteSeg 文档给出 Cityscapes checkpoint/export/Paddle Inference/Paddle Lite；Cityscapes 现行条款允许非商业个人实验但有注册/引用/禁止数据再分发与商业用途限制，且车载视角不等于眼镜视角。未下载或接受权重，新增 SEGMENTATION_RUNTIME 记录状态 not_installed。

实现 worker adapter：256KiB JPEG、1920×1080 mask、严格 schema/回显/model_id、二值 RLE、250ms 可配超时与 host-only 时间/标定。6 项测试逻辑先通过，format 要求测试文件重排；复核后又增加 FrameRequest 发送前身份/时间/来源校验，格式化后 6 项复测通过。没有实际进程 transport/Paddle 推理，下一步全量检查并保存软件检查点。

## 2026-09-05 / Phase 3 道路候选与 ToF 融合核心

基线 B = 642d69550152df27550ee444645d06fbe0ae9718，backup/pre-phase3-navigation-core-20260905 已 push 核验同值。新增 WalkableMask/TimedTof/FusionProfile/NavigationConfig/Event 和融合函数，无新依赖/模型/权重。大补丁在 README 旧文本上下文不匹配前已部分落盘 contracts/fusion；只读核实后补齐 README/协议/测试/白名单，没有重复覆盖。

首轮 8 项逻辑测试通过，format 要求两文件重排；格式化并增加未来接收时间门槛后，一项期望因判定先返回 future_receive 而失败，调整为先判源采样未来、再判接收未来，8 项通过。安全复核发现全局 ToF 有效率会掩盖中央局部未知，新增逐走廊有效率和第 9 项回归；中央底部两区未知时不再选择 forward。阈值只由测试显式配置，不作为实机值。

未做：模型推理、真实道路、日光/头动、外参标定、USB/ToF 实机、性能与安全评测。完整全量复测以下一交付记录为准。

## 2026-09-05 / Phase 2B 开发分支交付 A 审计

切换并新建 development/continuous-build-20260905，将已暂存成果连同 main 拒绝记录提交为 A = daa4e91020bb0313829f0529f7d50af07bf92de1，提交信息 feat: add local dashboard and control API；32 文件 3358 增/4 删。push -u 成功且 ls-remote 哈希一致，A 后工作区干净。main 未变更；此记录为 B，后续仍在开发分支。

## 2026-09-05 / Phase 2B 默认分支推送受限

32 文件 Phase 2B 交付前检查全通过后，尝试提交并 push 指定 main；平台自动风险审查以“大批量变更直接推送默认分支、需明确批准”为由在进程创建前拒绝，故没有生成提交或远端变更。遵守审查，不以拆命令等方式绕过；改在独立 `development/continuous-build-20260905` 分支提交并推送，后续连续施工沿该分支进行。最终合入 main 留待用户明确批准。

## 2026-09-05 / Phase 2B localhost API 与新前端

从 B = 776a04a6f405b76c6a9d129a3523c3e4264ae640 建并核验 backup/pre-phase2b-frontend-20260905 同值。官方资料确认 React 当前 19.2、Vite Node 要求与 Testing Library/Vitest 清理方式；npm view 固定实际 patch 版本。新增 server/api、LOCAL_API_V1、6 项 Python 测试；API 只绑定数值回环、校验 Host/JSON/大小/动作、默认无 dispatcher，uint64/纳秒用十进制字符串，账本有界。

新增 React/TS/Vite 前端、3 项交互测试和响应式高对比样式；无外部字体/CDN，命令只显示 pending/ACK 终态。首次 jsdom 30.0.1 engine 不兼容 Node 22.17.1，改锁 29.1.1。一次 apply_patch 在 frontend 工作目录导致重复路径失败；两次 npm --prefix 在本环境没有切换目录，改在 frontend 直接执行。首次 Vitest 因未清理 DOM 造成重复按钮，按官方 setupFiles afterEach cleanup 修复；首次 TypeScript 7 因缺 Vite CSS 声明失败，增加 vite-env.d.ts 后通过。

浏览器视觉尝试临时启动回环 API/Vite，但命令重复追加 host 参数使多余参数被当作 root，页面 GET 404、API GET 200。用户明确该步骤价值不大可省略；停止两个服务并删除未完成截图，不再重试，视觉/屏幕阅读器人工验收列未测。构建/交互测试不受该 404 影响。

npm audit 首次因系统 npmmirror 不实现 audit endpoint 失败；单次指定官方 registry 后生产依赖 0 vulnerabilities。尝试让 package-lock resolved 从镜像切至官方，npm 因复用已有/隐藏锁未改，安全恢复原锁；保留 integrity 和镜像来源并入台账，不手工改哈希。最终 Python 92 项、前端 3 项、typecheck/build、Ruff、96+ 必需文件、来源/固件合同、pip/diff 复测结果以交付前最终轮为准。

## 2026-09-05 / 固件协议基线交付 A 审计

A = 47174622f6a42cc818365796bf5851a7156bc9cd，提交信息 feat: add ESP32-S3 protocol firmware baseline；已 push 指定 main 且远端哈希相同，A 后工作区干净。暂存 24 文件均小于 1MiB；显式常见私钥/token 模式复扫无命中，首次扫描脚本错误沿用外部退出码并误报 2，改用结果变量后成功。LF→CRLF 为工作区换行提示，不是测试失败。此追加为审计 B，完成后继续 2B。

## 2026-09-05 / Phase 2A 固件协议基线

从已核验 B = 5201b13b530350f3e9bf5161cb6cfedd24d7894d 开工，远端备份 backup/pre-phase2a-firmware-20260905-0300 指向同一基线。实现 firmware 下 ESP-IDF 工程、C 协议和控制器，主机增加 capability 拒绝规则；默认固件只声明 CLOCK，相机/ToF/IMU/按键/震动没有伪装为已启用。增加固件静态合同、7 项负面/正面测试、VS Code 和固件说明。

工具链尝试：固定 ESP-IDF 5.5.4 浅克隆和所需工具安装到临时隔离路径；首次 export.ps1 因错误 Python/平台识别失败，随后用户决定由已有环境的团队成员承担编译和烧录，停止把本机 IDF 配置作为前置。没有刷写设备。固件 README 已修正为团队复制至短 ASCII 路径构建，不声称仓库存在自动复制工具。

首次组合验收中 86 项测试与固件合同通过，但 Ruff 报 server/input/link.py 导入顺序，且命令误用了不存在的 tools/check_sources.py；由于组合命令最后退出码为 0，该轮不能算通过。用锁定 Ruff 修复导入顺序，改用实际 tools/check_source_audit.py，并为每个外部命令显式检查退出码。最终 86 项约 1.8 秒通过，固件合同、76 必需文件、17 来源/6 报告、Ruff check/format、pip check、git diff --check 均通过。

未验收：ESP-IDF 交叉编译、CDC 枚举、任何外设、供电、时序和佩戴安全。当前准备检查点 A/B，之后继续 Phase 2B，不等待固件环境。

## 2026-09-04 / Phase 0 前置检查 / 用户中断前记录

### 本轮计划回放

用户要求说明施工顺序并开始施工；计划从 Phase 0 安全检查、身份、远端备份开始，不越阶段。

### 实际修改

无文件修改、无 Git 初始化、无依赖安装。

### 测试日志与验证结果

- Get-Location / Get-ChildItem / rg --files：目录为目标项目，只有方案 V2、方案 V3、MEMORY.md，均来源明确。
- python --version：命令不存在。Get-Command python/py/python3：未找到；尚未定位其他可用解释器，不等于电脑完全没安装 Python。
- git --version：2.52.0.windows.1；可执行文件 D:/Program Files/Git/cmd/git.exe。
- git rev-parse --is-inside-work-tree、branch --show-current、status --short、remote -v：当前不是 Git 仓库，因此没有可报告的分支/HEAD/origin；不是已初始化仓库发生损坏。
- git config --get user.name / user.email，以及 --show-origin 查询：无输出；提交相关环境变量未发现。不得据此编造身份；提交前需确认实际执行环境的身份配置。
- ssh -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes -T git@github.com：沙箱内 Permission denied。
- 按权限流程在沙箱外重试相同命令：输出 Hi 18941602006! You've successfully authenticated, but GitHub does not provide shell access. 退出码 1，按成功输出判定 SSH 认证通过。使用 Windows 原生 OpenSSH，未读私钥、未改 SSH 配置。

### GitHub 状态

SSH 身份已验证；仓库 18941602006/X-Glasses 的历史、访问及写权限尚未核查。指定 SSH Remote 尚未写入本地配置。基线、备份分支、commit 和 push 均未建立。

### 当前风险与停止点

用户中断并要求先修订施工规范。停止在前置检查；没有测试基线或业务验证。Python 命令和提交身份问题留待恢复 Phase 0 处理。

## 2026-09-04 23:47 +08:00 / 规范对齐 / V3

### 本轮计划回放

先写 DEV_PROGRESS.md 开工计划，再将旧施工提示词统一修订为配套方案 V3 的现行规范。仅文档，暂停真实施工。

### 实际修改与文件

- 根 X-Glasses施工规范V3.md：完整现行规则，替代旧模板；原外部 txt 保持不变。
- 方案V3.md：更新现行状态、Phase 0–6 映射（2A USB、2B 前端），移除过时的“本轮只讨论”表述与歧义小节名。
- docs/construction/DEV_PROGRESS.md、LOG.md、HANDOFF.md：前置计划、事实日志和停止点交接；这些不是完整 Phase 0 文档体系。
- MEMORY.md：补记中断的开工检查及本轮规范修订。

### 文档漂移修正

1. V2 总纲改 V3，盲道/斑马线对照模块不再恢复。
2. USB CDC 和 ESP-IDF/esp_tinyusb 明确为当前实现路线，Arduino 旧默认值废止。
3. 手部加入 ToF 标定、数据归属、晚到结果、遮挡降级及用户确认。
4. 新电脑前端归 Phase 2B，Android 无障碍前端归 Phase 6。
5. MCU 禁止模型/导航决策，但明确有限基础告警例外和输出协调。
6. 备份覆盖范围明确；未提交文档不会因创建分支自动获得远端保护。
7. 交付 A/审计 B 两段收尾，不要求审计提交包含自身哈希。
8. 规范读取不自动执行旧模板内的“现在开始”；按当前用户任务及授权推进。

### 验证结果

PowerShell 文档一致性检查退出码 0，10 项全部为 True：V3 基线、删除旧对照模块、USB/ESP-IDF、手部帧号与距离归属、前端 2B 阶段一致、Phase 0–6 完整、MCU 例外边界、A/B 审计无自引用、身份/备份门槛、方案无旧 P 编号表行。6 个本轮文档均存在且可读。

未安装依赖、未执行 lint 或单元测试；尚非 Git 仓库，未运行 git diff --check。文本检查通过不等于 Phase 0 或业务测试通过。

### GitHub 状态及回滚判断

本轮不执行 git init/commit/push；无远端备份、无最终提交。原外部规范、方案 V2 保留；无 Git 回滚目标，不删除任何用户文件。

### 当前风险与下一步

规范可以定稿，但 Git 身份、Python 解释器、远端历史和模型许可/手机适配不是已解决事项。恢复时先完成 Phase 0 安全门槛，不直接写固件或跳到 Phase 1。

## 2026-09-04 23:58 +08:00 / Phase 0 恢复 / 身份门槛

- 用户指令：开始施工，每完成一部分报备。已报备第一部分环境/远端核查结果。
- 计划：见 DEV_PROGRESS 本轮及 progress/layers/00-foundation.md；先身份/Bootstrap/备份，再完整基础施工。
- 实际修改：追加 DEV_PROGRESS、LOG、HANDOFF、MEMORY；新增 00-foundation 层计划。均属备份前允许的计划/阻塞记录，不是业务代码。
- 检查：重读现行规范及已有进度/日志/交接，检查目录、文件列表；仍无 Git 仓库。Git 2.52.0.windows.1；git config --show-origin --get user.name / user.email 无输出、退出码 1。
- Python：发现 C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe；直接 --version 返回 Python 3.12.14、成功。只证明解释器可执行，未验证 venv/pip 或项目依赖。先前 PATH 无 python 的历史事实不变。
- 远端命令：git -c 'core.sshCommand=ssh -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes' ls-remote git@github.com:18941602006/X-Glasses.git。沙箱内失败（port 22: Permission denied，退出码 1）；按权限流程沙箱外原命令复试退出码 0、无 refs 输出。当前按空远端规划 Bootstrap，执行写入前需再次检查；不据此宣称写权限已验证。
- SSH 账号：沿用本日前次独立 ssh -T 验证的 18941602006，当前未更换客户端/密钥配置，未读取私钥。
- 未运行：依赖安装、lint、单元测试、git diff --check；尚未初始化，不得宣称 Phase 0 通过。
- 漂移：仅更新实际状态和待办，产品仍为 V3、USB、有 ToF 融合/新前端、无 SLAM/盲道/斑马线专项；未改技术方案。
- GitHub：无本地分支/HEAD/origin、无基线/备份/A/B 提交、无 push。全部准备资料未受远端备份保护。
- 回滚：无须 Git 回滚，未删除/覆盖业务文件；既有记录保留追加历史。
- 停止点：规范要求缺失身份在首次 commit 前询问；请求提交姓名及确认指定邮箱后继续。不擅用管理员名、不改全局 Git 配置。

## 2026-09-05 / Phase 0 / Foundation 实施与验证

### 计划、身份与备份

用户指定提交姓名 Trollhunter 并要求继续，邮箱沿用规范已指定值。仅仓库级配置，检查未见 GIT_AUTHOR/COMMITTER 环境覆盖。Git 2.52.0.windows.1（D:/Program Files/Git/cmd/git.exe），Windows OpenSSH（C:/WINDOWS/System32/OpenSSH/ssh.exe）；SSH 输出认证账号 18941602006，远端 ls-remote 再次无 refs。

git init -b main 后添加指定 SSH origin；显式暂存 README/.gitignore 并审查，Bootstrap fb23e6fbd1b822db85160e5f641af9b0bff9b02d 已 push、ls-remote 匹配。准备文件清单与 SHA256 见 PREPARATION_BASELINE；审查为项目方案/身份/路径历史，无凭据或采集数据，常见私钥/token/key 模式无命中（不等于通用秘密检测证明）。文档基线 76bb6d685a02a833056515350cd0a4eccee5d4fc 和 backup/pre-phase0-foundation-20260905-0006 均成功 push、远端一致。创建备份时无工作区变更，全程保持 main；此后才建真实 Foundation。

### 实际变更

建立根 AGENTS、使用说明、.gitattributes、空 .env.example、requirements-dev.txt、pyproject.toml；补齐产品要求和施工主要求/入口/架构/计划/工作流/回滚/测试/分层/工具文档；建立 01–06 进度、Android 迁移说明、firmware/server 各层/frontend/tools/tests 职责 README。新增 tools/check_foundation.py 与 tests/test_foundation.py；更新 MEMORY 和进度/交接。本轮不是固件、服务或 UI 功能施工。

### 错误、处理和复测

1. 沙箱 Git status/add 出现全局 ignore 文件不可读警告和 LF/CRLF 提示，但命令执行完成。未改全局配置；后续受控沙箱外核查无该权限警告，新增 .gitattributes 固定文本换行，不批量重写历史文件。
2. 沙箱执行器多次报 helper_unknown_error: setup refresh had errors（commit 检查命令重试两次失败，后续读文档/venv 也失败）；未执行命令被当作未发生。受控授权沙箱外执行后 commit、venv 和检查均正常。
3. apply_patch 编辑工具遇到同一 sandbox helper 故障，未落盘检查工具。批准后用其批处理入口重试，失败 The command line is too long；读取入口确认其原生 codex.exe --codex-run-as-apply-patch 调用后，经授权使用同一原生补丁入口成功。未改用任意 shell 写文件、未绕过授权。
4. 首次 pip check 成功、Ruff lint 通过、43 文件结构检查通过、13 项工具单测通过；format --check 返回需重排 tools/check_foundation.py。虽然当时组合命令最终退出码为 0，格式子项仍判失败，不隐瞒。运行 Ruff format 修复，并将检查工具自身与测试纳入必需清单（45 文件），随后逐项失败即停止的完整复测全通过。

### 最终本地验证

- Python 3.12.14，项目 .venv；pip 25.0.1。只从 https://pypi.org/simple 安装 requirements-dev.txt 精确锁定的 Ruff 0.12.12；标准库 unittest 无额外依赖，未安装重型包。
- python -m pip check：No broken requirements found。
- python -m ruff check .：All checks passed；python -m ruff format --check .：2 files already formatted。
- python tools/check_foundation.py：45 必需文件、Phase 0 目录/空配置/锁定依赖、Git 忽略探针通过；简单相对文档链接检查通过。
- python -m unittest discover -s tests -v：13 项通过，复测约 0.881 秒；覆盖有效基线、缺失/空文件、冲突标记、非空配置且不泄漏值、格式错误、浮动/重依赖、过早业务文件、坏链接、Git 缺失/非仓库/忽略失配。
- git diff --check：通过。暂存审查、提交和远端核验在下方后续审计记录。
- 没有 USB/固件/模型/前端/Android 测试，没有采集实测指标；基础单测不是业务验收。

### 漂移、风险与下一步

人工对照 V3：USB/供电/断连、无 SLAM/盲道斑马线专项、ToF 时空归属与降级、输出仲裁、2B 新前端/6 Android 均一致；后续层全部未开始。工具不认证语义安全、不访问外链或硬件；Phase 2 前按新范围升级 Phase 0 目录限制。无需回滚，未删除用户资料；备份及回滚方法见 GITHUB_ROLLBACK。

本地验收完成，准备 A/B 交付；此段不宣称尚未执行的最终 push。Phase 1 需审核开源底座、固定依赖/源码许可及 LocateAnything 权重用途；用途、具体手机、模块/供电仍待确认，当前不因此擅自下载或替换模型。

## 2026-09-05 / Phase 0 / 交付 A 审计

- 提交前复核仓库级身份/origin 一致；42 个明确暂存文件均小于 1MiB，暂存常见私钥/token/key 模式无命中；仅 .env.example 空值占位，环境/模型/数据未入库。人工复核代码/配置及文档范围，git diff --cached --check 与 diff --check 通过，结构检查仍为 45 文件通过。
- 新建 .gitattributes 自身尚未设置 eol=lf，暂存时出现其 LF→CRLF 提示；仅换行提示，非失败，不影响已指定的 Markdown/Python 等规则。未声称所有文件都固定 LF。
- A = 66dc754444148a818beb5a06af74f6ec2f0902b4，提交信息 chore: establish Phase 0 foundation and verified checks；42 文件，692 增/4 删，删除仅为更新状态摘要，不删除历史记录或用户资料。
- git push origin main 成功；ls-remote refs/heads/main 与 A 完整哈希比较一致。A 推送后 git status --short 无输出。
- Phase 0 已完成，备份保持在 76bb6d685a02a833056515350cd0a4eccee5d4fc。无业务/实机验证结论。
- 此次补写 README 当前状态、MEMORY、进度/层进度、LOG/HANDOFF 构成审计 B。B 自身哈希不写入 B；最终 push/HEAD/remote/status 由终端核验，下一轮补记。未启动长期服务进程；pip 进程已结束。

## 2026-09-05 / Phase 1 / 来源与风险审核

### 开工与备份

用户要求继续下一步。补记上轮 B = 34fcde23e9bfa9161ff2c4175bd7c2104ac7cfb3；本轮核验 main/远端一致、工作区干净、身份 Trollhunter / d.o.n.0907@qq.com、SSH 账号 18941602006、指定 origin 不变。先写 DEV_PROGRESS/01 层计划，再 push backup/pre-phase1-audit-20260905-0026，ls-remote 与 B 一致；两份开工计划当时未提交，明确不在备份覆盖内。

沙箱首次执行仍报 helper_unknown_error: setup refresh had errors，按受控授权沙箱外读取和执行；文件编辑仍用 apply_patch 原生入口，未读取密钥/改变全局设置。

### 研究与实际修改

按 Search 技能读取检索/代码模式/提取/来源质量/综合说明，三组 Exa 查询各 numResults=5，共请求 15 条候选，按实体归并并排除聚合页；不是 15 个独立已验证来源。查询覆盖旧底座、LocateAnything、USB/硬件。Exa fetch 默认结果部分截断，后续官方 raw/API 和 web 定点补读许可/清单/关键源码，不用索引当最终证据。没有用子代理。

新增 docs/dependencies/{sources.audit.json,README.md,REUSE_REVIEW.md,ENVIRONMENT_GATES.md}、docs/hardware/INTERFACE_REVIEW.md、docs/android-migration/PHASE1_RISKS.md、exa-results/phase1-audit-2026-09-05/README.md，新增 tools/check_source_audit.py 和 tests/test_source_audit.py。更新 AGENTS/README、架构/测试/回滚/进度/交接/MEMORY 及工具说明，无业务源码导入。

关键实证：旧 bridge_io/sync_recorder 全文，其余主程序/导航/拿取/音频等仅 imports/结构和选段，明确非整仓审计；旧帧桥丢失源帧/采样时间，录制器固定 FPS 不等于真实同步。ToF 猜测的 STMicroelectronics/vl53l5cx API 请求 404，改核 STM32duino 来源，确认其 Arduino/TwoWire/C++ 类耦合，不能原样用于 ESP-IDF。

模型许可差异：搜索索引曾返回根 LICENSE_MODEL 的旧“academic/non-profit”文本，但固定 Eagle 783f656d127ee498137b5ff52603ce36c292d317 根路径 raw 为 404；Embodied/LICENSE_MODEL 与 HF c32291ca5e996f5a7a485845b4f57a233936bba0/LICENSE 实际均为 research/evaluation，模型卡仍保留更窄描述。已记录冲突，旧历史不删除、不自动解除 blocked_use。HF 只读取 metadata/config/LICENSE/README，未下载权重或执行远程模型代码。

USB 三项候选为 IDF 5.5.4、esp_tinyusb 2.2.1、camera 2.1.7，清单最低 IDF 版本兼容但传递依赖未解析。esp-usb 总仓许可证 API 返回 NOASSERTION，单独核对组件 Apache-2.0，未误判无许可。其余源码按 root license 和 commit 核对，未逐文件或对全部转依赖做法律/CVE 审计。硬件只给设计级模块/电平/引脚/地址表示与上电检查，无采购或电流实测。

### 失败与验证

首次 lint、17 来源/6 报告检查和 23 单测通过；format --check 发现 tools/check_source_audit.py 需格式化，单独记失败，组合终端最后返回 0 不代表格式子项通过。Ruff format 修复后逐项失败即停复测：pip check 成功，Ruff check 成功，4 文件 format 已符合，基础检查 45 文件通过，来源检查 17 条/6 报告通过，23 单测通过（约 0.921 秒），git diff --check 通过。

新 10 测试覆盖正常快照、错误 schema/空条目、重复来源、浮动 revision、许可链接未固定、伪造 runtime_verified、擅自解除模型暂停/移除模型以及缺少关卡。检查不认证许可适用/安装兼容或实机能力。

### 漂移、风险、回滚与交付状态

已将当前阶段更新为 Phase 1 并补来源/环境/硬件合同，保留 USB、无 SLAM/盲道斑马线专项、手部融合、新前端；未改识物模型。当前仅基础 .venv 依赖，未安装新增运行包；全部快照 runtime_verified=false / imported=false。

本地审核成果通过检查，A/B 尚待下方审计记录；不预写本轮 push。无需回滚，未删除用户资料。权重用途/许可差异、传递锁/编译、ToF 平台适配、采购模块/手机和其他权重许可仍为开放关卡；允许后续做不依赖模型的 USB 软件设计，但不以本阶段结论放行全部模型或佩戴测试。

### 用户追加用途确认与复测

用户在本轮施工中明确“LocateAnything为测试使用，不为学术或盈利为目的，所以放心去使用，请继续”。依据固定 LICENSE 的 research/evaluation 范围，将模型从 blocked_use 改 evaluation_only，记录用户原意、日期和许可来源，去掉等待用途确认关卡；保留说明页措辞差异。不得扩大为商业/生产使用，用户陈述不替代版权许可。没有下载/加载模型或执行远程代码。

审核工具相应接受有明确记录的有限评测，不允许无记录评测或伪造商业许可；增加两项授权边界单测，原限制提升测试改为禁止升级无约束候选。格式化后 lint/来源检查通过，25 单测通过（约 0.918 秒）。同步当前权威报告与摘要，旧 blocked_use 日志保留为历史。

## 2026-09-05 / Phase 1 / 交付 A 审计

最终显式暂存 21 个审核相关文件，检查体积均小于 1MiB、常见私钥/token/key 模式无命中、变更 Markdown 相对链接均存在；基础结构/来源台账/pip/lint/format/25 单测及工作区/暂存 diff --check 全通过（最后单测约 0.887 秒）。无采集数据、模型、环境或业务源码入库。

A = fb9d88a18ed6efe9acbdca5b397754fe9e43c3c3，21 文件 891 增/8 删（状态摘要更新，未删除历史或用户资料），已 push 指定 origin main，ls-remote 完整哈希一致；A 推送后 git status --short 无输出。开工备份仍为 backup/pre-phase1-audit-20260905-0026 → 34fcde23e9bfa9161ff2c4175bd7c2104ac7cfb3。

交付定义：Phase 1 来源/风险审核成果已交付，LocateAnything 用途明确为 evaluation_only；不是全部运行/硬件关卡通过。下一步可规划 Phase 2A USB 协议/输入/回放，并按实施范围逐项锁依赖与编译验证。此追加记录构成审计 B，不包含 B 自身哈希；终端最终核验 B/remote/status，下一轮补记。没有长期进程需要停止。

## 2026-09-05 / Phase 2A 第一部分 / 实施记录

开工：补记 Phase 1 B = 08aaecc722750e59a5009a19bed8d39a099bf08c，main/指定 origin/本地 Trollhunter 邮箱/SSH 18941602006 核验，无 GIT_AUTHOR/COMMITTER 覆盖，工作区干净，远端 main 一致。DEV_PROGRESS 和 02 层先写计划，backup/pre-phase2a-protocol-20260905-0110 成功 push、ls-remote 完整哈希相同，随后才实施，计划两文件当时不在备份内。

实际修改：server/common/protocol.py、server/input/{frames,stream,recording}.py，tools/replay_usb.py，tests/test_usb_{protocol,recording}.py，docs/protocol/USB_V1.md；升级 check_foundation 与测试的精确阶段白名单，同步入口/层说明/架构/合同/测试/备份/进度/交接/MEMORY。共 4 个运行文件，均标准库，没有依赖安装或第三方代码拷贝。

实现边界：v1 36 字节包头、CRC/4096 负载上限、500ms 部分包/帧本地 TTL、256KiB 最大 JPEG，短读写与会话清理；仅 SOI/EOI 检查、不解码。保留 capture_us，但源时间映射/标定为空；其他包类型原样返回，不假装完成 ToF/IMU/ACK/对时。XGR1 有界 64MiB 原始记录、CRC/时间/截断检查和虚拟时间回放；文件边界 EOF 不证明完整采集。CLI demo 只在内存生成一帧 6 字节标记数据，标 synthetic/replay/unsynchronized/hardware_verified=false。

失败与处理：首次普通终端失败 helper_unknown_error: setup refresh had errors，受控授权沙箱外执行，同一原生 apply_patch 入口编辑。必读文件一次组合读取截断，分批补读；误写 02-usb-link.md 路径后按规范实际 02-glasses-link.md 完整读取，无文件被该错误改变。首次全量 Ruff I001 指出 test_usb_recording 导入排序，停止扩展并 Ruff --fix 修复；之后 format/check、53 文件结构、17 来源、54 测试和 pip check 通过。新增最大帧/读写逾期/虚拟 tick 三测试后 31 项协议回放测试通过。文档补丁 TEST_METRICS 尾行上下文未匹配，前面 10 余文件已落盘；先只读核对，再单独补齐两份未更新文档，未假设整补丁原子性。

漂移：将无业务代码/Phase 1 当前状态更新为 2A 主机软件子项，白名单只开放 4 文件；USB/无 SLAM/盲道斑马线专项/手部融合和前端阶段保持。整个 2A 未通过，固件/实际 CDC/握手/心跳/传感器/对时/ACK/告警/供电和 30 分钟实机仍未测，无硬件安全结论。用户新指令连续推进全项目已记 MEMORY/进度，后续不在小检查点后停工等确认。

当前待最终检查和 A/B，未预写推送成功。没有用户资料删除，无需回滚；若撤销以本次备份及明确提交 revert 为依据。无长期服务或硬件采集进程。


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

## 2026-09-05 / Phase 4 LocateAnything 与拿取辅助核心

从开发分支 B = 66eeb8ab8d95f1b8157260730067eed3b0b4a566 创建并核验 backup/pre-phase4-locate-grasp-core-20260905 后施工。新增 common/geometry、locate/contracts、locate/grasp、LOCATE_GRASP_V1 和 9 项合成测试；navigation 复用共享矩形类型，基础白名单同步扩展。

首条 unittest 模块路径因 tests 非包而失败，改用 discover。首轮业务测试发现 ToF 投影矩形在边界包含同一点，修复为左闭右开确定归属；第二轮一项无效深度夹具仍指向旧 zone，改为目标实际 zone。随后 116 项全量测试通过，1 项可选 pyserial 跳过；110 文件基础检查及 compileall 通过。系统 Python 未安装 Ruff，随后找到仓库固定 `.venv` Ruff 0.12.12，修复 1 处导入排序并格式化 2 文件后 check/format 通过；未安装新工具。

安全边界：LocateAnything 仍为 evaluation_only，未下载权重、未执行 remote code；host 保留时间和标定元数据，worker 只能返回目标框。无效/过期/错会话/错标定/低质量/遮挡/同区深度全部降级，二维重叠不自动完成，只有有效期内一次性 button/voice 确认可完成。无真实模型、标定或硬件结果。

## 2026-09-05 / Phase 5 辅助功能与输出仲裁

从 B = 9455b7c783fefcb1f265cde659456107384689b4 建立并核验 backup/pre-phase5-assist-arbitration-20260905。新增 assist contracts/worker、arbitration core/adapters、output executor、ASSIST_OUTPUT_V1 和 23 项测试，扩展基础范围及对应 README/架构/进度。

首批 13 项合同/仲裁测试通过，Ruff 提示 2 文件格式差异；审查发现仲裁跨层导入私有校验函数且自由文本可能绕过过街限制，改为公开严格校验并在 OutputCandidate 全局拒绝常见中英文授权短语，新增类型/空白测试。再补 worker 超时/请求上限、输出执行回执及道路/拿取/辅助映射，阶段测试增至 23 项。

最终 139 项全仓测试、117 文件范围、17 来源/6 报告、compileall、Ruff 全仓 check/format、diff check 通过。没有新增依赖、真实网络调用、密钥、模型、地图、TTS 或硬件执行；fake transport 只验证边界，不验证识别/导航/对话质量。

## 2026-09-05 / Phase 6 Android 第一软件检查点

用户取消电脑摄像头测试后恢复 Phase 6。基线 a3e2e315d5f821256fdcbb908e9323ee84fc3fb3，backup/pre-phase6-android-20260905 已推送核验同值。本机 Java/Gradle/ADB/SDK 均未发现；公开版本网页检索无可审计正文，固定版本标 candidate_unresolved，不安装工具链。

新增独立 Android 工程、任务 reducer、Compose UI、UsbSessionManager、XgProtocol、Kotlin 测试源码、Android 静态 checker/测试、依赖候选和团队验收文档。超长首批补丁在进程执行前因 Windows 206 拒绝，确认 android 目录不存在后拆为五批。黄金向量首写 header CRC 错为 7960e3e7，Python 冻结实现生成真实完整向量后修正为 26184fbc；静态检查要求显式 XG03 同步修正。

审查另发现 bulk endpoint 打开不能等同握手 READY，新增 TRANSPORT_OPEN，当前不会启用风险监测。最终 Android 静态 17 文件、6 项回归、全仓 145 项、122 文件、来源、compileall、Ruff/diff 通过。未执行 Kotlin/Gradle/APK/真机，Kotlin 测试源码不计入已运行数字。

### Phase 6 第二软件检查点

第一检查点 A = a3fc152384cd20a453fd19256468ac039d128de2 已推送远端一致。新增 ControlSession/AndroidHostLink 和 Kotlin 测试，接入随机会话、nonce、必需能力、boot、序号与握手/心跳 deadline；当前固件只有 CLOCK，按设计不能 READY。人工审查修复 HELLO 当场写失败后外层状态覆盖竞态。

重复提示首个补丁因 hunk 分隔格式错误被拒绝、未落盘，拆分两次成功。新增 checker 对 READY 来源、repeat、TalkBack触点和 Python/固件黄金后缀的破坏性测试。最终静态 20 文件、7 项回归、全仓 146 项、Ruff/diff 通过；12 项 Kotlin 测试仍只是源码。
## 2026-09-05 / Phase 6 高德地图接入开工

- 用户确定国内地图使用高德。本轮采用高德 Android 地图/搜索 SDK，而不是把 Web 服务 Key 直接放入 APK 请求；Android Key 将绑定 applicationId 与 debug/release SHA1，并只由本机 Gradle 属性注入。
- 基线 `868e1ef8adcd865273abe6a88752b6518d96cf19`，当前分支 `development/continuous-build-20260905`。工作区仅发现未知 `.workbuddy/`，明确排除。
- 施工范围：隐私授权门、POI/步行路线适配、WGS84/GCJ-02 归一化、导航 provider 延迟配置、Compose 状态与静态合同/文档。
- 尚未施工或验证；先提交本计划并从安全基线建立远端备份。

## 2026-09-05 / Phase 6 高德地图接入实施与验证

- 备份 `backup/pre-phase6-amap-navigation-20260905-1531` 已 push/ls-remote 核验与 `868e1ef8adcd865273abe6a88752b6518d96cf19` 一致。SSH 账号 18941602006、仓库身份 Trollhunter、指定 origin 正确；未知 `.workbuddy/` 未读取/修改/暂存。
- 新增高德 POI/步行路线 provider、WGS84→GCJ-02 转换、SDK 隐私同意持久化/拒绝/撤回；MainActivity 在保存同意前不创建 provider。Compose 显示服务提供方、处理目的/信息类型、官方政策入口和服务状态。Key 仅从 `AMAP_ANDROID_KEY` 本机属性注入，Manifest 保留占位符。
- 构建固定 `10.1.300_loc6.4.9_sea9.7.4`、ARM ABI 和官方混淆范围。官方文档示例 `10.1.200...` 从 Central 请求 404；随后实际下载 10.1.300 JAR 到系统临时目录，SHA256 `E135AE1016A463DCDCA6CED385060D52486BAA9FE9076E08181619067176B365`，并确认路线回调、异步 POI/步行和隐私公开方法存在。临时文件未入库。
- 首次 Android 破坏性回归 10 项中 1 项失败：新增高德断言被误插入原断链测试方法；生产静态合同当时已通过。移动断言到正确方法后，10/10 复测通过。Ruff format 初检提示 2 个 Python 文件需格式化，执行格式化后复测通过。
- 最终执行：pip check、124 文件 foundation、17 来源/6 报告、30 文件 Android checker、全仓 149 项 unittest、compileall、Ruff check/format、`git diff --check`，均通过。21 项 Kotlin `@Test` 仅为源码，因本机没有 Java/Gradle/Android SDK 未运行；未构建 APK、未使用真实 Key、未测试 GPS/路线/坐标偏移/TalkBack/弱网/配额/隐私合规或真机安全指标。
