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
