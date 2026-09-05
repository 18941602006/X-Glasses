# VS Code 与 ESP-IDF

VS Code 可用于本项目，但编辑器/扩展不替代 ESP-IDF SDK。当前固定的 SDK、工具和 Python 环境是可复现编译基础；Espressif IDF 扩展只是配置、编译、烧录、monitor 的界面。未经用户选择，本轮不安装/更新全局扩展，不改用户 settings.json。

建议安装官方扩展 ID `espressif.esp-idf-extension`，选择 **Use existing setup**，指向固定 ESP-IDF 5.5.4 与隔离 IDF_TOOLS_PATH。不要让扩展安装 latest 或覆盖当前版本。项目根作为 workspace，固件目录为 firmware；服务/前端继续用各自命令，不在同一个固件 CMake 工程内。

Windows 注意：官方文档要求 IDF/项目路径避免空格，非 ASCII 只有启用 UTF-8 系统区域设置时才建议使用。当前项目路径含中文；不为此修改系统区域或要求重启。命令行验证采用工具创建的唯一 ASCII 构建副本，输出位置明确；任何烧录必须回到真实项目配置、明确 COM 口并人工确认板型，绝不从临时副本或自动枚举直接 flash。

VS Code 状态栏显示 build 成功只表示对应目标编译，不能代表 USB 枚举、传感器、马达、供电或产品安全。monitor 输出走 USB Serial/JTAG 调试口，应用二进制 CDC 不能混文本日志。
