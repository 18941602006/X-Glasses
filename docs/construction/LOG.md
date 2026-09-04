# X-Glasses 施工日志（追加记录）

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
