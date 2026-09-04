# 硬件接口评审 / 设计级，未上电验证

本清单用于核对具体模块，不是采购订单或已测接线图。主板仍是 XIAO ESP32-S3 Sense，单前向 ToF，无 SLAM/额外腕部传感器。

## 模块与信号候选

| 模块 | 候选 | 主机侧接口 |
| --- | --- | --- |
| 眼镜主板 | Seeed XIAO ESP32-S3 Sense，核实相机批次 | 板载原生 USB-C，不经 UART 桥 |
| ToF | Pololu #3417 VL53L5CX carrier | 3.3V 电平 I²C；具体供电/峰值见下 |
| IMU | Adafruit LSM6DSOX breakout | 3.3V VIN，共地；7 位地址 0x6A（可选 0x6B） |
| 震动驱动 | Adafruit DRV2605L breakout | 3.3V VIN，共地；7 位地址 0x5A |
| 震动执行器 | 3V ERM 小型马达，型号/额定及峰值电流待选 | 接驱动 OUT+/OUT−，不直接 GPIO 驱动 |
| 用户输入 | 两个常开瞬时按键 | GPIO1/D0、GPIO2/D1 至 GND，3.3V 上拉，软件消抖 |
| 结构与线材 | USB 数据线、刚性相机-ToF 支架、应力释放 | 不买 Y 型并联供电线；耳机连计算主机 |

外设 SDA/SCL 拟用 GPIO5/D4、GPIO6/D5；ToF LPn 可用 GPIO4/D3（首版轮询，INT 可不接），I2C_RST 按转接板默认下拉。保留 GPIO43/44 作串口调试候选。避开相机 GPIO10–18/38–40/47–48、PDM 41/42、SD 3/7/8/9 和原生 USB 19/20；GPIO3 还是启动绑带，不拿作普通按钮。以上据 [Seeed 引脚表](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) 和 [ESP-IDF USB](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32s3/api-reference/peripherals/usb_device.html) 制定，必须按到货板复核。

## 不能忽略的电气细节

Pololu #3417 的 SDA/SCL 上拉电平跟随 VIN。拟用 3.3V VIN，禁止用 5V VIN 后直连 ESP32 GPIO；LPn/I2C_RST 不耐 5V。该板给出的测距电流约 100mA、峰值可至 150mA，只是厂商资料，不是本机功耗。[模块资料](https://www.pololu.com/product/3417)

LSM6DSOX 和 DRV2605L 转接板也按 3.3V 电平连接；多个板自带上拉并联后要核验等效阻值和上升时间，首版先按 400kHz 以下共享总线规划。ToF 固件上传/测量读取需分块且不能长时间霸占总线，马达控制应及时；若实测不满足，再评估分总线，不预设必然可达 15Hz。[IMU 引脚](https://learn.adafruit.com/lsm6dsox-and-ism330dhc-6-dof-imu/pinouts)、[震动驱动](https://learn.adafruit.com/adafruit-drv2605-haptic-controller-breakout/pinouts)

地址需区分表示法：VL53L5CX 驱动常量 0x52 对应 7 位 0x29；ST LSM6DSOX 头文件用 0xD5/0xD7，而主机 7 位地址为 0x6A/0x6B。ESP-IDF API 按实际参数要求只转换一次，不能照抄 8 位读写地址。[ToF 头文件](https://github.com/stm32duino/VL53L5CX/blob/e904f764c1bdd2c35032cb4e9f9bbfdd94329865/src/vl53l5cx_api.h)、[IMU 头文件](https://github.com/STMicroelectronics/lsm6dsox-pid/blob/9570c27f142448b9e9d83bc9b746a5851c0ee785/lsm6dsox_reg.h)

## 供电与首次测试关卡

不能用主板空载或 Wiki 某次摄像头例子的电流当整机峰值；Seeed 不同示例电流差异较大，电源余量仍待实测。摄像头、ToF、马达同时动作要测 USB 总电流、3.3V 跌落和温升，确认主机供电、板上稳压器/线材容量。马达具体峰值未确定前，不批准整机长期佩戴上电。

USB 枚举前后电流与声明一致；传感器/摄像头/震动采用阶段启动，不能默认任何电脑口/手机 OTG 都能无条件供足电。必要的独立电源/电源路径管理属于后续明确变更，不擅自并联电源。

台架顺序：只连主板并确认 USB → 单 ToF/IMU 电压与地址 → 同步采样与总线占用 → 照相并发 → 限时低强度马达 → 持续/拔插/掉电。断电眼镜无本地反馈，由主机清除旧提示并告警。首次测距要固定姿态、检查保护膜、记录有效性，不把无回波当无障碍。

尚未确定：到货 PCB/相机批次、马达具体料号、线长、总功耗与手机供电；不采购、不改 PCB、不承诺可穿戴安全。
