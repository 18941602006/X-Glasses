# Android 运行依赖候选 / Phase 6

状态：`candidate_unresolved`。2026-09-05 当前施工机无 Java/Gradle/ADB/Android SDK，公开网页检索接口未返回可审计正文，因此下列精确版本只作为保守工程候选，不声明“最新”、已下载、已解析或许可证/CVE 已完成。

| 项目 | 候选版本 |
| --- | --- |
| JDK | 17 |
| Android SDK compile/target | 35 |
| Android Gradle Plugin | 8.9.1 |
| Kotlin + Compose plugin | 2.1.20 |
| Compose BOM | 2025.04.01 |
| activity-compose | 1.10.1 |
| core-ktx | 1.16.0 |
| JUnit | 4.13.2 |
| 高德 3D 地图+定位+搜索组合包 | 10.1.300_loc6.4.9_sea9.7.4 |

首版 USB 直接使用 Android SDK `UsbManager`/`UsbDeviceConnection`，未引入 usb-serial-for-android，避免在未解析时增加第三方运行依赖。团队首次 Android Studio Sync 必须记录仓库、最终解析版本、SHA/verification metadata、许可证和失败；生成与 AGP 匹配的 Gradle wrapper 后才能作为 CLI 构建入口。

模型运行时仍全部 `NOT_INSTALLED`。LocateAnything 的 Android 算子、量化、内存和许可专项未通过；道路、手部、OCR、灯模型也未冻结移动格式。不得因 UI/状态机存在便宣称本地推理已迁移。

地图导航新增高德闭源组合 JAR 候选，Maven Central 文件 SHA256 为 `E135AE1016A463DCDCA6CED385060D52486BAA9FE9076E08181619067176B365`（本轮临时下载核验，不纳入仓库）。该哈希只是下载证据，不代表 Gradle 已解析、许可证/商业条件已放行或 APK 已构建。高德为国内主 provider；原 `LocationManager` 和 Photon/Valhalla 适配器保留。配置、官方依据、条款门与未测项见 `MAP_NAVIGATION_RUNTIME.md`。
