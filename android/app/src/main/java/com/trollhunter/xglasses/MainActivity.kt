package com.trollhunter.xglasses

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.trollhunter.xglasses.domain.AppAction
import com.trollhunter.xglasses.domain.AppReducer
import com.trollhunter.xglasses.domain.AppState
import com.trollhunter.xglasses.domain.UsbState
import com.trollhunter.xglasses.runtime.ModelRuntimeRegistry
import com.trollhunter.xglasses.ui.XGlassesApp
import com.trollhunter.xglasses.usb.UsbSessionManager
import com.trollhunter.xglasses.usb.UsbSessionResult
import com.trollhunter.xglasses.usb.UsbBulkTransport

class MainActivity : ComponentActivity() {
    private var state by mutableStateOf(AppState())
    private lateinit var usbSessions: UsbSessionManager
    private var usbTransport: UsbBulkTransport? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ModelRuntimeRegistry().inspect().forEach { (task, runtime) ->
            dispatch(AppAction.RuntimeChanged(task, runtime))
        }
        usbSessions = UsbSessionManager(this)
        usbSessions.register(
            onPermission = { deviceId, granted ->
                if (granted) openAuthorized(deviceId)
                else dispatch(AppAction.UsbChanged(UsbState.FAILED))
            },
            onDetached = { deviceId ->
                if (state.usbDeviceId == deviceId) {
                    usbTransport = null
                    dispatch(AppAction.UsbChanged(UsbState.DISCONNECTED))
                }
                refreshUsbDevices()
            },
        )
        refreshUsbDevices()
        setContent {
            XGlassesApp(
                state = state,
                dispatch = ::dispatch,
                refreshUsb = ::refreshUsbDevices,
                connectUsb = ::connectUsb,
            )
        }
    }

    override fun onStart() {
        super.onStart()
        dispatch(AppAction.ForegroundChanged(true))
    }

    override fun onStop() {
        dispatch(AppAction.ForegroundChanged(false))
        super.onStop()
    }

    override fun onDestroy() {
        usbSessions.close()
        super.onDestroy()
    }

    private fun refreshUsbDevices() {
        dispatch(AppAction.UsbDevicesChanged(usbSessions.availableDevices().map { it.deviceId }))
    }

    private fun connectUsb(deviceId: Int) {
        dispatch(
            AppAction.UsbChanged(
                UsbState.CONNECTING,
                deviceId,
            ),
        )
        handleUsbResult(usbSessions.requestPermission(deviceId), deviceId)
    }

    private fun openAuthorized(deviceId: Int) {
        handleUsbResult(usbSessions.openAuthorized(deviceId), deviceId)
    }

    private fun handleUsbResult(result: UsbSessionResult, deviceId: Int) {
        val usbState = when (result) {
            is UsbSessionResult.PermissionRequired -> UsbState.PERMISSION_REQUIRED
            is UsbSessionResult.Ready -> {
                usbTransport = result.transport
                UsbState.TRANSPORT_OPEN
            }
            is UsbSessionResult.Failed -> UsbState.FAILED
        }
        dispatch(AppAction.UsbChanged(usbState, deviceId))
    }

    private fun dispatch(action: AppAction) {
        state = AppReducer.reduce(state, action)
    }
}
