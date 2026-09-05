# X-Glasses Android

独立 Kotlin/Compose Phase 6 工程，不复用桌面 React UI。当前为可审查源码骨架，不是已构建 APK：施工机没有 JDK、Android SDK、Gradle 或 ADB，且尚未解析依赖。

## 高德国内地图配置

1. 在高德开放平台创建 Android Key，包名填写 `com.trollhunter.xglasses`，分别登记团队实际 debug 与 release 签名 SHA1。不要使用 Web 服务 Key。
2. 仅在开发机用户级 `%USERPROFILE%\.gradle\gradle.properties` 写入 `AMAP_ANDROID_KEY=你的AndroidKey`。不要提交 `local.properties`、密钥、签名文件或包含密钥的构建日志，也不要把 Key 作为命令行参数留在历史中。
3. App 首次打开导航页时显示高德隐私说明；只有用户明确同意后才初始化搜索、路线与坐标转换接口。拒绝时地图导航关闭，USB 和其他任务继续可用。
4. 发布或受控测试前，团队必须把高德处理的数据类型、用途及其隐私政策纳入 App 正式隐私政策并完成合规复核；当前界面说明不是法律验收结论。

依赖固定为 `com.amap.api:3dmap-location-search:10.1.300_loc6.4.9_sea9.7.4`，只打包 `arm64-v8a`/`armeabi-v7a`，适配目标骁龙手机。施工机已核对 Maven Central 文件存在和公开 API 类，但未执行 Gradle 解析。

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

- Manifest 声明 USB Host、网络和前台粗略/精确位置；不申请后台位置、Android 相机或录音权限。
- 用户刷新列表并明确选择设备后才请求 USB 权限；不硬编码未冻结 VID/PID。
- 打开 bulk endpoint 后只进入 `TRANSPORT_OPEN`，XG03 握手完成前不得进入 `READY`。
- 五项模型运行时默认 `NOT_INSTALLED`，不会静默下载、上云或替换 LocateAnything。
- 取消阅读/对话等任务不关闭独立基础风险监测；拔线会取消任务并使监测不可用。
- 行进导航页以高德作为国内主服务，支持地点搜索、候选确认、步行路线、系统 GPS 坐标转换、到达附近和偏航重算；Key 未配置或隐私未同意时保持不可用。

地图配置、官方依据与开放后备参考见 `../docs/dependencies/MAP_NAVIGATION_RUNTIME.md`。旧 `XG_GEOCODER_BASE_URL`/`XG_ROUTER_BASE_URL` 仍只用于 Photon/Valhalla 测试后备；国内默认使用本机 `AMAP_ANDROID_KEY`。当前页面依靠 TalkBack live region 提示，尚未完成统一 TTS/震动仲裁或真机验收。
