# 电脑端 LocateAnything 与 DeepSeek 样机

当前任务：先用电脑图片/摄像头完成真实模型验证；LocateAnything 手机迁移、高德联网联调暂缓。最终硬件仍按 USB/ToF 方案，电脑模拟不替代硬件验收。

## LocateAnything 来源与运行范围

- 模型：`nvidia/LocateAnything-3B`，固定 revision `c32291ca5e996f5a7a485845b4f57a233936bba0`。
- [固定模型说明与推理示例](https://huggingface.co/nvidia/LocateAnything-3B/blob/c32291ca5e996f5a7a485845b4f57a233936bba0/README.md)、[模型许可证](https://huggingface.co/nvidia/LocateAnything-3B/blob/c32291ca5e996f5a7a485845b4f57a233936bba0/LICENSE)。沿用已确认非商业测试用途，不改为商用/生产授权。
- 自定义源码只缓存在忽略目录，保留上游版权/许可证，不复制到项目分发。已审查 AutoConfig/AutoModel/AutoProcessor 导入及输入路径；上游 processor 支持 URL、LMDB/pickle 等分支，本项目只传本地解码 PIL.Image，不开放那些入口，不加载训练 pickle/bin。
- 官方模型默认 Magi 路径不适合本次 Windows 目标；本项目明确选择 PyTorch SDPA、BF16、单图和 slow/NTP 模式，图片缩至 640×480 以内，不以 H100 官方速度外推本机性能。
- 模型返回 0..1000 的二维框；CLI 转为 0..1，校验范围/顺序。没有模型置信度时返回 `confidence: null`；没有 ToF 返回 `distance_m: null`，不接入数值深度引导或自动确认拿取。

两个权重分片 SHA256：

| 文件 | 字节数 | SHA256 |
| --- | ---: | --- |
| model-00001-of-00002.safetensors | 4959632160 | 923cfc10fed19808067da6df85a9a4220ddc1f9eb91ceee94c0fecd05d0f2d58 |
| model-00002-of-00002.safetensors | 2701795216 | 3459ba101f40594f3f62d3312014f1f8378b4ba3da3b1d562480045938fc7d47 |

哈希来自固定 revision 的 Hugging Face LFS 元数据。`--range-download` 对 HTTP 206/Content-Range/分片长度和最终 SHA256 做校验；模型、缓存、环境、图片与结果均不进入 Git。

## 启动方法

在仓库根目录执行。新电脑先建独立 Python3.11 环境：

```powershell
py -3.11 -m venv .venv-pc
.\.venv-pc\Scripts\python.exe -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
.\.venv-pc\Scripts\python.exe -m pip install -r requirements-locate-pc.txt --index-url https://pypi.org/simple
.\.venv-pc\Scripts\python.exe -m pip check
.\.venv-pc\Scripts\python.exe -m tools.prepare_locate_pc --range-download
.\.venv-pc\Scripts\python.exe -m tools.locate_pc --image "你的图片.jpg" --query "a cup" --output artifacts/locate/result.png
```

电脑摄像头单次拍照：

```powershell
.\.venv-pc\Scripts\python.exe -m tools.locate_pc --camera 0 --query "a cup" --output artifacts/locate/camera.png
```

只有指定 `--camera` 才打开相机，只有指定 `--output` 才保存图片/JSON；照片只在本机处理。当前是单次找物入口，不是连续跟踪或完整拿取辅助。默认英文查询依据模型英语说明；中文效果另测。冷启动要加载约7.7GB权重，首次执行需等待，不是实时风险回路。

本施工机为 RTX4090 Laptop 16GB / Python3.11.9。因 CUDA 大包下载停滞，最终 `.venv-pc` 不启用 system-site-packages，只用本机目录 Junction 复用已有 torch/torchvision/torchgen/functorch，其他依赖单独安装，未修改全局包。此机器上的链接不随 Git 分发；其他电脑按以上正常安装命令构建，不能复制 venv。

## DeepSeek

精确传递依赖记录在根 `requirements-locate-pc.lock.txt`，本机 `.venv-pc` 的 `pip check` 已通过。需要相同版本重建时先安装上述 CUDA 两包，再用 lock 文件安装其余依赖。

官方 Base URL 为 `https://api.deepseek.com`。根据[官方模型调用说明](https://api-docs.deepseek.com/)，`deepseek-flash` 对应用户指定的 DeepSeek-V4.1-Flash-1017；[官方视觉说明](https://api-docs.deepseek.com/guides/vision/)确认其接受图片，所以首轮不再额外依赖千问视觉 API。

先用隐藏输入配置本机 Key，再执行真实对话：

```powershell
.\.venv-pc\Scripts\python.exe -m tools.dialogue_pc --configure
.\.venv-pc\Scripts\python.exe -m tools.dialogue_pc --question "你好，请介绍你的用途"
```

Key 可由 `DEEPSEEK_API_KEY` 环境变量或 Git 忽略的 `config.local.ai.json` 提供。本机已保存用户提供的 Key 到该忽略文件；其他电脑需要自行配置，不能复制提交密钥。程序不输出请求头/错误体，不跟随重定向。本轮系统 HTTPS 与项目 Python3.11 入口已分别成功完成短文本调用。基础 `.venv` Python3.12 曾出现 TLS EOF，故统一使用 `.venv-pc`；没有关闭 TLS 校验。不要把含 Key 的本地配置、截图或日志发到 GitHub。

只有显式选择图片并允许上传，才向官方 API 发图：

```powershell
.\.venv-pc\Scripts\python.exe -m tools.dialogue_pc --question "描述这张图片" --image "你的图片.jpg" --allow-image-upload
```

此入口与本地 LocateAnything 独立；图片最多2MiB，默认不发图。本轮已用 Hugging Face 官方文档公开样图实测图片调用，返回图中有两只猫；个人图片/摄像头画面未上传。这个样例验证了接口，不代表视觉准确率评测。云端描述有延迟，不能替代实时 ToF/避障。完整语音交互/TTS/麦克风仍未完成。

## 本机真实验证 / 2026-10-21

两个 safetensors 分片均已下载且 SHA256 与固定官方LFS元数据一致，模型目录合计约7.7GB，未进Git。Python3.11.9 / torch2.6.0+cu124 / transformers4.57.1 / RTX4090 Laptop 16GB 实测：

```powershell
.\.venv-pc\Scripts\python.exe -m tools.locate_pc --image datasets/pc-smoke/coco_sample.png --query cat --output artifacts/locate/coco-cats.png
```

公开样图来源：[Hugging Face 文档样图](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/coco_sample.png)。640×480、slow/NTP、单张单次；模型推理1377.51ms（不含冷加载/预处理），峰值CUDA allocated 7938.0MiB。输出一只猫的框 `[0.0, 0.112, 0.494, 0.988]`。图中实际两只猫，漏检另一只，因此只证明真实推理跑通，不能宣称多物完整召回或找物准确率验收。JSON/标注图仅存在本机 artifacts。

hybrid模式试验返回超过16个框，被上限校验拒绝；此模式不作为当前CLI选项交付，保留已实测成功的slow路径。源码审查与后续多图评测仍需继续，未以截断框或挑选结果掩盖失败。上游弃用提示保留日志，未修改权重或上游模型代码。

## 训练与无硬件范围说明

| 功能 | 第一轮 | 后续是否标注/微调 |
| --- | --- | --- |
| LocateAnything 找物 | 直接评测预训练权重 | 自定义物品、中文指令等明显不足后再决定 |
| OCR | 先使用 PaddleOCR 预训练模型 | 特殊字体、反光/模糊场景不足时考虑 |
| 手部关键点 | 先使用 MediaPipe 预训练模型 | 先处理遮挡、机位和标定，再决定 |
| 道路分割 | 先用预训练模型建立基线 | 需要眼镜视角样本验证，可能微调 |
| 国内行人信号灯 | 评测明确的灯状态模型 | 可能需要标注红/绿/未知及方向对象，依据实测决定 |

人工参与重点是采集、标注、验证误识别，第一版不从零训练全部模型。无硬件时可以验证公开图/录像和电脑摄像头输入、框输出、对话、失败/取消/过期逻辑；真实 ToF 距离归属、传感器标定、硬件震动、供电/USB时序和步行安全效果仍无法验收。

## 电脑页面入口 / 2026-10-21

在仓库根目录启动本地API（明确启用真实PC任务），另一个终端启动前端：

```powershell
.\.venv\Scripts\python.exe -m server.api --pc-runtime
```

```powershell
Set-Location frontend
npm run dev
```

打开http://127.0.0.1:5173，在“电脑模型样机”选择JPEG/PNG（最多1MiB），填写英文描述并点击“本机找物”。图片只在本机处理，框为静态结果，没有ToF/手物距离；初次任务需冷加载，每次独立进程，不是连续跟踪。页面显示的设备仍可离线，这是正确状态。

填写对话问题，勾选本次文字发送DeepSeek同意后点击发送；只上传文字、不上传所选图片，有API费用可能。任务处理中可取消，取消未确认时不声称已停。刷新页面或提交响应丢失时使用“查询后台任务”找回运行任务，再取消/等结果；恢复时不叠旧图。服务未加--pc-runtime会明确拒绝，不伪造结果。

任务使用系统临时文件，正常完成/失败/取消后清理；强制杀死主机进程不能保证清理。没有主动打开摄像头，不自动保存照片到项目。详细限制见[任务协议](../protocol/PC_JOBS_V1.md)，训练数据候选见[VISION_DATASETS_REVIEW](VISION_DATASETS_REVIEW.md)。部署其他电脑仍需自行安装独立环境、准备已授权模型和配置本机Key，Git不分发这些文件。
