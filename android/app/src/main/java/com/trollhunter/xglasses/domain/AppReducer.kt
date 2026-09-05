package com.trollhunter.xglasses.domain

object AppReducer {
    fun reduce(state: AppState, action: AppAction): AppState = when (action) {
        is AppAction.UsbDevicesChanged -> state.copy(
            availableUsbDeviceIds = action.deviceIds.distinct().sorted(),
            announcement = if (action.deviceIds.isEmpty()) "未发现 USB 设备" else "请选择眼镜 USB 设备",
        )
        is AppAction.UsbChanged -> onUsbChanged(state, action)
        is AppAction.RuntimeChanged -> state.copy(
            runtimes = state.runtimes + (action.task to action.state),
            announcement = "${action.task.title}运行时：${action.state.name.lowercase()}",
        )
        is AppAction.StartTask -> startTask(state, action.task)
        AppAction.CancelCurrentTask -> cancelCurrent(state)
        AppAction.RepeatLastOutput -> state.copy(
            announcementRevision = state.announcementRevision + 1,
        )
        is AppAction.TaskFailed -> failTask(state, action)
        is AppAction.TaskCompleted -> completeTask(state, action)
        is AppAction.ForegroundChanged -> state.copy(
            isForeground = action.foreground,
            announcement = if (action.foreground) "应用已回到前台" else "应用进入后台，停止任务输出",
            activeTask = if (action.foreground) state.activeTask else null,
            tasks = if (action.foreground) state.tasks else cancelRunning(state.tasks),
        )
        is AppAction.AudioFocusChanged -> state.copy(
            hasAudioFocus = action.held,
            announcement = if (action.held) "已获得音频焦点" else "音频焦点丢失，暂停播报",
        )
    }

    private fun onUsbChanged(state: AppState, action: AppAction.UsbChanged): AppState {
        val ready = action.state == UsbState.READY
        return state.copy(
            usbState = action.state,
            usbDeviceId = if (action.state in setOf(UsbState.DISCONNECTED, UsbState.FAILED)) {
                null
            } else {
                action.deviceId
            },
            activeTask = if (ready) state.activeTask else null,
            tasks = if (ready) state.tasks else cancelRunning(state.tasks),
            announcement = when (action.state) {
                UsbState.DISCONNECTED -> "眼镜已断开，当前任务已取消"
                UsbState.PERMISSION_REQUIRED -> "请选择眼镜并授予 USB 权限"
                UsbState.CONNECTING -> "正在建立 USB 会话"
                UsbState.TRANSPORT_OPEN -> "USB 端点已打开，等待 XG03 握手；风险监测尚未运行"
                UsbState.READY -> "眼镜 USB 会话已连接，基础风险监测已启动"
                UsbState.FAILED -> "USB 会话失败，请重新连接"
            },
        )
    }

    private fun startTask(state: AppState, task: TaskKind): AppState {
        if (state.usbState != UsbState.READY) {
            return state.copy(announcement = "眼镜未连接，无法启动${task.title}")
        }
        if (state.runtimes[task] != RuntimeState.AVAILABLE) {
            return state.copy(announcement = "${task.title}运行时尚未安装或未通过验证")
        }
        val cancelled = cancelRunning(state.tasks)
        return state.copy(
            activeTask = task,
            nextRequestId = state.nextRequestId + 1,
            tasks = cancelled + (task to TaskState.Running(state.nextRequestId)),
            announcement = "已启动${task.title}；基础风险监测保持独立运行",
        )
    }

    private fun cancelCurrent(state: AppState): AppState {
        val task = state.activeTask ?: return state.copy(announcement = "当前没有可取消的任务")
        return state.copy(
            activeTask = null,
            tasks = state.tasks + (task to TaskState.Cancelled),
            announcement = "已取消${task.title}；基础风险监测未关闭",
        )
    }

    private fun failTask(state: AppState, action: AppAction.TaskFailed): AppState {
        val task = state.activeTask ?: return state
        val running = state.tasks[task] as? TaskState.Running ?: return state
        if (running.requestId != action.requestId) return state
        return state.copy(
            activeTask = null,
            tasks = state.tasks + (task to TaskState.Failed(action.reason.take(160))),
            announcement = "${task.title}失败；基础风险监测保持独立运行",
        )
    }

    private fun completeTask(state: AppState, action: AppAction.TaskCompleted): AppState {
        val task = state.activeTask ?: return state
        val running = state.tasks[task] as? TaskState.Running ?: return state
        if (running.requestId != action.requestId) return state
        return state.copy(
            activeTask = null,
            tasks = state.tasks + (task to TaskState.Completed),
            announcement = "${task.title}已完成；基础风险监测保持独立运行",
        )
    }

    private fun cancelRunning(tasks: Map<TaskKind, TaskState>): Map<TaskKind, TaskState> =
        tasks.mapValues { (_, value) -> if (value is TaskState.Running) TaskState.Cancelled else value }
}
