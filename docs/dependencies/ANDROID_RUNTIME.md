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

首版 USB 直接使用 Android SDK `UsbManager`/`UsbDeviceConnection`，未引入 usb-serial-for-android，避免在未解析时增加第三方运行依赖。团队首次 Android Studio Sync 必须记录仓库、最终解析版本、SHA/verification metadata、许可证和失败；生成与 AGP 匹配的 Gradle wrapper 后才能作为 CLI 构建入口。

模型运行时仍全部 `NOT_INSTALLED`。LocateAnything 的 Android 算子、量化、内存和许可专项未通过；道路、手部、OCR、灯模型也未冻结移动格式。不得因 UI/状态机存在便宣称本地推理已迁移。

地图导航没有新增 Maven 依赖，使用 Android SDK `LocationManager`、`HttpURLConnection` 和 `org.json`。导航 provider 仅在构建时同时提供 HTTPS `XG_GEOCODER_BASE_URL` 与 `XG_ROUTER_BASE_URL` 才标记可用；开源参考、数据许可、配置和未测项见 `MAP_NAVIGATION_RUNTIME.md`。
