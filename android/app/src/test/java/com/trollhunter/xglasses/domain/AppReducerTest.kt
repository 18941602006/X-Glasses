package com.trollhunter.xglasses.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AppReducerTest {
    @Test
    fun usbDeviceChoicesAreSortedAndDeduplicated() {
        val result = AppReducer.reduce(AppState(), AppAction.UsbDevicesChanged(listOf(5, 2, 5)))
        assertEquals(listOf(2, 5), result.availableUsbDeviceIds)
    }

    @Test
    fun unavailableRuntimeCannotStart() {
        val connected = AppReducer.reduce(AppState(), AppAction.UsbChanged(UsbState.READY, 3))
        val result = AppReducer.reduce(connected, AppAction.StartTask(TaskKind.DIALOGUE))
        assertNull(result.activeTask)
        assertTrue(result.safetyMonitoringActive)
    }

    @Test
    fun bulkEndpointAloneDoesNotEnableSafetyMonitoring() {
        val state = AppReducer.reduce(
            AppState(),
            AppAction.UsbChanged(UsbState.TRANSPORT_OPEN, 3),
        )
        assertFalse(state.safetyMonitoringActive)
        assertNull(state.activeTask)
    }

    @Test
    fun cancellingTaskDoesNotDisableSafetyMonitoring() {
        var state = AppReducer.reduce(AppState(), AppAction.UsbChanged(UsbState.READY, 3))
        state = AppReducer.reduce(
            state,
            AppAction.RuntimeChanged(TaskKind.READ_TEXT, RuntimeState.AVAILABLE),
        )
        state = AppReducer.reduce(state, AppAction.StartTask(TaskKind.READ_TEXT))
        state = AppReducer.reduce(state, AppAction.CancelCurrentTask)
        assertNull(state.activeTask)
        assertTrue(state.safetyMonitoringActive)
        assertEquals(TaskState.Cancelled, state.tasks[TaskKind.READ_TEXT])
    }

    @Test
    fun disconnectCancelsTaskAndSafetyBecomesUnavailable() {
        var state = AppReducer.reduce(AppState(), AppAction.UsbChanged(UsbState.READY, 3))
        state = AppReducer.reduce(
            state,
            AppAction.RuntimeChanged(TaskKind.NAVIGATION, RuntimeState.AVAILABLE),
        )
        state = AppReducer.reduce(state, AppAction.StartTask(TaskKind.NAVIGATION))
        state = AppReducer.reduce(state, AppAction.UsbChanged(UsbState.DISCONNECTED))
        assertFalse(state.safetyMonitoringActive)
        assertNull(state.activeTask)
        assertEquals(TaskState.Cancelled, state.tasks[TaskKind.NAVIGATION])
    }
}
