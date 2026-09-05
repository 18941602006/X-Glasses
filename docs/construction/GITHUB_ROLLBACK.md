# GitHub 与回滚

## 2026-09-05 / Phase 6 高德接入前备份

`backup/pre-phase6-amap-navigation-20260905-1531` → `868e1ef8adcd865273abe6a88752b6518d96cf19`，已 push 并由 `ls-remote` 核验。覆盖此前地图导航审计 B；不含随后追加的本轮计划与高德代码，也不含未知未跟踪 `.workbuddy/`。始终在 `development/continuous-build-20260905` 施工；如需撤销，先审查本轮 A，再优先普通 `git revert`，不得覆盖用户文件。

最新第二部分备份：backup/pre-phase2a-control-20260905-0200 → a7bb773726bb6ab5a9a22bfbba9c726ee7ae933a，push/ls-remote 已一致。覆盖第一部分 A/B，不含当时两份未提交计划；始终 main 施工。无回滚/删除操作。

指定 origin：git@github.com:18941602006/X-Glasses.git。提交姓名 Trollhunter，邮箱 d.o.n.0907@qq.com（仓库级）；SSH 账号必须为 18941602006。

## 已核验基线

- Bootstrap：fb23e6fbd1b822db85160e5f641af9b0bff9b02d，仅 README/.gitignore。
- 准备文档基线：76bb6d685a02a833056515350cd0a4eccee5d4fc。
- 远端备份：backup/pre-phase0-foundation-20260905-0006，已核验与准备基线相同。
- 覆盖：Bootstrap + 8 份准备文档和 PREPARATION_BASELINE 哈希清单；不包含本次备份之后新建的 Foundation 文件。
- 创建备份时本地状态为空、仍在 main；未检出备份分支开发。

## 常规回退

先 git status --short、git log --oneline、git show <目标提交>，确认影响和用户改动。优先在 main 对明确错误提交 git revert <提交>，解决冲突并复测，审查后普通 push。不得默认使用 reset --hard、clean、覆盖式 checkout 或 force push。

备份用于对比/恢复依据，不意味着可以覆盖当前用户文件；恢复某文件或切换工作树须先明确范围与授权。多提交回退检查先后/合并关系，不给未经核查的范围命令。当前没有需要执行的回滚。

## 核验

git ls-remote origin refs/heads/main refs/heads/<备份名> 与本地 git rev-parse 对比。认证成功不等于仓库可写；push 后核验才算交付。A/B 哈希见 LOG/HANDOFF 最新记录；B 自身在终端核验，下轮记入日志。

## 2026-09-05 / Phase 1 开工备份

backup/pre-phase1-audit-20260905-0026 → 34fcde23e9bfa9161ff2c4175bd7c2104ac7cfb3（Phase 0 审计 B），已 push 并 ls-remote 核验。覆盖此前完整 Phase 0 交付；两份本轮开工计划在备份创建时未提交，不在此备份内，随本轮审核交付保存。未在备份分支开发，未回滚或覆盖任何用户资料。

## 2026-09-05 / Phase 2A 第一部分备份

backup/pre-phase2a-protocol-20260905-0110 → 08aaecc722750e59a5009a19bed8d39a099bf08c（Phase 1 审计 B），已 push 并核验完整哈希。覆盖完整已提交 Phase 0/1；本轮 DEV_PROGRESS 与 02 层开工计划在当时未提交，不被该备份覆盖，随交付 A 保存。始终在 main 开发，无回滚/删除操作。后续如需撤销，先审查本轮 A，再经授权 revert 明确提交，不覆盖用户文件。
