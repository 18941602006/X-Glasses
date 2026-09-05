package com.trollhunter.xglasses

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.core.content.ContextCompat
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.trollhunter.xglasses.domain.AppAction
import com.trollhunter.xglasses.domain.AppReducer
import com.trollhunter.xglasses.domain.AppState
import com.trollhunter.xglasses.domain.UsbState
import com.trollhunter.xglasses.domain.TaskKind
import com.trollhunter.xglasses.domain.TaskState
import com.trollhunter.xglasses.navigation.NavigationCoordinator
import com.trollhunter.xglasses.navigation.NavigationProviderFactory
import com.trollhunter.xglasses.navigation.NavigationUiState
import com.trollhunter.xglasses.protocol.ControlSnapshot
import com.trollhunter.xglasses.protocol.ControlState
import com.trollhunter.xglasses.runtime.ModelRuntimeRegistry
import com.trollhunter.xglasses.ui.XGlassesApp
import com.trollhunter.xglasses.usb.AndroidHostLink
import com.trollhunter.xglasses.usb.UsbSessionResult
import com.trollhunter.xglasses.usb.UsbSessionManager

class MainActivity : ComponentActivity() {
    private var state by mutableStateOf(AppState())
    private lateinit var usbSessions: UsbSessionManager
    private var hostLink: AndroidHostLink? = null
    private var navigationState by mutableStateOf(NavigationUiState())
    private var navigationVisible by mutableStateOf(false)
    private lateinit var navigation: NavigationCoordinator
    private val locationPermission = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { result ->
        val granted = result[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
            result[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        navigation.setPermission(granted)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ModelRuntimeRegistry().inspect().forEach { (task, runtime) ->
            dispatch(AppAction.RuntimeChanged(task, runtime))
        }
        navigation = NavigationCoordinator(
            applicationContext,
            NavigationProviderFactory.createOrNull(),
            { next -> runOnUiThread { navigationState = next } },
            { reason -> runOnUiThread { failNavigationTask(reason) } },
            { runOnUiThread { completeNavigationTask() } },
        )
        navigationState = navigation.state()
        usbSessions = UsbSessionManager(this)
        usbSessions.register(
            onPermission = { deviceId, granted ->
                if (granted) openAuthorized(deviceId)
                else dispatch(AppAction.UsbChanged(UsbState.FAILED))
            },
            onDetached = { deviceId ->
                if (state.usbDeviceId == deviceId) {
                    hostLink?.close()
                    hostLink = null
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
                navigationVisible = navigationVisible,
                navigationState = navigationState,
                openNavigation = ::openNavigation,
                closeNavigation = { navigationVisible = false },
                updateDestinationQuery = navigation::setQuery,
                searchDestination = navigation::search,
                selectDestination = navigation::select,
                startNavigation = ::startMapNavigation,
                stopNavigation = ::stopMapNavigation,
            )
        }
    }

    override fun onStart() {
        super.onStart()
        dispatch(AppAction.ForegroundChanged(true))
        if (navigationVisible && navigationState.providerConfigured) navigation.resumeLocation()
    }

    override fun onStop() {
        navigation.pauseLocation()
        hostLink?.close()
        hostLink = null
        dispatch(AppAction.ForegroundChanged(false))
        super.onStop()
    }

    override fun onDestroy() {
        navigation.close()
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
        when (result) {
            is UsbSessionResult.PermissionRequired -> {
                dispatch(AppAction.UsbChanged(UsbState.PERMISSION_REQUIRED, deviceId))
            }
            is UsbSessionResult.Ready -> {
                hostLink?.close()
                hostLink = AndroidHostLink(result.transport) { snapshot ->
                    runOnUiThread { onControlState(snapshot, deviceId) }
                }.also { it.start() }
            }
            is UsbSessionResult.Failed -> {
                dispatch(AppAction.UsbChanged(UsbState.FAILED))
            }
        }
    }

    private fun onControlState(snapshot: ControlSnapshot, deviceId: Int) {
        val state = when (snapshot.state) {
            ControlState.DISCONNECTED -> UsbState.DISCONNECTED
            ControlState.HANDSHAKING -> UsbState.TRANSPORT_OPEN
            ControlState.READY -> UsbState.READY
            ControlState.FAILED -> UsbState.FAILED
        }
        dispatch(AppAction.UsbChanged(state, deviceId))
    }

    private fun dispatch(action: AppAction) {
        val navigationMustStop = state.activeTask == TaskKind.NAVIGATION && (
            action == AppAction.CancelCurrentTask ||
                action is AppAction.UsbChanged && action.state != UsbState.READY ||
                action is AppAction.ForegroundChanged && !action.foreground
            )
        if (navigationMustStop && ::navigation.isInitialized) {
            navigation.stop()
        }
        state = AppReducer.reduce(state, action)
    }

    private fun startMapNavigation() {
        dispatch(AppAction.StartTask(TaskKind.NAVIGATION))
        navigation.start(
            state.usbState == UsbState.READY && state.activeTask == TaskKind.NAVIGATION,
        )
    }

    private fun stopMapNavigation() {
        navigation.stop()
        if (state.activeTask == TaskKind.NAVIGATION) dispatch(AppAction.CancelCurrentTask)
    }

    private fun failNavigationTask(reason: String) {
        val running = state.tasks[TaskKind.NAVIGATION] as? TaskState.Running ?: return
        dispatch(AppAction.TaskFailed(running.requestId, reason))
    }

    private fun completeNavigationTask() {
        val running = state.tasks[TaskKind.NAVIGATION] as? TaskState.Running ?: return
        dispatch(AppAction.TaskCompleted(running.requestId))
    }

    private fun openNavigation() {
        navigationVisible = true
        if (!navigationState.providerConfigured) return
        val granted = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_FINE_LOCATION,
        ) == PackageManager.PERMISSION_GRANTED || ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_COARSE_LOCATION,
        ) == PackageManager.PERMISSION_GRANTED
        navigation.setPermission(granted)
        if (!granted) {
            locationPermission.launch(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION,
                ),
            )
        }
    }
}
