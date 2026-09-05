# 道路候选与 ToF 融合核心 v1

输入是上游分割模型生成的二值“候选可行区域”掩码和已映射到主机单调时钟的 ToF 样本。掩码不是安全道路证明；引擎不识别盲道/斑马线，不做 SLAM、定位或过街决策。

`FusionProfile` 为每个 4×4/8×8 ToF zone 保存归一化图像矩形。mask、ToF 与 profile 的 calibration_id 必须一致，session 必须一致；两路最坏时间差、源年龄和接收驻留必须在显式 `NavigationConfig` 内。配置还包含近障/紧急距离、ToF 有效率、分割质量、下半部 ROI 和候选覆盖阈值；代码没有可直接用于佩戴的默认阈值。

输出 `NavigationEvent` 带 verdict、direction、reason、创建/过期时间、session/frame/sample/profile/config、三走廊覆盖率、最近有效距离和 live/replay/synthetic 来源。verdict 仅有 unknown/stop/candidate；不存在 safe、cross 或 go。中心紧急近障直接 stop；非紧急障碍屏蔽重叠走廊，优先中心，否则选覆盖率更高的一侧。全部走廊不足则 stop。低 ToF 有效率、低模型质量、时间/标定错误均 unknown。

当前合成测试验证合同与保守降级，不能给出真实漏报率、误报率、日光性能或延迟。profile 和阈值必须用实际镜头/ToF 安装位姿标定并冻结版本后，才可进行有人陪同的受控场景评测。
