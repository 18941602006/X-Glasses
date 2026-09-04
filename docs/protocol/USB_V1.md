# USB 二进制合同 v1 / Phase 2A 软件子交付

状态：2026-09-05 冻结主机端分包布局与回放格式，已做纯模拟测试，尚无固件互通。不是 Phase 2A 完整验收。后续变更必须同步 Python/固件/测试向量并升级不兼容版本，不沿用旧 Wi-Fi 帧桥。USB CDC 数据流不混裸日志。

## 消息布局

全部多字节整数 little-endian、无隐式填充。CRC 为 CRC-32/ISO-HDLC（标准校验向量 `123456789` → `0xCBF43926`，Python zlib.crc32），线上 uint32 小端。CRC 仅检测传输损坏，不认证设备或用户。

| 偏移 | 字段 | 字节 | 规则 |
| --- | --- | --- | --- |
| 0 | magic | 4 | ASCII XG03；表示项目 V3 基线，不是协议版本号 |
| 4 | version | 1 | 1，不兼容版本拒绝 |
| 5 | kind | 1 | 1 JPEG；2 ToF；3 IMU；4 BUTTON；5 STATUS；6 COMMAND；7 ACK；8 CLOCK |
| 6 | flags | 2 | 当前只能为 0 |
| 8 | session_id | 8 | 非零；每次设备启动/主机重新握手使用新值，握手机制待下一子任务 |
| 16 | sequence | 4 | 每个方向各自递增；允许 uint32 回绕；前向差必须小于 2^31 |
| 20 | capture_us | 8 | 设备单调采样微秒；不能填主机收包时间；消息类型语义后续细化 |
| 28 | payload_length | 4 | 0–4096；在分配/等待前检查头 CRC 及上限 |
| 32 | header_crc | 4 | 对字节 0–31 校验，保护长度等元数据 |
| 36 | payload | 0–4096 | 原始负载 |
| 36+length | payload_crc | 4 | 仅 payload；空负载 CRC=0 |

最大发包 4136 字节。单次 feed/read 上限 65536；解析器分段处理，持久未完成缓冲小于一包，内部瞬时缓冲小于两包，输出列表受单次输入上限约束。调用方须及时消费返回列表，不另外建立无限队列。坏头/坏负载向后寻找 magic，不能依赖换行。部分包 500ms 未完成丢首字节并重同步；空读也必须调用 feed/tick 以驱动超时。预算为模拟起步值，非实测安全阈值。

底层 InputSession 除 JPEG 外原样返回封包。Phase 2A 第二部分新增 HostLink 及 [CONTROL_V1](CONTROL_V1.md)，已实现主机传感器归一化解析、握手/心跳、ACK 关联、CLOCK 误差/过期估计；固件与真实串口仍未接入，不得把模拟 ACK 当成实际执行成功。

## JPEG 分片与时效

负载前 12 字节为 uint32 frame_id / uint32 total_length / uint32 offset，其后是非空 JPEG 片段。因此单片图像最多 4084 字节，完整 JPEG 最多 256KiB。每帧所有片段必须同 session/frame_id/采样时间/total；USB 有序流只接受连续 offset。乱序/重叠/不一致废弃当前组帧，不为图像重传；更大的新 frame_id 的 offset=0 抢占旧组帧。帧号同样按半范围规则回绕，重复起始帧不再发布。

只保留一个在组帧和一个最新完整帧；上层 pop_latest 消费一次即清空。组帧和完整帧从首个完整片段解析时刻起最长保留 500ms，超时丢弃。该限制仅控制本地驻留，**不能检测设备/USB 中已积压的源帧**，不能作为真实帧龄。后续对时后须再按映射采样时间/误差界限判断新鲜度。

Frame 保留 session/frame_id、设备 capture_us、首片解析/完成的主机单调 ns、origin、原始 JPEG。mapped_capture_ns 与 calibration_id 当前为 None，timing_status=unsynchronized；未标定不得进入安全相关融合。仅检查 SOI/EOI 标记，不解码或保证 JPEG 合法；下游安全解码/分辨率上限仍待实现。演示中的标记包不是实际图像。

## 会话、读写与断连

InputSession.start 必须由将来的可信握手控制器显式调用；普通包不能切换会话。不同 session 和重复/旧 sequence 拒绝，跳号累计诊断。start/disconnect 清空解析缓冲、组帧、最新帧、顺序状态，并暴露失效原因。不同会话不得融合。

ByteStream 为注入接口，不是已完成的 pyserial/USB 适配器。read/write 必须自行遵守传入的主机单调 deadline_ns；Python 同步核心不能抢占一个永不返回的驱动。read 短读正常，b'' 是空闲 tick，不能单凭它判断拔线。驱动 OSError/超时使 poll 清理会话；真正设备移除通知、链路心跳超时、重连退避和主机失联播报尚待实现。没有背景线程/扬声器/震动操作。

write_packet 完成短写并检查截止，零进度/异常失败；返回仅说明字节写入，不是 MCU 执行或 ACK。写失败可能留下半包，后续控制器必须废弃链路/重新握手，不能直接重发有副作用命令。本轮没有命令队列或调度器；固件须在 JPEG 分片间插入高优先级包。

## 录制 / 回放 XGR1

仅供显式触发的原始输入日志，不是固定 FPS AVI；录下实际短读/损坏字节、会话和空闲 tick，回放复用同一接入核心。Writer 接收调用方已打开的 BinaryIO，必须在用户点击录制后用独占 `xb` 新建 recordings/ 内文件，不能默认打开/覆盖/上传。本轮没有录制按钮、真实设备采集或文件落盘演示。

文件头为 `XGR1\r\n\x1a\n` 8 字节 + source uint8（1 synthetic / 2 live）+ 前 9 字节 CRC uint32。每记录为 kind uint8 + elapsed_ns uint64 + payload_length uint32 + payload + 前 13 字节与 payload 的 CRC uint32。elapsed_ns 为从录制起点经过的主机单调时间，非 UTC、曝光时间或设备采样时间；非递减，允许同值。

记录 kind：1 START，payload 非零 session uint64；2 RX，1–65536 字节；3 TICK / 4 DISCONNECT，空 payload。文件总上限 64MiB，超限显式关闭并由用户继续新文件，禁止无限增长。头版本/CRC、记录类型/长度/时间/CRC、截断严格检查。完整记录边界 EOF 是有效前缀，**无封尾标志，无法证明录制正常结束或检测删去整条尾记录**；不把回放读取成功叫作完整采集证明。

回放采用虚拟时间，无 sleep、无硬件输出；Frame.origin 始终 replay，文件中的 synthetic/live 仅说明原始来源。回放 EOF 或异常清理内部会话，已迭代消费的前缀帧不保证后续文件也有效。CLI 完整读取成功才给出汇总；失败返回非零，不显示成功汇总。不加载 JPEG 解码器/模型、不播放音频。

## 本地验证入口

项目根目录：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m tools.replay_usb --demo
.\.venv\Scripts\python.exe -m tools.replay_usb --replay recordings/example.xgr
```

第三条仅在用户已产生对应日志时使用。demo 纯内存生成 1 个 6 字节标记帧，输出 synthetic/replay/unsynchronized/hardware_verified=false，不写文件。没有图像质量、吞吐、端到端 P95、电流或 30 分钟实机结论。
