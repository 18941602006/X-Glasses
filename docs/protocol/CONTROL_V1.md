# USB v1 控制与传感器合同 / Phase 2A 第二部分

串口层补充：server/input/serial_port.py 已接入可选 pyserial 3.5，工具 usb_probe 仅显式指定端口探测握手/对时。实际安装/只读枚举/内存回环见 [运行台账](../dependencies/INPUT_RUNTIME.md)；没有接通眼镜硬件。新对时样本相对前一有效样本超出 RTT/量化/假设漂移预算时清空旧估计，等待重新采样，不继续沿用旧时钟。

本文件补充 [包头/JPEG/XGR1](USB_V1.md)。所有布局 little-endian，无隐式填充；只完成 Python 主机与模拟测试，ESP-IDF 互通、晶振漂移、功耗和执行机构尚未实测。封包头 host→device 的 capture_us 当前必须为 0；device→host 数据为设备采样/事件时间，CLOCK 响应为发送采样时间。session 每次连接新建非零随机 uint64；本轮主机核心接受上层注入，未来适配器必须生成随机数，不使用测试常量。

## 会话与存活

STATUS subtype=1 HELLO `<BQ>`：1 与 host_nonce uint64；使用拟定 session 包头发送。设备确认支持协议后清空旧命令/流状态与旧 TX 队列，绑定新 session，回复 subtype=2 WELCOME `<BQQI>`：2、原 nonce、非零 boot_id、capabilities uint32。boot_id 每次启动更新；nonce 精确回显仅防陈旧响应，不是密码认证。当前 capability 位保留用于声明能力，主机尚不以其授予设备执行权限，实际拒绝能力不足命令由固件 ACK 回报。

握手 2s 截止；未经成功握手的图像不能进入当前帧。设备每 500ms 发 STATUS subtype=3 HEARTBEAT `<BQ>`：3 与 boot_id；1.5s 无心跳或 boot_id 改变即失联，清帧/传感器/按钮/时钟/待确认命令。坏包和普通视觉流不代替心跳。半包超时重同步在 tick 找到的包仍交给状态机处理，不静默丢失。

以上周期是模拟预算，不是实测。HostLink 无串口线程、无扬声器/马达操作；适配器必须按短周期调用 tick、识别真实拔线并调用 disconnect。消费方以 state/reason 为准，不以 socket 或 CDC 端口打开代表设备就绪。原始 InputSession 供调试回放使用，不自带握手；实时链路应使用 HostLink。

## 归一化传感器

ToF payload：`<IBB>` sample_id/rows/columns，后接 rows*columns 个 `<HBB>` distance_mm/normalized_valid/raw_status。仅 4×4 或 8×8；valid=1 距离 1..65534mm，valid=0 必须 65535 哨兵、上层值 None，其他组合拒绝。不把无回波变成 0 或无穷远。此数值范围仅线格式范围，**不是传感器有效量程声明**。raw_status 保留厂商原始码；驱动必须依固定 SDK 判定有效/不确定，不能未经核验复制模拟中的码值。质量门槛/积分时间/分区映射/外参待驱动与标定，不因 normalized_valid=1 就断言距离属于目标。

IMU payload `<I6fB>`：sample_id、3 个加速度（m/s²）、3 个角速度（rad/s）、valid=0/1。所有 float 必须有限；valid=0 是无效样本，不能积分为可靠航向。传感器方向/轴映射/饱和条件待硬件验证。

BUTTON payload `<IBB>` event_id/button/pressed：button=1/2，pressed=0释放/1按下，防抖由固件负责。HostLink 事件队列上限 32；take_buttons 按源时效消费一次，过期/未对时不执行用户动作。不能将 pressed 自动当成功拿取或关闭风险监测。

## 四时间戳对时

CLOCK 请求 `<QQ>` request_id、host_send_ns；响应 `<QQQQ>` request_id、原 host_send_ns、device_receive_us、device_send_us。仅接收匹配的单个在途请求，2s 过期。主机收到时获取 host_receive_ns，不用 wall clock；设备必须在实际收/发处采样，不能伪造 USB 曝光时间。

扣除设备处理耗时的 RTT 必须 0..100ms。主机估计偏移为 `((host_send+host_receive) - 1000*(device_receive+device_send))/2`，误差初值 RTT/2 + 2µs。保存最多 8 个样本，按当前误差预算选择最小者；5s 后失效，随时间增加 200ppm 漂移预算。**200ppm 是未实测假设，不是晶振精度保证**；超范围实际漂移会使误差界限失效，实机阶段必须测量、冻结预算并检测异常。

映射不是内外参标定；Frame 包含 mapped_capture_ns、time_uncertainty_ns、timing_status=estimated，calibration_id 仍空。HostLink 当前有效数据接口拒绝未对时、误差>50ms、最坏源帧龄>=500ms、明显未来时间和本地驻留>=500ms；这是工程防陈旧预算，不认证行进安全。无效 ToF/IMU 即使时间有效也仍保持未知。

## 命令与 ACK

COMMAND `<QBQHB>`：request_id uint64、opcode uint8、device_deadline_us uint64、duration_ms uint16、intensity uint8。opcode 1 START_STREAM、2 STOP_STREAM、3 HAPTIC、4 CANCEL_HAPTIC。HAPTIC 仅 1..500ms、强度 1..255，非震动命令参数为 0。START/HAPTIC 须有新鲜对时，设备截止时间按 500ms TTL 扣除时钟误差保守计算；STOP/CANCEL 可不依赖对时，deadline=0，只取消/停止，不产生动作。

ACK `<QBB>`：request_id/opcode/result，result=1 APPLIED、2 REJECTED、3 EXPIRED。主机最多 8 个在途命令、结果环形队列 32，500ms 未收到匹配 ACK 则 timeout；错 session/opcode/未知或重复 request 不可转成功，迟到 ACK 不恢复成功。结果含 session_id，不让新会话复用 request_id 误关联。write 成功仍是 pending；不自动重试执行机构命令。

设备实现必须：执行前核对 session、opcode/范围/截止；按 session+request_id 去重并缓存 ACK，重复请求不重新触发；队列有界；HELLO/断连/看门狗清旧震动与命令；本地风险输出与主机输出统一调度。本文件未实现 MCU 行为，Python ACK 模拟不证明马达已动或实际安全。

主机控制入口后续只由仲裁/输出层使用，调试 UI 不能绕开仲裁直接发 HAPTIC。用户取消聊天/播报不关闭基础风险监测；STOP_STREAM 不等于设备制动，也不自动关闭仍有电的 MCU 基础风险告警。
