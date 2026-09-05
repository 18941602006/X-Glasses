# localhost API

Phase 2B 的电脑调试台边界：只绑定回环地址，输出显式来源/时效/未知状态，并把前端操作变成后端请求。前端不能持有串口对象，也不能把 pending 当作硬件已执行。默认启动时没有设备和命令分发器，因此所有硬件能力显示不可用。

开发入口：`python -m server.api`。接口合同见 `docs/protocol/LOCAL_API_V1.md`。
