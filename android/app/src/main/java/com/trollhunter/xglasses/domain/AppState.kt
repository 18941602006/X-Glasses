package com.trollhunter.xglasses.domain

enum class TaskKind(val title: String, val description: String) {
    NAVIGATION("行进导航", "地图步行指引、道路候选与近距避障"),
    LOCATE_GRASP("找物拿取", "定位目标并辅助用户拿取"),
    READ_TEXT("读文字", "按原始顺序朗读识别文字"),
    SIGNAL("看信号灯", "只报告灯态，不提供过街许可"),
    DIALOGUE("AI 对话", "低优先级问答，不参与风险判断"),
}

enum class UsbState {
    DISCONNECTED,
    PERMISSION_REQUIRED,
    CONNECTING,
    TRANSPORT_OPEN,
    READY,
    FAILED,
}
enum class RuntimeState { NOT_INSTALLED, CHECKING, AVAILABLE, FAILED }

sealed interface TaskState {
    data object Idle : TaskState
    data class Running(val requestId: Long) : TaskState
    data class Failed(val reason: String) : TaskState
    data object Completed : TaskState
    data object Cancelled : TaskState
}

data class AppState(
    val usbState: UsbState = UsbState.DISCONNECTED,
    val usbDeviceId: Int? = null,
    val availableUsbDeviceIds: List<Int> = emptyList(),
    val runtimes: Map<TaskKind, RuntimeState> =
        TaskKind.entries.associateWith { RuntimeState.NOT_INSTALLED },
    val tasks: Map<TaskKind, TaskState> = TaskKind.entries.associateWith { TaskState.Idle },
    val activeTask: TaskKind? = null,
    val nextRequestId: Long = 1,
    val announcement: String = "眼镜未连接",
    val announcementRevision: Long = 0,
    val isForeground: Boolean = true,
    val hasAudioFocus: Boolean = false,
) {
    val safetyMonitoringActive: Boolean
        get() = usbState == UsbState.READY
}

sealed interface AppAction {
    data class UsbDevicesChanged(val deviceIds: List<Int>) : AppAction
    data class UsbChanged(val state: UsbState, val deviceId: Int? = null) : AppAction
    data class RuntimeChanged(val task: TaskKind, val state: RuntimeState) : AppAction
    data class StartTask(val task: TaskKind) : AppAction
    data object CancelCurrentTask : AppAction
    data object RepeatLastOutput : AppAction
    data class TaskFailed(val requestId: Long, val reason: String) : AppAction
    data class TaskCompleted(val requestId: Long) : AppAction
    data class ForegroundChanged(val foreground: Boolean) : AppAction
    data class AudioFocusChanged(val held: Boolean) : AppAction
}
