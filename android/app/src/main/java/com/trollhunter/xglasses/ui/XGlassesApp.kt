package com.trollhunter.xglasses.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.OutlinedTextField
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.trollhunter.xglasses.domain.AppAction
import com.trollhunter.xglasses.domain.AppState
import com.trollhunter.xglasses.domain.RuntimeState
import com.trollhunter.xglasses.domain.TaskKind
import com.trollhunter.xglasses.navigation.GuidanceStatus
import com.trollhunter.xglasses.navigation.NavigationUiState
import com.trollhunter.xglasses.navigation.PlaceCandidate

private val Background = Color(0xFF07110F)
private val Foreground = Color(0xFFF0F8F4)
private val Accent = Color(0xFF2E7D5B)
private val AppColors = darkColorScheme(
    primary = Accent,
    onPrimary = Foreground,
    background = Background,
    onBackground = Foreground,
    surface = Background,
    onSurface = Foreground,
)

@Composable
fun XGlassesApp(
    state: AppState,
    dispatch: (AppAction) -> Unit,
    refreshUsb: () -> Unit,
    connectUsb: (Int) -> Unit,
    navigationVisible: Boolean,
    navigationState: NavigationUiState,
    openNavigation: () -> Unit,
    closeNavigation: () -> Unit,
    updateDestinationQuery: (String) -> Unit,
    searchDestination: () -> Unit,
    selectDestination: (PlaceCandidate) -> Unit,
    startNavigation: () -> Unit,
    stopNavigation: () -> Unit,
) {
    MaterialTheme(colorScheme = AppColors) {
        Surface(modifier = Modifier.fillMaxSize(), color = Background, contentColor = Foreground) {
            if (navigationVisible) {
                NavigationScreen(
                    state = navigationState,
                    close = closeNavigation,
                    updateQuery = updateDestinationQuery,
                    search = searchDestination,
                    select = selectDestination,
                    start = startNavigation,
                    stop = stopNavigation,
                )
            } else LazyColumn(
                modifier = Modifier.fillMaxSize().padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                item {
                    Text(
                        "X-Glasses",
                        fontSize = 32.sp,
                        modifier = Modifier.semantics { heading() },
                    )
                }
                item { StatusCard(state) }
                item { UsbChooser(state, refreshUsb, connectUsb) }
                items(TaskKind.entries) { task ->
                    TaskButton(task, state, dispatch, openNavigation)
                }
                item {
                    Button(
                        onClick = { dispatch(AppAction.CancelCurrentTask) },
                        modifier = Modifier.fillMaxWidth().heightIn(min = 64.dp),
                        enabled = state.activeTask != null,
                    ) {
                        Text("取消当前任务", fontSize = 20.sp)
                    }
                }
                item {
                    Button(
                        onClick = { dispatch(AppAction.RepeatLastOutput) },
                        modifier = Modifier.fillMaxWidth().heightIn(min = 64.dp),
                    ) {
                        Text("重复上一条提示", fontSize = 20.sp)
                    }
                }
                item {
                    Text(
                        "绿灯识别不是过街许可。原型测试请保留盲杖并由他人陪同。",
                        fontSize = 16.sp,
                    )
                }
            }
        }
    }
}

@Composable
private fun UsbChooser(state: AppState, refreshUsb: () -> Unit, connectUsb: (Int) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(
            onClick = refreshUsb,
            modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp),
        ) {
            Text("刷新 USB 设备", fontSize = 18.sp)
        }
        if (state.availableUsbDeviceIds.isEmpty()) {
            Text("没有可选择的 USB 设备", fontSize = 16.sp)
        } else {
            state.availableUsbDeviceIds.forEach { deviceId ->
                Button(
                    onClick = { connectUsb(deviceId) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 64.dp)
                        .semantics { contentDescription = "选择并授权 USB 设备 $deviceId" },
                ) {
                    Text("连接 USB 设备 $deviceId", fontSize = 18.sp)
                }
            }
        }
    }
}

@Composable
private fun StatusCard(state: AppState) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Accent)
            .padding(16.dp)
            .semantics { liveRegion = LiveRegionMode.Polite },
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Text("USB：${state.usbState.name.lowercase()}", fontSize = 18.sp)
        Text(
            if (state.safetyMonitoringActive) "基础风险监测：运行中" else "基础风险监测：未运行",
            fontSize = 18.sp,
        )
        Text(
            state.announcement,
            fontSize = 16.sp,
            modifier = Modifier.semantics {
                contentDescription = "${state.announcement}；提示序号${state.announcementRevision}"
            },
        )
    }
}

@Composable
private fun TaskButton(
    task: TaskKind,
    state: AppState,
    dispatch: (AppAction) -> Unit,
    openNavigation: () -> Unit,
) {
    val runtime = state.runtimes[task] ?: RuntimeState.NOT_INSTALLED
    Button(
        onClick = {
            if (task == TaskKind.NAVIGATION) openNavigation() else dispatch(AppAction.StartTask(task))
        },
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 76.dp)
            .semantics {
                contentDescription =
                    "${task.title}；${task.description}；运行时${runtime.name.lowercase()}"
            },
    ) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Column {
                Text(task.title, fontSize = 22.sp)
                Text(task.description, fontSize = 14.sp)
            }
            Text(runtime.name.lowercase(), fontSize = 12.sp)
        }
    }
}

@Composable
private fun NavigationScreen(
    state: NavigationUiState,
    close: () -> Unit,
    updateQuery: (String) -> Unit,
    search: () -> Unit,
    select: (PlaceCandidate) -> Unit,
    start: () -> Unit,
    stop: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Text("步行导航", fontSize = 30.sp, modifier = Modifier.semantics { heading() })
        }
        item {
            Column(
                modifier = Modifier.fillMaxWidth().background(Accent).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Text("状态：${guidanceLabel(state.guidance.status)}", fontSize = 20.sp)
                Text(
                    state.guidance.instruction,
                    fontSize = 20.sp,
                    modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                )
                state.guidance.remainingDistanceM?.let { Text("预计剩余 ${it} 米", fontSize = 18.sp) }
                state.error?.let { Text(it, fontSize = 18.sp) }
            }
        }
        item {
            Text(
                if (state.providerConfigured) "地图服务：已配置" else "地图服务：未配置，请由团队设置服务地址",
                fontSize = 17.sp,
            )
        }
        item {
            OutlinedTextField(
                value = state.query,
                onValueChange = updateQuery,
                label = { Text("目的地名称或地址") },
                modifier = Modifier.fillMaxWidth().semantics { contentDescription = "输入目的地名称或地址" },
                singleLine = true,
            )
        }
        item {
            Button(
                onClick = search,
                enabled = state.providerConfigured && !state.searching,
                modifier = Modifier.fillMaxWidth().heightIn(min = 64.dp),
            ) { Text(if (state.searching) "正在搜索" else "搜索目的地", fontSize = 20.sp) }
        }
        items(state.candidates, key = { it.id }) { candidate ->
            Button(
                onClick = { select(candidate) },
                modifier = Modifier.fillMaxWidth().heightIn(min = 68.dp)
                    .semantics { contentDescription = "选择目的地 ${candidate.label}" },
            ) { Text(candidate.label, fontSize = 18.sp) }
        }
        state.selected?.let { destination ->
            item { Text("已选择：${destination.label}", fontSize = 18.sp) }
            item {
                Button(
                    onClick = start,
                    enabled = state.locationPermissionGranted && !state.routeLoading,
                    modifier = Modifier.fillMaxWidth().heightIn(min = 68.dp),
                ) { Text(if (state.routeLoading) "正在规划" else "开始步行导航", fontSize = 20.sp) }
            }
        }
        item {
            Button(
                onClick = stop,
                enabled = state.guidance.status !in setOf(GuidanceStatus.IDLE, GuidanceStatus.ARRIVED),
                modifier = Modifier.fillMaxWidth().heightIn(min = 64.dp),
            ) { Text("结束导航", fontSize = 20.sp) }
        }
        item {
            Button(onClick = close, modifier = Modifier.fillMaxWidth().heightIn(min = 64.dp)) {
                Text("返回首页", fontSize = 20.sp)
            }
        }
        item {
            Text("地图数据：© OpenStreetMap 贡献者，ODbL", fontSize = 14.sp)
            Text("地图路线不是道路安全证明；行进中继续使用盲杖并听从近距风险提示。", fontSize = 16.sp)
        }
    }
}

private fun guidanceLabel(status: GuidanceStatus): String = when (status) {
    GuidanceStatus.IDLE -> "未开始"
    GuidanceStatus.ROUTING -> "规划中"
    GuidanceStatus.ACTIVE -> "导航中"
    GuidanceStatus.PAUSED -> "定位不足，已暂停"
    GuidanceStatus.REROUTE_REQUIRED -> "偏航重算"
    GuidanceStatus.ARRIVED -> "到达附近"
    GuidanceStatus.FAILED -> "不可用"
}
