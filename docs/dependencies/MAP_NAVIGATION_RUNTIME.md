# 地图步行导航运行时 / Phase 6

状态：高德国内 provider 源码检查点已实现，Gradle/APK/服务与真机未验收。代码不包含真实 API Key、瓦片或离线地图数据；未配置或用户未同意隐私条款时导航明确不可用。

## 国内主方案：高德 Android SDK

- 固定候选 `com.amap.api:3dmap-location-search:10.1.300_loc6.4.9_sea9.7.4`。Maven Central 已确认 2025-05-26 发布的约 33 MB JAR 存在；本轮临时核验 SHA256 为 `E135AE1016A463DCDCA6CED385060D52486BAA9FE9076E08181619067176B365`。官方文档给出的 `10.1.200...` 示例在本轮直接请求 Central 时返回 404，因此没有采用不可解析示例版本。
- 高德官方文档要求 Android Key 绑定 release/debug SHA1 和包名。本项目包名为 `com.trollhunter.xglasses`，Key 仅放开发机用户级 Gradle 属性 `AMAP_ANDROID_KEY`，Manifest 使用占位符；不得提交、截图或粘贴真实 Key。
- `AmapNavigationProvider` 使用 `PoiSearch` 获取最多 5 个地点、使用 `RouteSearch.WalkRouteQuery` 获取步行路线；回调等待分别限制 8/10 秒，1000 以外错误码失败关闭。
- Android 系统定位视为 WGS84；每个 fix 在进入导航引擎前通过 `CoordinateConverter.CoordType.GPS` 转 GCJ-02。目的地与路线均保持高德坐标，禁止与 WGS84 路线几何直接比较。
- `MapsInitializer` 与 `ServiceSettings` 合规状态在构造坐标转换、POI 或路线对象前更新；只有用户明确同意或已保存同意时才创建 provider。拒绝不会关闭 USB/感知任务。
- 高德 SDK/数据/服务不是本项目开源代码，受高德服务协议、隐私与可能的配额/商业条件约束；上线前必须由团队核对当前条款、技术服务许可和 App 正式隐私政策。本源码检查不构成法律放行。

## GitHub 参考与采用边界

| 项目 | 许可/用途 | 本项目决定 |
| --- | --- | --- |
| [MapLibre Navigation Android](https://github.com/maplibre/maplibre-navigation-android) | MIT；无遥测的导航逻辑，可接自有 Directions | 参考 turn-by-turn 分层，不复制源码；待 Android 工具链解析后再决定是否引入库 |
| [MapLibre Native](https://github.com/maplibre/maplibre-native) | BSD-2-Clause；Android 矢量地图渲染 | 仅作为后续可视地图候选；盲人主流程不以地图画面为前置 |
| [Valhalla](https://github.com/valhalla/valhalla) | MIT；支持 pedestrian 路线 | 当前 `OpenNavigationProvider` 的路线 JSON 合同目标，可连接团队自托管或合规托管实例 |
| [GraphHopper](https://github.com/graphhopper/graphhopper) | Apache-2.0；OSM 路线引擎 | 可替换路线 provider；当前未实现其专用响应适配 |
| [Organic Maps](https://github.com/organicmaps/organicmaps) | 代码 Apache-2.0，二进制地图数据另有许可 | 适合作为离线导航行为参考；完整 App/C++ 栈过重，不直接嵌入首版 |
| [Photon](https://github.com/komoot/photon) | Apache-2.0；OSM 地点搜索 | 当前搜索 JSON 合同目标；公共 demo 无 SLA，量产前自托管或签约托管 |
| [Pelias](https://github.com/pelias/pelias) | MIT；模块化地理编码 | 可替换地点搜索服务；当前未实现其专用响应适配 |

Photon/Valhalla 后备使用 OpenStreetMap 数据时仍受 ODbL 和署名要求约束；只有实际启用该 provider 时才应显示对应归属。高德模式显示高德来源，不混用两套数据归属或坐标系。

## 当前实现

- `NavigationEngine`：定位新鲜度/精度门、逐步指令、到达附近、连续三次偏航后重算；没有 `safe/go/cross` 语义。
- `AmapNavigationProvider`：国内默认候选，高德 POI、步行路线和 WGS84→GCJ-02 转换。
- `AmapPrivacyConsent`：保存用户选择并在任何高德对象构造前同步地图/搜索隐私状态。
- `OpenNavigationProvider`：Photon 兼容地点搜索、Valhalla pedestrian 路线；只接受 HTTPS，作为测试后备。
- `AndroidLocationSource`：只在前台使用系统 GPS/网络定位，不申请后台定位权限。
- `NavigationCoordinator`：单线程网络请求、路线状态、偏航重算和任务完成/失败回写。
- Compose 导航页：目的地搜索、候选确认、开始/结束、剩余距离、下一指令及 TalkBack live region。

## 构建配置

开发机用户级 `%USERPROFILE%\.gradle\gradle.properties`：

```properties
AMAP_ANDROID_KEY=仅填写团队自己的AndroidKey
```

不要把 Key 作为 `-P` 参数写入命令历史。高德控制台同时配置 debug/release SHA1 与包名；签名切换后重新核对，否则可能返回 `INVALID_USER_SCODE`。旧开放后备仍可用以下非密钥 URL 属性，但不作为国内默认：

以下是服务地址，不是密钥；它们会写入 APK 的 BuildConfig，因此不得把私密 token 放入其中：

```powershell
gradle :app:testDebugUnitTest `
  -PXG_GEOCODER_BASE_URL=https://your-photon.example `
  -PXG_ROUTER_BASE_URL=https://your-valhalla.example

gradle :app:assembleDebug `
  -PXG_GEOCODER_BASE_URL=https://your-photon.example `
  -PXG_ROUTER_BASE_URL=https://your-valhalla.example
```

不传参数时运行时保持 `NOT_INSTALLED`，页面仍可打开并明确提示团队配置服务。公网 demo 只可在遵守对方使用政策的人工开发测试中短时使用，不能当作项目生产后端。

## 尚未验证

- 高德 Gradle 解析、Kotlin 编译、debug/release Key、真实 POI/步行路线响应、错误码、坐标偏移与偏航阈值。
- 高德当前服务条款、配额/计费、技术服务许可、正式隐私政策和用户撤回同意流程。
- 中国大陆路线合法性、无障碍道路属性及隧道/高楼定位；地图路线本身不证明现场可安全行走。
- TalkBack 真机播报节奏、TTS/震动统一仲裁、前后台、功耗和断网缓存。
- MapLibre 可视地图、离线地图下载和增量更新；这些不是当前盲人主流程的必要条件。
