# X-Glasses BLACK / OV5640 — Blender结构交付

2026-10-25。用户已选第三张效果图并批准中央加厚，实物为OV5640版本；最终要求镜框改黑、连续完成。当前交付为可编辑概念结构与拆装展示，已做选定名义包络的软件核算，未做实物/制造验收。

> 当前外观修订：**XG04**。用户指出XG03与第三版AI参考差异，要求进一步贴近。新入口见 [XG04说明](REFERENCE_FIT_XG04.md)，产物 `artifacts/mechanical/xg04/`；下面XG03清单作为历史交付记录，不能把它当作用户最终认可的外观。

## 当前成果

当前脚本：`build_xg03.py`、`verify_xg03.py`、`render_details_xg03.py`。XG01和FLOW02是被用户否定/改进的历史探索，保留源文件及产物；不能把旧造型当当前定稿。原XG01说明见[历史文档](DESIGN_HISTORY_XG01.md)。

本机交付目录：`artifacts/mechanical/xg03/`，遵守项目规则被Git忽略；生成产物本机交付，复现脚本和说明进入开发分支。

| 文件 | 用途 |
| --- | --- |
| X-Glasses_BLACK_OV5640.blend | 原生可编辑模型、材质、灯光、关键帧与中文内嵌说明 |
| assembled.png | 完整黑色装配，1920×1280 |
| exploded.png | 同一模型的爆炸状态，1920×1280 |
| internal.png | 移除外壳与内盖后的硬件布局 |
| front.png | 无文字遮挡的正视造型 |
| hardware_detail.png | 相机/ToF/支架细节 |
| mainboard_detail.png | 单独揭示控制主板屏蔽罩、USB接口、触点与小元件 |
| optional_battery_packaging.png | 独立电池候选包络，不是已实施供电电路 |
| assembly_preview.mp4 | 10秒拆解与还原展示，960×640；最终生成状态见LOG |
| parts.csv | 对象ID、装配组、可选/包络标记、真实评估几何尺寸和状态 |
| fit_results.json / verification.json | 软件包络/回位检查的原始结果 |
| fit_initial_failed.json | 首次圆角内腔失败现场，修复后另存最终结果 |

动画：240帧/24fps；1–35装配停留，35–110展开，110–150展开停留，150–225还原，225–240装配停留。MP4采用每3帧输出一次、8fps，展示总时长仍为10秒。爆炸位移是便于观察的布局，非实际检修顺序、物理约束运动或铰链折叠仿真。

## 最终结构决定

黑色哑光连续眉框包住主板/OV5640和一颗前向ToF，左右渐薄镜腿安放IMU、震动驱动、两按键与走线。主机负责计算/音频，USB数据与供电。镜片、鼻托/耳套、刚性光学支架、内侧检修盖、螺钉和铰链分别建模。

共有21个基线装配组，另有第22组独立电池候选，默认隐藏。241个带ID对象含细部和6个FIT核算包络；这不是241种独立采购件。电子器件外形/小元件/引线是结构参考，不是精确原厂PCB设计。

## 尺寸与核算

尺寸单位mm，场景几何以米存储、显示为毫米。

| 对象 | 采用尺寸/预算 | 核验边界 |
| --- | --- | --- |
| 中央主控容纳区 | 约60宽×26高×25前后深 | 厚度向两侧连续过渡 |
| 眉框壁厚 | 轴向预算1.5 | 非工艺公差或强度认证 |
| 中央内腔截面 | 23高×22前后深，4次方圆角截面 | 核算保留圆角，不能只比矩形外尺寸 |
| XIAO Sense整套 | 21水平×17.8高×15前后深 | 官方名义值；购买的OV5640精确板/镜头/排线仍需量取 |
| 主控支架/间隙预算 | 22水平×18.8高×17前后深 | 独立FIT包络；具体固定点/USB插头未选定 |
| Pololu3417 | 12.7水平×17.78高×2.54前后深 | 校核每侧额外0.5间隙 |
| LSM6DSOX / Adafruit4438 | 25.6纵长×17.8高×4.6横厚 | 完整载板名义尺寸，非裸芯片 |
| DRV2605L / Adafruit2305 | 25.8纵长×17.8高×4.6横厚 | 完整载板名义尺寸，非裸芯片 |
| 镜腿前段 | 横厚起点约14.4、高约25，局部随曲率变化后向耳后收薄 | 为辅助板额外每侧0.5间隙修订，非按图片估算 |
| USB内插头余量 | 12×9.4×4.2参考包络 | 型号/插入与维修路径/线缆弯曲半径未验证 |
| 整体结构实际评估包络 | X167.147×Y161.620×Z61.775 | 不含外部USB线/插头和可选电池；含镜腿/佩戴细部 |

选定的6个名义包络均通过简化曲面内腔核算：XIAO整套、主控支架预算、ToF、IMU、震动驱动、USB插头余量。每个包络沿曲面方向取21点、另外两轴取4个角，共504个采样点。判据：圆角截面归一化分数<1。XIAO裸包络最大0.84308，支架预算0.87482，ToF含余量0.92195，IMU含余量0.77862，震动驱动含余量0.89768，USB余量0.06487。

该计算证明的是**当前简化内腔能容纳这些名义包络**。它不包含所有零件间干涉、螺柱与线材的完整公差链，也不构成实物“保证能塞入”的验收。镜腿初版在每侧0.5间隙下失败，已保留失败数据并实际增宽/增高后复测通过，没有缩小载板冒充通过。

光学检查仅验证外壳在相机/ToF中心轴上开通，不等于完整FoV无遮挡。OV5640不同AF/镜头/FPC版本、ToF隔光与串扰、标定和时间归属均待实物验证。

## 电池与供电

基线仍为USB主机供电。第22组仅是7横厚×38纵长×15高的电池候选包络，包含示意保护板、引线与接插件，放在独立隐藏集合中，没有装入当前镜腿，也没有容量/续航结论。不是采购料号、已完成电气方案或可直接并联USB供电的设计。用户本轮确认的是黑色整体造型和继续建模，不把图片里的候选电池自动升级为硬件电路定案。

## 资料来源

2026-10-25复核的官方资料：

- [Seeed XIAO ESP32-S3 Sense尺寸与相机批次说明](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)
- [OV5640相机结构图纸](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/new-res/OV5640_Camera_Module_Specification.pdf)
- [另一OV5640相机模块资料](https://files.seeedstudio.com/wiki/xiaos3-sscma/OV5640-8225N-120.pdf)；8.5×8.5×4.5仅用于相机体参考，不能用它代替整套主控尺寸，也不能据此断言用户具体AF批次一致。
- [Pololu3417完整载板规格](https://www.pololu.com/product/3417/specs)
- [Adafruit4438完整载板规格](https://www.adafruit.com/product/4438)
- [Adafruit2305完整载板规格](https://www.adafruit.com/product/2305)

官方STEP/DXF链接发现但未成功获取/导入；当前不是从官方精确CAD直接装配而成，不能称为完整器件级原厂尺寸核验。表内官方名义值和本轮设计预算明确分开。

## 打开与复现

双击.blend，或用Blender4.5.2 LTS打开。空格播放，小键盘0看相机；时间轴输入1、130、240看装配、爆炸和还原。Outliner按01–21集合展开选择对象。内置中文说明在Text Editor的`READ ME - 使用说明`中。

FIT开头对象是核算包络，渲染隐藏、视口显示线框；辅助检查时可通过Outliner显示/隐藏。第22组电池候选默认隐藏，需单独启用查看，不能误认为基线内部件。

在仓库根目录执行（Blender安装路径按本机调整）：

```powershell
& 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe' --background --factory-startup --python-exit-code 1 --python docs/hardware/mechanical/build_xg03.py -- --render
& 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe' --background artifacts/mechanical/xg03/X-Glasses_BLACK_OV5640.blend --python-exit-code 1 --python docs/hardware/mechanical/verify_xg03.py -- --movie
& 'C:/Program Files/Blender Foundation/Blender 4.5/blender.exe' --background artifacts/mechanical/xg03/X-Glasses_BLACK_OV5640.blend --python-exit-code 1 --python docs/hardware/mechanical/render_details_xg03.py
```

脚本仅用Blender自带bpy/标准库，不需下载插件/新模型。重建会重写指定生成目录；保留定制修改请另存.blend，或给build脚本传`--output`指定新目录。不要把从其他电脑复制的venv当可移植依赖。

## 尚未完成的工程验收

到货OV5640相机/板卡/排线的精确测量与厂商原CAD核对；全零件干涉与装配/检修路径；螺纹/公差/卡扣与工艺强度；铰链弯折寿命和过线；人体佩戴/鼻托压力/重量重心；光学视场、ToF串扰和标定；USB供电、马达并发、温升与汗液防护。未提供生产STL/STEP，不将可编辑Blender概念模型宣称可直接加工量产或整机安全验收。
