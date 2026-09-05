# 测试与指标

## 2026-09-05 / Phase 6 高德国内导航源码检查点

- 已运行：pip check；foundation 124 文件；来源审核 17 项/6 报告；Android 静态合同 30 文件；Python 全仓 149 项；compileall；Ruff check/format；diff check，最终均通过。
- 失败与复测：新增破坏性回归首次 1/10 失败，原因为断言归属错误，修复后 10/10 通过；Ruff format 首次报告 2 文件，格式化后全仓 43 文件通过。
- 临时依赖核验：Maven Central 高德 10.1.300 JAR 约 33 MB，SHA256 `E135AE1016A463DCDCA6CED385060D52486BAA9FE9076E08181619067176B365`，公开 POI/路线/坐标/隐私类方法存在；不是 Gradle 解析或许可证放行。
- 已编写未运行：Kotlin 21 项，其中新增高德转向映射 2 项。本机无 JDK/Gradle/Android SDK，故不计入已运行测试。
- 未测：APK、debug/release SHA1/Key、真实 POI/步行路线、GCJ-02 偏移、GPS、断网/配额、隐私流程人工合规、TalkBack、TTS/震动仲裁、后台、功耗/温升和实机安全指标。

## 2026-09-05 / Phase 6 地图导航第一检查点

- 已运行：`tools.check_foundation`（124 必需文件）、`tools.check_android_contract`（27 Android 文件）、Python 全仓 148 项、Ruff check/format、compileall、git diff check，均通过。
- 已编写未运行：Android/Kotlin 共 19 项源码测试，其中地图导航 6 项、任务完成 1 项；施工机没有 Android/JVM 工具链。
- 未测：Gradle 解析、APK、真实 Photon/Valhalla、GPS 精度、偏航阈值、目标地区路线质量、TalkBack、TTS/震动仲裁、后台/断网、功耗/温升和实机安全指标。

## Phase 6 Android 第一软件检查点 / 2026-09-05

新增 6 项 Python 静态合同回归，全仓 145 项通过；Android checker 校验 17 个工程文件、五任务、模型安全默认、USB Host/权限/拔线/上限、TRANSPORT_OPEN 与 READY 分离、XG03 常量、禁止过街/旧功能/网络 URL/浮动依赖。122 文件、来源、compileall、Ruff 全仓和 diff 检查通过。

Kotlin 源码另含 4 项 reducer 测试和 3 项协议黄金/分割/损坏测试，但因本机无 JDK/SDK/Gradle而未执行，不能计入 145 项。没有 Gradle 解析、APK、Android instrumentation、USB/手机/模型/性能/功耗/温升或 TalkBack 实测。

第二检查点：Android 静态范围增至 20 文件、破坏性回归增至 7 项、全仓 146 项通过；Kotlin 待运行源码测试增至 12 项。新增 nonce/能力/boot/握手与心跳超时/序号回绕，以及 repeat 语义。上述仍未经过 Kotlin 编译，不能把源码数量计作执行成功。

## Phase 5 辅助功能与输出仲裁 / 2026-09-05

新增 23 项标准库 synthetic/fake 测试，全仓 139 项通过。覆盖信号灯方向/状态且禁止过街许可、OCR 原文顺序/上限、地图与对话 provenance、worker JPEG/问题/超时/失败关闭、固定安全优先级、过期/未来/错会话、同类替换、取消/清会话/限频、感知与拿取映射、长文本分块门，以及输出期限/幂等/失败回执。

117 必需文件、17 固定来源/6 报告、compileall、Ruff 全仓 check/format 和 diff 检查通过。transport 全是 fake；没有模型准确率、地图定位误差、网络恢复、TTS 时延、震动 ACK 或实际过街测试，且不以合成 green 样例形成任何安全结论。

## Phase 4 Locate/拿取软件核心 / 2026-09-05

新增 9 项 synthetic 测试，Python 全量 116 项通过、1 项可选 pyserial 测试跳过；基础结构 110 项通过，compileall 通过。覆盖 Locate worker 的 JPEG/查询/数量/字段/session/frame/model 上限，手/物/ToF 的身份、标定、时间、质量、遮挡、同区和无效距离降级，以及二维重叠后一次性 button/voice 显式确认。

首测暴露 ToF 网格边界双重归属，改为左闭右开并调整夹具后通过。系统 Python 没有 Ruff，改用仓库固定 `.venv` Ruff 0.12.12，修复 1 处导入排序并格式化 2 个文件后 check/format 通过。未安装模型或运行 worker，也没有真实手部/物体、标定、成功率、时延或误确认数据。

## Phase 3 分割 worker 合同 / 2026-09-05

新增 6 项隔离 worker 测试，Python 全量预期 107 项。覆盖可信主机元数据保留、JPEG/timeout 上限、超时、session/frame/model 回显、额外字段、二值 RLE 精确像素与上限、非有限质量。transport 为 fake，没有启动 Paddle 或加载权重，不能形成模型准确率/速度结论。

## Phase 3 融合核心 / 2026-09-05

新增 9 项 synthetic 道路掩码/ToF 融合测试，Python 全量预期 101 项。覆盖前进候选、中心非紧急障碍侧向选择、中心紧急障碍停止、全局/中央局部 ToF 未知、无候选区、session/标定/质量、源过期/接收未来/采样未来/不同步和合同非法值。没有真实图像、模型权重或硬件，因此不产生漏报率、误报率、FPS 或安全结论。

## Phase 2B 本地 API 与前端 / 2026-09-05

Python 全量 92 项（原 86 + localhost API 6）通过；前端 3 项交互测试通过，另有 TypeScript 无输出检查、Vite 生产构建、精确依赖树和官方 registry 生产依赖 audit。构建产物约 199.09kB JS（gzip 63.14kB）、7.51kB CSS（gzip 2.53kB）。96 个必需文件和当前运行范围检查通过。

交互覆盖离线/未知不伪造值、无能力按钮禁用、提交只宣告 pending、rejected 与 replay 明示；API 覆盖回环绑定/Host guard、严格 JSON/动作、无 dispatcher、状态拷贝、日志/命令上限和终态单次转换。用户决定跳过浏览器截图/人工视觉验收，因此响应式布局、颜色与真实屏幕阅读器仍标未人工验收；自动测试不替代这些项目。

## Phase 2A 固件协议基线 / 2026-09-05

新增 7 项固件合同测试，连同主机 capability 拒绝回归后全量共 86 项，约 1.8 秒通过。静态检查核对必要固件文件、ESP-IDF/组件精确版本、Python/C 协议常量、默认仅 CLOCK 能力及禁用功能边界；基础检查现为 76 个必需文件。Ruff、来源台账、pip 和差异检查同时通过。

本机 ESP-IDF 安装与交叉编译按用户决定跳过，转由已有环境的团队成员执行。因此编译、USB 枚举、摄像头、ToF、IMU、震动、电源和时序均为未验收；静态合同不得代替团队构建日志或真机测试。

2026-09-05 第二部分更新：78 项（26 工具+31 协议回放+19 控制传感器时钟+2 串口），其中串口为本地内存回环，未安装可选依赖则该测试显式 skip。64 必需文件，9 个当前运行文件白名单。没有真实 USB/FPS/P95/电流数据；时钟漂移200ppm、RTT100ms、TTL500ms均为待实测预算。完整结果见 LOG 最新条目。

状态：以下是验收方法，不是实测结果。每条实测记录须有日期、commit、硬件/系统/模型版本、参数、数据来源（模拟/回放/实机）、样本数、成功失败/耗时和复测结果；未测写“未测”，不得用 0 填充。

## Phase 0

在项目 .venv 中执行：

- python -m pip check
- python -m ruff check .
- python -m ruff format --check .
- python tools/check_foundation.py
- python -m unittest discover -s tests -v
- git diff --check 及暂存后的 git diff --cached --check

基础检查验证必需文件、配置空值、基础依赖锁定、目录限制与 Git 忽略规则；单测只测该工具，不代表 USB/模型/业务测试。Phase 0 无硬件/算法性能指标。

## 后续验收设计

Phase 1 增加 python tools/check_source_audit.py：检查 17 条来源的精确引用、根许可证据、未验证标记、用户明确的有限模型测试范围与报告存在性；unittest 新增 12 项，总计 25 项。仍需人工对照官方原文和文档链接，不认证许可适用、不执行漏洞扫描，不代替实际安装锁/编译/模型/硬件验证。

| 测试对象 | 度量与异常场景 | 阶段 |
| --- | --- | --- |
| USB | 有效字节/秒、最坏 JPEG 长、丢帧/坏包/短读写、命令确认时延；持续 30 分钟、拔插/断电 | 2A |
| 时间与 UI | 采样时间偏差、端到端 P50/P95（统一时钟后）、帧龄/过期提示次数、命令失败反馈 | 2A/2B |
| ToF/行进 | 有效分区/总分区、漏报/误报计数及分母、距离误差；日光/暗处/反光/头动/未知 | 3 |
| 拿取 | 首次定位时延、漂移、错误深度归属、任务成功/错误确认；多物/无物/遮挡/晚到结果 | 4 |
| 辅助 | OCR 字符错误率/顺序，灯状态混淆/未知，对话/地图断网、取消和风险抢占 | 5 |
| Android | 指定机型 USB/供电/后台/来电、内存/温升/功耗、长时延迟和本地推理 | 6 |

640×480 JPEG 约 10fps、ToF 8×8 约 15Hz、IMU 50–100Hz 仅起步预算。安全相关延迟/阈值和允许误差必须依据场景与基线，在对应阶段测试前冻结，不事后调整掩盖失败。不能仅用平均 FPS 宣称行进安全。

测试受控、有陪同、保留盲杖；不安排独立道路或过街验证。纯模拟不能替代实机、电流/温升和真实传感器失效验证。

## Phase 2A 第一部分 / 2026-09-05

新增标准库协议/输入/流接口/回放测试 31 项，加原有 25 项及基础白名单边界 1 项，合计 57 项。环境 Python 3.12.14 / Ruff 0.12.12，无新增安装依赖。模拟覆盖全部单包分割点、确定性随机分块、头/负载 CRC 与非法元数据、部分包超时、最大 256KiB 组帧、乱序/重复/会话切换/断连、短读写/截止、录制损坏/截断/上限/来源及虚拟 tick 过期。数据为人工标记字节，不是相机图像或硬件采样。

完整执行命令仍为本文件 Phase 0 检查组，加来源检查和 python -m tools.replay_usb --demo。基础结构现为 53 必需文件及显式 4 个运行文件白名单。demo 仅恢复 1 个 6 字节标记帧；不得计算或宣称实机 FPS/P95/供电。握手、源时间映射、传感器语义、ACK、真实 CDC/固件/30 分钟链路都未验收。失败/最终复测见 LOG。
