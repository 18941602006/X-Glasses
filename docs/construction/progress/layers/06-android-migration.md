# Phase 6 / Android

## 2026-09-05 / 恢复开工计划

基线 a3e2e315d5f821256fdcbb908e9323ee84fc3fb3。创建备份后新增独立 `android/` 工程，首批完成原生 USB Host 会话、纯 Kotlin 任务状态机和 Compose 五入口无障碍界面；不复用桌面 React UI。用户取消电脑摄像头测试，Phase 6 现恢复。

本机无 JDK/SDK/Gradle/ADB，故只做源码/清单/结构和可在现有 Python 工具内验证的合同检查。固定依赖先标未解析候选，APK、USB 授权、后台、来电/音频焦点、温升/功耗/内存/延迟以及骁龙 8 本地模型均留待团队真机；任何未测项不得写为完成。

## 2026-09-05 / 第一软件检查点

已创建独立 Kotlin/Compose 工程、五任务状态/reducer、大触控/TalkBack 文本、UsbManager 用户选设备/权限/拔线清理/双 bulk endpoint、4KiB/1s 传输上限，以及 XG03/CRC/长度/超时增量 codec 源码和 Kotlin 黄金向量测试。Manifest 不申请网络、Android 相机或录音权限；模型全部默认 NOT_INSTALLED。

主动修正端点打开即 READY 的错误语义：当前只进入 TRANSPORT_OPEN，XG03 握手前基础风险监测保持未运行，任务不能启动。Python 静态检查覆盖 17 个 Android 文件并有 6 项破坏性回归；全仓 145 项测试通过，122 文件/来源/compileall/Ruff/diff 通过。

状态：第一软件检查点完成，Phase 6 未完成。本机没有执行 Gradle/Kotlin 编译，Kotlin 单测只是待团队运行的源码；没有 APK、USB 真机、握手、后台服务、模型、TalkBack 实测或骁龙性能数据。

## 2026-09-05 / 阶段登记

状态：第一软件检查点完成；构建、协议会话、模型和真机验收未完成。

后续范围与验收：USB Host + Kotlin/Compose 无障碍 + 本地模型。具体手机、功耗/温升/后台/音频实测及 LocateAnything 迁移专项；失败须请求路线决策，不默认上云或换模型。

开工时补充当前分支/基线、拟改文件、测试命令、成功远端备份和回滚方案后再施工；不得将此登记当作已完成。
