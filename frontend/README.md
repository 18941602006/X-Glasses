# frontend

Phase 2B 新 React/TypeScript/Vite 电脑调试台。显示 USB/时钟、帧龄与来源、ToF/IMU 有效性、capability、标定、日志和 request_id/ACK；所有命令经 localhost API，不直连硬件。手机 UI 在 Phase 6 独立开发，不复用本页面代码。

开发：先运行 `python -m server.api`，再在本目录执行 `npm run dev`。默认 API 无设备 dispatcher，页面应显示离线且命令禁用。`npm test` 做交互语义测试，`npm run build` 做类型和生产构建。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
