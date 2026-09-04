# Phase 1 手机迁移风险预审

目标不变：骁龙 8 系列 Android，本地推理；前期电脑验证不替代最终目标。目前没有具体手机或 Android 工程。

| 风险 | 已核查依据 | 后续实证 |
| --- | --- | --- |
| LocateAnything 不是普通检测 ONNX | 自定义 AutoModel、BF16、混合生成和自定义注意力/视觉预处理 | 拆解 preprocess/vision/LLM/生成与框解析，核对移动运行时支持，不仅测模型加载 |
| NVIDIA 路线与手机不同 | 官方以 CUDA/Transformers 为主，列出 NVIDIA GPU；本轮未找到 Android 成品部署证据 | 固定手机和运行时，做算子/量化精度/内存/延迟/温升试验 |
| 模型内存 | 3B×2 字节约 6GB 仅粗略参数预算；4bit 约 1.5GB 仅理论参数量，不含 KV/视觉/临时内存 | 实际峰值及长时复测，不能由理论大小宣布可跑 |
| USB Host | 支持由具体设备、权限、角色/供电和后台行为共同决定 | 真机拒绝/重连/锁屏/后台/来电，CRC/过期帧和命令确认一致 |
| UI/音频 | 桌面 React 不等于 Compose/TalkBack，USB-C 已占用 | 手机五任务/大触控/焦点/取消/重复和开放式耳机 |
| 外部服务 | 地图/云对话仍可能需联网 | 服务地区/条款/隐私、断网与风险提示隔离 |

来源：[固定模型配置](https://huggingface.co/nvidia/LocateAnything-3B/blob/c32291ca5e996f5a7a485845b4f57a233936bba0/config.json)、[模型说明](https://huggingface.co/nvidia/LocateAnything-3B/blob/c32291ca5e996f5a7a485845b4f57a233936bba0/README.md)、[Android USB Host](https://developer.android.com/develop/connectivity/usb/host)。

上表内存是计算推断，不是运行数据；未找到成品不证明技术绝对不可能。模型许可差异见 [环境关卡](../dependencies/ENVIRONMENT_GATES.md)。若单机本地目标无法满足，提交可复现证据再请用户选择，不默认云端或替代识物模型。
