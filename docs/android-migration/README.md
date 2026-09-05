# Android 迁移预审

Phase 6 已创建独立 `android/` Kotlin/Compose 工程骨架。目标为骁龙 8 系列，具体手机/内存/系统尚未确认；本机无 Android 工具链，工程尚未解析或编译。

Phase 1 预审：LocateAnything 算子/量化/内存/运行时可行性，权重用途许可；USB Host CDC 授权、后台及供电；地图/音频服务边界。不得承诺已有 Android 版本或默认云端替代。

Phase 6 实测：指定机型本地推理与长时温升/功耗、USB 插拔/拒绝/重连、灭屏/后台/来电/音频焦点。Compose 五任务入口和 TalkBack 独立设计；共享帧/事件/取消与确认语义，不复用桌面 UI。

当前首批实现：五任务状态/reducer、默认模型 NOT_INSTALLED、官方 UsbManager 用户选设备/权限/双 bulk endpoint、4KiB/1s 传输上限、Compose 大触控与 TalkBack 文本。Manifest 不申请 INTERNET/CAMERA/RECORD_AUDIO，防止骨架阶段静默联网或采集。`python tools/check_android_contract.py` 只做静态合同检查，不代替 Gradle、APK 或真机。

若指定模型无法满足手机本地目标，给出可复现证据并请求用户决策；持续依赖游戏本不算迁移完成。
