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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
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

private val Background = Color(0xFF07110F)
private val Foreground = Color(0xFFF0F8F4)
private val Accent = Color(0xFF2E7D5B)

@Composable
fun XGlassesApp(
    state: AppState,
    dispatch: (AppAction) -> Unit,
    refreshUsb: () -> Unit,
    connectUsb: (Int) -> Unit,
) {
    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize(), color = Background, contentColor = Foreground) {
            LazyColumn(
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
                items(TaskKind.entries) { task -> TaskButton(task, state, dispatch) }
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
        Text(state.announcement, fontSize = 16.sp)
    }
}

@Composable
private fun TaskButton(task: TaskKind, state: AppState, dispatch: (AppAction) -> Unit) {
    val runtime = state.runtimes[task] ?: RuntimeState.NOT_INSTALLED
    Button(
        onClick = { dispatch(AppAction.StartTask(task)) },
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
