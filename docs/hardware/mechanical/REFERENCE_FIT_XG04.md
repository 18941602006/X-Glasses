# XG04 黑色参考图贴合修订

2026-10-25。基于用户认可的第三版AI图及容量修订图，修正XG03的等厚横梁感、偏圆且低的镜片、突出的金属铰链和过宽光学饰面。此版为实际Blender模型，不是AI修饰照片；外观相似度由用户判断，不预称视觉验收完成。

## 本轮改动

- 中央保留26高×25前后深，横向±28mm区间维持完整截面；向两侧收薄，末端平顺回接铰链。原来的60mm完整等截面表述改为56mm；整个眉框宽度不变。
- 镜片上沿跟随眉框下缘，底部为圆角方形弧线，降低镜片悬挂和脱节感。
- 取消前脸横向银色装饰线，铰链同黑，光学饰面从51缩至40mm宽，保留相机和单颗ToF开口。
- 使用较低的产品展示视角，保持硬件、USB有线方案及21组拆装关键帧。

## 文件与复现

产物位于 `artifacts/mechanical/xg04/`：原生 `X-Glasses_BLACK_OV5640.blend`、assembled/exploded/internal/front/hardware_detail.png、parts.csv、fit_results.json、verification.json。240个带ID对象包含6个包络；21个基线组和1个独立电池候选。空格播放240帧，1/240为装配，130为拆解；没有新导出视频，XG03视频仅展示旧轮廓。

使用Blender4.5执行 `--background --python docs/hardware/mechanical/build_xg04.py -- --render`；再打开生成的blend，运行 `--python docs/hardware/mechanical/verify_xg04.py`。

## 验证与限制

沿用并重新核算6个名义硬件包络和关键帧回位；具体结果见verification.json。主控21×17.8×15mm、ToF选定载板及辅助板预算保留。首轮渲染发现外侧镜片上沿空隙，已调整上沿贴合，首轮图保留为iteration1-gap.png。

这不是制造发布：具体到货OV5640、线缆弯曲、所有零件干涉、公差、完整光学视场、热、铰链折叠和人体适配均待实测。参考图三个圆形光学窗不强行照搬，当前真实配置为一个相机和一颗ToF。电池仍为独立候选，基线USB供电。主控空间导致中央眉框仍比原始薄框概念厚，不能假称完全复刻。
