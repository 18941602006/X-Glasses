# Phase 6 / Android

## 2026-09-05 / 地图步行导航开工计划

在现有 USB 控制会话后补齐手机地图任务：目的地文字搜索、候选确认、步行路线、前台位置更新、逐步指令、到达、偏航重算与取消。采用可替换 provider，不把 MapLibre 渲染器与路线引擎绑定；首个检查点不下载离线地图、不硬编码公共服务或密钥。

前端新增导航专页而不是把调试字段堆到五任务首页；TalkBack 可读目的地候选、当前位置质量、剩余距离和下一指令。GPS 低精度/过期、网络失败、路线为空均进入未知/暂停，不输出虚假继续前进。地图提示继续低于本地风险提示，并明确不构成道路安全或过街许可。

## 2026-09-05 / 地图导航第一软件检查点

已实现 provider 解耦的目的地搜索与步行路线、Android 前台位置源、保守步进/到达/偏航重算引擎、任务生命周期和无障碍导航页。当前 adapter 兼容 Photon GeoJSON 与 Valhalla pedestrian/polyline6；URL 仅由 Gradle 属性配置，只接受 HTTPS，未硬编码 demo 或密钥。Manifest 新增网络及前台粗略/精确位置，明确拒绝后台位置。

静态/全仓验证通过，Kotlin 测试源码 19 项仍待团队 Gradle 执行。真实地区服务、WGS84/GCJ-02、OSM 覆盖和数据许可、GPS/TalkBack、TTS/震动统一仲裁、路线图渲染及离线地图均未验收。地图页面可用不等于设备导航安全完成。

## 2026-09-05 / 恢复开工计划

基线 a3e2e315d5f821256fdcbb908e9323ee84fc3fb3。创建备份后新增独立 `android/` 工程，首批完成原生 USB Host 会话、纯 Kotlin 任务状态机和 Compose 五入口无障碍界面；不复用桌面 React UI。用户取消电脑摄像头测试，Phase 6 现恢复。

本机无 JDK/SDK/Gradle/ADB，故只做源码/清单/结构和可在现有 Python 工具内验证的合同检查。固定依赖先标未解析候选，APK、USB 授权、后台、来电/音频焦点、温升/功耗/内存/延迟以及骁龙 8 本地模型均留待团队真机；任何未测项不得写为完成。

## 2026-09-05 / 第一软件检查点

已创建独立 Kotlin/Compose 工程、五任务状态/reducer、大触控/TalkBack 文本、UsbManager 用户选设备/权限/拔线清理/双 bulk endpoint、4KiB/1s 传输上限，以及 XG03/CRC/长度/超时增量 codec 源码和 Kotlin 黄金向量测试。Manifest 不申请网络、Android 相机或录音权限；模型全部默认 NOT_INSTALLED。

主动修正端点打开即 READY 的错误语义：当前只进入 TRANSPORT_OPEN，XG03 握手前基础风险监测保持未运行，任务不能启动。Python 静态检查覆盖 17 个 Android 文件并有 6 项破坏性回归；全仓 145 项测试通过，122 文件/来源/compileall/Ruff/diff 通过。

状态：第一软件检查点完成，Phase 6 未完成。本机没有执行 Gradle/Kotlin 编译，Kotlin 单测只是待团队运行的源码；没有 APK、USB 真机、握手、后台服务、模型、TalkBack 实测或骁龙性能数据。

## 2026-09-05 / 阶段登记

状态：第一软件检查点完成；构建、协议会话、模型和真机验收未完成。

## 2026-09-05 / 第二软件检查点

第一检查点 A = a3fc152384cd20a453fd19256468ac039d128de2 已推送核验。新增 ControlSession 与 AndroidHostLink：随机非零 session/nonce、HELLO/WELCOME、2s 握手、1.5s 心跳、boot/能力/序号回绕门、4KiB 短写循环和读线程；READY 只能由控制状态机产生。要求 CLOCK+TOF+CAMERA，当前仅 CLOCK 的固件不会通过。

修复 HELLO 同步写失败后被外层 TRANSPORT_OPEN 覆盖的竞态；补充重复上一条提示动作与无障碍大按钮。Android 静态合同 20 文件/7 项破坏性回归，全仓 146 项通过；当时 Kotlin 12 项测试源码仍未执行。下一步必须在团队 Android 环境解析/编译，并使用具体手机、固件和模型继续，静态施工不能替代。

后续范围与验收：USB Host + Kotlin/Compose 无障碍 + 本地模型。具体手机、功耗/温升/后台/音频实测及 LocateAnything 迁移专项；失败须请求路线决策，不默认上云或换模型。

开工时补充当前分支/基线、拟改文件、测试命令、成功远端备份和回滚方案后再施工；不得将此登记当作已完成。
## 2026-09-05 / 高德国内导航适配计划

新增高德 POI/步行路线 provider，并在 coordinator 边界统一坐标系；系统 LocationManager 原始位置保持为 WGS84，高德会话将其转换为 GCJ-02 后搜索、规划与偏航判断。高德 SDK 只在用户明确同意隐私条款后初始化，拒绝时导航不可用但 USB 与其他本地任务不受影响。

前端增加“高德地图服务”、未配置 Key、待授权/已启用状态和同意/拒绝操作，移除固定 OpenStreetMap 署名。Android Key 通过未跟踪的本机 Gradle 属性注入并绑定 applicationId/SHA1；不在代码、示例或日志写入真实凭据。开放 Photon/Valhalla provider 保留作可替换测试后备，不作为国内默认完成声明。

本检查点只宣称源码适配；高德依赖解析、debug/release SHA1、控制台 Key、真机定位与路线质量、隐私合规文案、弱网/后台及 TalkBack 必须在团队 Android 环境实测。

## 2026-09-05 / 高德国内导航源码检查点结果

已完成 `AmapNavigationProvider`、`AmapPrivacyConsent`、provider 延迟配置和前端授权/撤回流程；坐标归一化发生在 coordinator 接收每个系统 fix 后，路线、目的地和偏航比较保持 GCJ-02。Key 使用 Manifest 占位符与本机 Gradle 属性，仓库无真实值。高德固定候选包已做临时文件存在、哈希和公开 API 名核验，未纳入仓库。

本机静态/全仓验证通过，第一次新增回归因断言插入了错误测试方法而失败，调整测试结构后复测通过；官方示例固定版本下载 404 后改用 Central 可用的 10.1.300 并记录差异。真实 Android 编译及手机验收仍为硬门槛，不把源码检查点写成地图功能已实机完成。

高德源码交付 A = `bfbd865b7300adb95b6c9aa21fe0af709feeb9aa`，已推送开发分支并核验。Phase 6 继续处于“源码检查点完成、团队 Android/真机验收未完成”。
