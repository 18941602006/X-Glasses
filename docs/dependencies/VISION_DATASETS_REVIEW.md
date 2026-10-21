# 视觉公开标注数据与训练策略

核查日期：2026-10-21。状态：资料调研，不是训练、数据下载、许可授权或模型验收。用户接受电脑样机方案，要求优先复用现有标注数据；高德和手机本地迁移继续暂缓。

## 结论与优先级

数据集是图像及标签；预训练模型是已经训练出的权重。优先验证现成模型，出现稳定、可复现的场景缺陷后才考虑微调，不从零训练所有功能。国内行人信号灯、眼镜视角道路是优先评测项；LocateAnything、手部和OCR先测现成权重。公开可下载不等于代码/数据/权重同许可证，更不等于可商用。

## 候选与证据

| 优先级/任务 | 官方入口及已核对内容 | 用于本项目的方式与缺口 | 许可/获取状态 |
| --- | --- | --- | --- |
| P1 道路分割 | [Segments sidewalk-semantic](https://huggingface.co/datasets/segments/sidewalk-semantic)：比利时人行道图像、像素级类别，含人行道、路缘、台阶、车辆和行人 | 优先作为步行场景候选数据；比车辆视角更贴近任务，但仍需本地眼镜视角验证，不是安全可走真值 | 卡片标CC BY-NC 4.0，文件受门控，需本人登录接受条件；本轮未申请/下载 |
| P2 道路分割 | [Cityscapes概览](https://www.cityscapes-dataset.com/dataset-overview/)与[条款](https://www.cityscapes-dataset.com/license/) | 与既有PP-LiteSeg候选衔接；车载视角和欧洲街景不能直接代表国内步行视角 | 非商业用途及注册条件；数据不得重分发；衍生模型也不能默认商用。当前条款还列科学机构/用途注册要求，与页末个人实验描述须一并核对，不默认当前团队能获批 |
| P1 行人灯检测 | [DTLD官方](https://www.uni-ulm.de/en/in/institute-of-measurement-control-and-microtechnology/research/data-sets/driveu-traffic-light-dataset/)：23万以上灯实例，边框、状态、图案、朝向、相关性及track ID；包含行人灯 | 先按行人图案、正向和有效状态筛选，再检查样本；德国车载采集，不能覆盖国内灯型/倒计时/眼镜角度 | [登记条款](https://www.uni-ulm.de/en/in/institute-of-measurement-control-and-microtechnology/research/data-sets/driveu-traffic-light-dataset/registration-form-dtld/)仅自身研究/教学，禁止商业用途及向第三方披露数据；非商业个人测试不自动等于满足研究用途。申请需真实资料，本轮未提交 |
| P2 国内灯补充 | [清华-Tencent信号灯](https://cg.cs.tsinghua.edu.cn/traffic-light/)：超过1.5万灯实例，JSON边框；6类中有Red pedestrian | 可补国内红色行人灯及车灯混淆样本；没有单列绿色行人灯，不能拿它单独训练完整行人红绿识别 | 有训练集下载入口，页面未见明确数据授权条款；只列候选，下载/训练前补证据 |
| P2 行人灯状态 | [ImVisible/PTL](https://github.com/samuelyu2002/ImVisible)：5059图，红/绿/绿倒计时/空白倒计时/无灯；提供LytNet代码和训练后权重 | 可参考状态分类；CSV中的4个坐标是斑马线中线起止点，不是灯框。仅考虑状态标签，若做灯检测需补灯框，不能照搬原整套过街模型 | [仓库MIT](https://github.com/samuelyu2002/ImVisible/blob/master/LICENSE)措辞针对软件及文档；外链图像授权需另核，不直接推定MIT覆盖全部原图 |
| P3 手物交互 | [100DOH官方实现](https://github.com/ddshan/hand_object_detector)及[数据入口](https://fouheylab.eecs.umich.edu/~dandans/projects/100DOH/download.html)：手/物检测与接触状态研究数据、训练后检测权重 | 可用于手物接触困难样本评测或后续小模型微调；不替换LocateAnything指定物体识别，不证明拿牢/不提供本机ToF标定 | 数据主页访问超时，下载页搜索可见；数据许可仍待核，不下载；原Faster-RCNN环境较旧，不直接塞入当前模型环境 |
| P3 中文OCR | [PaddleOCR官方公开数据目录](https://paddlepaddle.github.io/PaddleOCR/v2.10.0/en/datasets/ocr_datasets.html)及[FAQ](https://paddlepaddle.github.io/PaddleOCR/v3.1.0/en/FAQ.html)：包括LSVT中文街景训练来源及转换资料 | 先使用中文OCR预训练模型；只有目标场景小字、反光、倾斜等稳定错误才筛选同类数据微调，不训练DeepSeek API | 官方目录不是第三方图像授权；LSVT等各自条款/实际下载入口需另审，当前仅候选 |

## 已训练模型补充候选

[tobiasc/segformer-b0-finetuned-segments-sidewalk](https://huggingface.co/tobiasc/segformer-b0-finetuned-segments-sidewalk)明确说明已在sidewalk-semantic微调，约3.72M参数，可以作为PP-LiteSeg的电脑对照候选；本次页面未见独立明确权重许可证，未下载，也不擅自替换现行候选。先补训练来源/权重许可、固定revision与SHA256、图像预处理/类别映射，再与现行模型在同一回放集比较。不能依据网页示例宣称已适配Android或满足实时性。

## 数据进入工程后的规则

1. 按来源保留许可、版本、URL、校验和及原标签；不同许可数据不直接合包发布。数据/权重仍放忽略目录，不上传GitHub，不上传API密钥。
2. 道路只映射候选人行区域、障碍和未知。原数据含crosswalk类别不意味着恢复专项功能：在本项目训练/评测映射中设ignore，不能映射为可走，也不新增盲道/斑马线输出、页面、定位或对齐任务。
3. 灯按检测与状态分开：边框+行人灯类别+红/绿/灭/未知、朝向、遮挡。国内数据缺绿色行人灯、倒计时或相关方向时补采/补标；多个灯无法确认归属时保持未知。图像级标签不能当所有灯的边框标签。
4. 先建立独立测试集，再调整模型。按地点、路口、录制序列/视频分组划分，近邻帧不得随机分到训练和测试；留国内目标场景测试集，包含夜间、逆光、雨天、模糊、遮挡及无目标负样本。公开数据成绩不代替本机/眼镜实测。
5. 第一轮建议从数百张有代表性的授权图片/片段做误差分析起步（建议规模，不是已采集数量或足够性的保证）。若标签齐全可直接复用；域差/类别缺失仍需少量人工筛选、复核或补标，不承诺零人工。
6. 报道路类别IoU、候选区危险误判、行人灯红误判绿/车灯误认行人灯、目标无物误报/多物召回、OCR字符错误及端到端P95/过期率。验收门槛需在实测前确定，不能用训练loss或一次样图结果取代。
7. LocateAnything当前两猫只检出一猫，先扩大多物/无目标评测并检查提示词、解码及适配；一次漏检不足以认定必须训练3B模型。确需微调时先复核其训练方式/许可和16GB显存预算，不承诺全参数训练。
8. 手物接触数据无法替代相机-ToF内外参、时钟、距离归属和用户拿取确认。缺硬件时距离未知；模型不提供安全过街许可。

## 本轮实际操作

仅网页和本地文档核查。未提交申请/替用户接受数据协议，未下载上述数据或新权重，未训练、未打开摄像头、未修改业务实现。原156项软件回归与既有单图推理事实仍为上一轮基线，本轮不重复宣称其已重新测试。
