# 电脑静态模型任务 / V1

用途：电脑样机选图找物与显式云端文字对话。不是USB协议、实时帧推理、拿取完成或行进指令。既有/api/v1/status和设备命令语义不变；PC任务不会把设备标READY。

## 启用与边界

默认`python -m server.api`不启用任务。使用`python -m server.api --pc-runtime`显式启用，默认子进程解释器`.venv-pc/Scripts/python.exe`，可由启动者在CLI使用`--pc-python`指定；HTTP不能指定解释器、模型路径、磁盘路径、命令或云端地址。API仅绑定回环。POST必须是允许的本地Origin（http://127.0.0.1或localhost的5173/当前API端口）；不启用跨域CORS。

## HTTP

- `POST /api/v1/pc/jobs`：JSON；202返回job_id/kind/state/result/error。不可假设返回即推理成功。
- 找物字段严格为`kind=locate`、`query`（1..160可打印字符）、`image_base64`（纯base64的JPEG/PNG，解码后最多1MiB；不接URL或文件路径）。模型进程检查最多1600万像素，转换RGB并保持比例缩至640×480以内。
- 文字字段严格为`kind=dialogue`、`question`（1..1000可打印字符）、`allow_cloud_text=true`。拒绝附带图像/Key/额外字段。UI需先勾选本次文字上传同意；后端只调用已有官方文字provider。
- `GET /api/v1/pc/jobs/{job_id}`查询；状态为running/succeeded/failed/cancelled。job_id为32位随机十六进制，不接受路径片段。
- `POST /api/v1/pc/jobs/{job_id}/cancel`提交空JSON对象，返回当前状态。已终态不改成取消；运行中先标cancelled并触发进程终止，进程退出前仍保持busy，不允许第二任务占用GPU。
- `GET /api/v1/pc/active`返回`{"job":记录或null}`，用于页面刷新/提交响应丢失后找回仍在运行的任务。前端查询后台时清除选图，避免将恢复任务的框叠到不相关图片。
- 400输入无效，403 Origin不符，404任务不存在，409单worker忙，413请求超限，415非JSON，503未显式启用。正文上限1410000字节，socket读写超时5秒，不支持chunked；请求和错误正文不得含凭据/本机路径。

## 生命周期与隐私

每次任务启动独立Python进程，冷加载不计入返回的inference_ms，不能据此宣称实时性能。单活动任务、不排等待队列，最多保留16条内存回执，不保留请求/图片/问题副本至记录；终态保留到淘汰或服务关闭。硬超时180秒；stdout/stderr各128KiB上限，取消/超时/超限结束子进程。公开错误只给有限错误码，禁止返回traceback/第三方错误体/请求头。UTF-8明确设置，模型进程本地离线加载，不自动下载权重。

图像/问题在系统临时目录传给子进程，正常完成、失败、取消后删除该任务临时目录，非安全擦除保证；主机崩溃/强制杀死父进程可能留临时文件，不能宣传绝不落盘。服务关闭时取消活动子进程。系统临时目录和环境均不入Git。图片不会送DeepSeek；文字默认不发送，需每次明确点击。API Key只从已有环境或忽略的本机配置读取，不提供HTTP读取/写入Key接口。

框为0..1，前端只叠在提交的同一静态图上；切换查询/图片/任务清除结果。取消后晚到结果丢弃；查询失败不显示旧框。distance_m/confidence保持null、tof_status=not_connected、grasp_confirmed=false。对话标text_only，视觉标static_image_not_live；这些是调试显示，不进入实时风险仲裁、不触发语音/震动或自动拿取。

## 未覆盖

没有连续相机、实时跟踪/手部、ToF/USB实机、分割/OCR/灯模型或语音输出接入；没有训练或质量验收。自动测试验证合同，真实单图/文字请求另记TEST_METRICS。浏览器人工视觉与屏幕阅读器仍未验收，用户此前省略截图步骤，不将其恢复为阻塞。
