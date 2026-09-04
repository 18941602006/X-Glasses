# 环境隔离与放行条件

## 环境划分（设计，不是已安装）

| 环境 | 候选与依据 | 放行要求 |
| --- | --- | --- |
| .venv 基础 | Python 3.12.14 / Ruff 0.12.12，已验证 | 保持工具测试，不放模型 |
| USB/调试主机 | Python 3.12；pyserial 3.5、FastAPI 0.141.1、Uvicorn 0.52.4；解码候选 OpenCV-headless 4.11.0.86 + NumPy 1.26.4 | 新建隔离环境，解析传递依赖锁、许可证/漏洞检查、最小安装与输入测试后再采用 |
| LocateAnything worker | 优先另选 Python 3.11 推理环境；官方 transformers 4.57.1，tokenizers 0.22.0，按 GPU/CUDA 固定 torch | 用途许可、远程代码审查、可安装组合、单张推理与超时隔离；不能照装训练大清单 |
| Paddle 系 | 分割/OCR 独立验证并按实际 Paddle 版本隔离 | checkpoint/数据许可、导出与算子、标签匹配 |
| 手部 worker | MediaPipe 0.10.21 源码候选 | .task 权重许可和环境兼容、帧时间合同 |
| 固件 | ESP-IDF 5.5.4 + TinyUSB/Camera 候选 | 安装/传递锁/编译/恢复模式/实机，未进行 |

官方 LocateAnything 包含训练及服务依赖、Triton/DeepSpeed、浮动包，不是最小推理锁。模型卡还固定 numpy 1.25.0；PyPI 该版本无 CPython 3.12 预编译 wheel，且其 OpenCV 4.11.0.86 在 Python 3.12 下要求 numpy>=1.26.0，故不能原样组合到当前基础环境。采用独立 Python 3.11 是待验证路线，不是已成功安装。[官方工程清单](https://github.com/NVlabs/Eagle/blob/783f656d127ee498137b5ff52603ce36c292d317/Embodied/pyproject.toml)、[模型卡](https://huggingface.co/nvidia/LocateAnything-3B/blob/c32291ca5e996f5a7a485845b4f57a233936bba0/README.md)、[NumPy 元数据](https://pypi.org/pypi/numpy/1.25.0/json)、[OpenCV 元数据](https://pypi.org/pypi/opencv-python-headless/4.11.0.86/json)。

本次 PyPI 检索还见 OpenCV-headless 5.0.0.93 要求 Python>=3.9 时 NumPy>=2；不把“最新版本”直接混入 NumPy<2 的模型环境。候选版本不是强制升级，也未验证全部传递依赖。

## LocateAnything 许可差异：修正旧结论，不自动放行

固定 HF revision c32291ca5e996f5a7a485845b4f57a233936bba0 的 [LICENSE](https://huggingface.co/nvidia/LocateAnything-3B/blob/c32291ca5e996f5a7a485845b4f57a233936bba0/LICENSE) 第 3.3 节将非商业用途表述为研究或评测；固定 GitHub [Embodied/LICENSE_MODEL](https://github.com/NVlabs/Eagle/blob/783f656d127ee498137b5ff52603ce36c292d317/Embodied/LICENSE_MODEL) 相同。但同版模型卡仍用学术及非营利研究的更窄说明，且提示 Qwen Research License 等第三方条款。

先前使用的根 LICENSE_MODEL 链接在当前固定 GitHub 提交为 404；搜索索引仍可返回旧文本。2026-09-05 用户明确“测试使用，不为学术或盈利为目的”。结合固定许可文件第 3.3 节的评测范围，当前改为 evaluation_only：允许准备非商业测试，不再把用途确认列为阻塞；说明页描述差异保留记录，不据此扩大到商业或生产用途。运行前仍审查自定义代码/第三方条款、固定版本并使用隔离环境；截至本次审核没有下载权重或执行 trust_remote_code。用户陈述是用途事实，不替代权利人许可；本次依据是已读取的固定许可证，而不是仅凭用户说“放心”。此处是工程合规记录，不是法律意见。

## 必须留待实施前通过

1. 本轮模型用途已确认为非商业测试；下载时固定 revision 并核验文件哈希、逐文件/第三方声明。不扩大为商业/生产分发，用途变更重新审核。
2. Hugging Face 自定义 AutoModel/processor 代码先审查，固定 code revision/local path，不运行不明远程代码。
3. USB/调试主机和固件完成实际依赖解析与编译；源码快照不能代替完整 SBOM/lock。
4. ToF Arduino 平台层移植和嵌入固件数组许可；多区输出质量/时间语义不能丢。
5. 具体采购模块/供电和手机机型需实测，不默认性能/兼容性。
6. 交通灯权重、PP-LiteSeg checkpoint、MediaPipe .task、OCR 模型、地图/对话供应商尚未冻结；在对应阶段前审核，不用旧模型目录兜底。

允许继续的工作：不触碰模型的 USB 协议设计、输入/回放单测和硬件台架规划。禁止因某模型关卡未通过而静默更换识物模型或上传画面至云端。
