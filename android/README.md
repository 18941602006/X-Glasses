# X-Glasses Android

独立 Kotlin/Compose Phase 6 工程，不复用桌面 React UI。当前为可审查源码骨架，不是已构建 APK：施工机没有 JDK、Android SDK、Gradle 或 ADB，且尚未解析依赖。

## 团队首次构建

使用 Android Studio 的项目打开功能选择本目录；JDK 17、Android SDK 35、AGP/Kotlin/Compose 候选版本见 `docs/dependencies/ANDROID_RUNTIME.md`。首次 Sync 前先确认版本仍可从 Google/Maven Central 解析，生成并提交 Gradle verification metadata/依赖锁及构建日志；不要改成 `+` 或 `latest`。

建议命令（具备受信工具链后）：

```powershell
gradle --version
gradle :app:testDebugUnitTest
gradle :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

仓库没有伪造 Gradle wrapper：必须由团队受信 Gradle 生成匹配 wrapper JAR 后再提交。APK 构建成功仍不代表 USB、模型、功耗、温升或安全验收。

## 当前行为

- Manifest 只声明 USB Host，不申请网络、Android 相机或录音权限。
- 用户刷新列表并明确选择设备后才请求 USB 权限；不硬编码未冻结 VID/PID。
- 打开 bulk endpoint 后只进入 `TRANSPORT_OPEN`，XG03 握手完成前不得进入 `READY`。
- 五项模型运行时默认 `NOT_INSTALLED`，不会静默下载、上云或替换 LocateAnything。
- 取消阅读/对话等任务不关闭独立基础风险监测；拔线会取消任务并使监测不可用。
