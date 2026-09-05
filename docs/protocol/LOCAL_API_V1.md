# localhost 调试 API v1

服务仅绑定数值回环地址 `127.0.0.1`，不提供 CORS，不是远程控制接口。Vite 开发服务器通过同源代理访问；生产部署应由同一个本地壳层提供静态文件和 API。默认服务没有设备 dispatcher，命令返回 503，不能演示为硬件已执行。

- `GET /api/v1/health`：进程存活，不代表眼镜在线。
- `GET /api/v1/status`：`xg.status.v1` 快照，包含 revision、mode、link/clock、frame/source/age、ToF/IMU、calibration、最多 32 条命令和 100 条日志。uint64 标识和纳秒时间使用十进制字符串，禁止转为 JavaScript number 后丢精度。
- `POST /api/v1/commands`：唯一 JSON 字段 `action`；允许 `start_stream`、`stop_stream`、`cancel_haptic`、`safe_stop`。成功接收返回 HTTP 202 和 `request_id/state=pending`；最终 applied/rejected/expired/timeout/disconnected 只能来自后端状态更新。

请求体上限 1024 字节，未知字段/动作拒绝。API 不提供任意震动强度入口，前端不得直连串口或使用前端自增 ID 伪造 request_id。`safe_stop` 的实际调度必须由后端依次取消输出/停止流，并保留每个底层 ACK；本阶段只定义请求合同，没有连接真实 HostLink。
