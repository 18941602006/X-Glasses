# localhost API

Phase 2B 的电脑调试台边界：只绑定回环地址，输出显式来源/时效/未知状态，并把前端操作变成后端请求。前端不能持有串口对象，也不能把 pending 当作硬件已执行。默认启动时没有设备和命令分发器，因此所有硬件能力显示不可用。

开发入口：`python -m server.api`。接口合同见 `docs/protocol/LOCAL_API_V1.md`。

电脑真实任务需明确使用`python -m server.api --pc-runtime`启用；默认独立.venv-pc进程运行选图找物或用户同意的DeepSeek文字，不开放文件路径/Key接口/云端图片。单活动任务、有界记录、超时、取消和后台查询；与设备状态/控制隔离，设备不因此READY。合同见[PC_JOBS_V1](../../docs/protocol/PC_JOBS_V1.md)，操作见[电脑运行说明](../../docs/dependencies/LOCATE_PC_RUNTIME.md)。
