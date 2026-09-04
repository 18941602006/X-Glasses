# tools

check_foundation.py 检查基础工程及 Phase 2A 精确运行白名单；check_source_audit.py 检查固定来源/许可状态和剩余关卡。二者都不验证模型或硬件。replay_usb.py 通过公共输入接口执行纯内存演示/指定 XGR1 文件回放，运行 python -m tools.replay_usb --demo；不访问硬件或调用模型，详细限制见 [协议合同](../docs/protocol/USB_V1.md)。

数据边界见 docs/construction/LAYER_CONTRACT.md，实际进度以 HANDOFF 最新记录为准。
