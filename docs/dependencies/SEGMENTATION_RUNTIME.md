# 道路分割运行时关卡

候选仍为 PaddleSeg release/2.10 固定提交 `3c4db66de1d9d59d0628ed87590b6308a2f4aa2a` 的 PP-LiteSeg STDC1。源码 Apache-2.0；官方[模型导出说明](https://github.com/PaddlePaddle/PaddleSeg/blob/3c4db66de1d9d59d0628ed87590b6308a2f4aa2a/docs/model_export.md)给出 Cityscapes 权重、argmax/softmax 导出及 Paddle Inference/Paddle Lite 路径。

Cityscapes [现行许可](https://www.cityscapes-dataset.com/license/)允许非商业科研、教学和个人实验，并允许分发无法还原数据的抽象衍生模型，但禁止商业目的、要求引用且数据本身不可再分发。此处只记录条款，不替用户接受协议。当前未下载 checkpoint/数据、未核验权重哈希或权重文件内许可，不把 PaddleSeg 源码许可自动套用到权重。

技术风险：官方基准来自车载 Cityscapes 视角，road/sidewalk 标签不等于眼镜佩戴者可行区；原始基准速度基于 V100/特定 Snapdragon 855 配置，不能外推本机 4090 Laptop 或骁龙 8。正式接入需固定 checkpoint SHA256、Paddle/CUDA 组合和 deploy.yaml，隔离环境单帧验证，采集获授权的眼镜视角评测集，再测漏报/误报/延迟。Android 需单独验证 Paddle Lite/其他后端，不直接复制桌面 worker。

当前选择：提交运行时无关的 worker 协议和融合合同，模型状态保持 `not_installed`。在权重关卡完成前，服务不得生成 live WalkableMask；synthetic/replay 必须显式标源。
