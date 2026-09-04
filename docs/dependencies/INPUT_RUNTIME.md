# Phase 2A 输入运行依赖 / 2026-09-05

Phase 1 的 sources.audit.json 是历史审核快照，不改写其当时 runtime_verified=false；本文件记录随后真实安装。协议/时钟/传感器/控制仍是标准库；实际本地串口适配器可选安装 pyserial 3.5。

- 锁：根 requirements-input.txt，只允许官方 PyPI wheel pyserial-3.5-py2.py3-none-any.whl，SHA256 c4451db6ba391ca6ca299fb3ec7bae67a5c55dde170964c7a14ceefec02f2cf0；无传递依赖。
- 来源：[PyPI 3.5 元数据](https://pypi.org/pypi/pyserial/3.5/json)、[官方 API](https://pyserial.readthedocs.io/en/latest/pyserial_api.html)。使用有时限短读写；端口只显式指定，不接受 network URL 或自动开端口。
- 实际安装：项目 .venv、Python 3.12.14，pip --require-hashes --only-binary=:all: 安装成功，loop:// 本地内存回环测试通过；这不是 USB/硬件测试。
- 许可证：实际 wheel METADATA 为 BSD，serial/__init__.py 与 serialwin32.py 标 BSD-3-Clause；wheel dist-info 未携带独立 LICENSE 文件。已核对 [官方 v3.5 LICENSE](https://github.com/pyserial/pyserial/blob/v3.5/LICENSE.txt)，分发本工程及依赖时须保留版权、三条件和免责声明，不能仅拷贝 wheel 忽略通知。没有将 pyserial 源码 vendoring 入库。
- 端口枚举 python -m tools.usb_probe --list 返回 []，未打开任何真实设备；真实拔插/CDC/电源未测。
- 只读环境：Node 22.17.1、npm 10.9.2；GPU NVIDIA GeForce RTX 4090 Laptop GPU / 16376MiB / 驱动 595.79。当前 PATH 未发现 java/cmake/ninja/idf.py，常见 ESP-IDF/Android SDK/JDK 目录未找到；不是全盘证明未安装。后续优先隔离工具环境，不改全局配置。

安装和探针（实际 probe 仅针对已刷写兼容 X-Glasses 固件的明确端口）：

```powershell
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple --require-hashes --only-binary=:all: -r requirements-input.txt
.\.venv\Scripts\python.exe -m tools.usb_probe --list
.\.venv\Scripts\python.exe -m tools.usb_probe --port COM3 --seconds 5
```

最后一条为用户选择端口后手动操作示例，本轮未运行。仅发送 HELLO/CLOCK，不启动相机/录制/震动。DTR=true/RTS=false 用于 CDC 主机状态，OS 开口可能影响控制线；不能拿不明设备或下载口测试，不承诺不会复位。115200 是 CDC line coding，不是 USB 视频带宽上限。USB Full-Speed 实际吞吐与 30 分钟链路另测。
