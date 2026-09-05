# 地图步行导航运行时 / Phase 6

状态：Android 源码检查点已实现，服务与真机未验收。代码不包含默认公共服务 URL、API 密钥、瓦片或离线地图数据；未配置时导航运行时明确不可用。

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

OpenStreetMap 数据受 ODbL 和署名要求约束；导航页显示 `© OpenStreetMap 贡献者，ODbL`。若换用国内地图服务，必须按服务条款替换数据归属、坐标系与隐私说明，不能混用 GCJ-02/WGS84 后仍声称路线准确。

## 当前实现

- `NavigationEngine`：定位新鲜度/精度门、逐步指令、到达附近、连续三次偏航后重算；没有 `safe/go/cross` 语义。
- `OpenNavigationProvider`：Photon 兼容地点搜索、Valhalla pedestrian 路线；只接受 HTTPS，5/8 秒超时、1 MiB 响应上限、最多 5 个地点和 20,000 个路线点。
- `AndroidLocationSource`：只在前台使用系统 GPS/网络定位，不申请后台定位权限。
- `NavigationCoordinator`：单线程网络请求、路线状态、偏航重算和任务完成/失败回写。
- Compose 导航页：目的地搜索、候选确认、开始/结束、剩余距离、下一指令及 TalkBack live region。

## 构建配置

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

- Gradle/Kotlin 编译、真实 Photon/Valhalla 响应兼容、中文地址质量和偏航阈值。
- 中国大陆 OSM 覆盖、坐标系、路线合法性、无障碍道路属性及隧道/高楼定位。
- TalkBack 真机播报节奏、TTS/震动统一仲裁、前后台、功耗和断网缓存。
- MapLibre 可视地图、离线地图下载和增量更新；这些不是当前盲人主流程的必要条件。
