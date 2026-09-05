package com.trollhunter.xglasses.usb

import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.hardware.usb.UsbConstants
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbDeviceConnection
import android.hardware.usb.UsbEndpoint
import android.hardware.usb.UsbInterface
import android.hardware.usb.UsbManager
import android.os.Build

data class UsbDeviceSummary(
    val deviceId: Int,
    val vendorId: Int,
    val productId: Int,
    val productName: String?,
)

sealed interface UsbSessionResult {
    data class PermissionRequired(val deviceId: Int) : UsbSessionResult
    data class Ready(val transport: UsbBulkTransport) : UsbSessionResult
    data class Failed(val reason: String) : UsbSessionResult
}

class UsbSessionManager(private val context: Context) : AutoCloseable {
    private val manager = context.getSystemService(UsbManager::class.java)
    private val permissionAction = "${context.packageName}.USB_PERMISSION"
    private var permissionReceiver: BroadcastReceiver? = null
    private var receiverRegistered = false
    private var connection: UsbDeviceConnection? = null

    fun availableDevices(): List<UsbDeviceSummary> = manager.deviceList.values.map { device ->
        UsbDeviceSummary(
            device.deviceId,
            device.vendorId,
            device.productId,
            device.productName,
        )
    }.sortedBy { it.deviceId }

    fun register(
        onPermission: (deviceId: Int, granted: Boolean) -> Unit,
        onDetached: (deviceId: Int) -> Unit,
    ) {
        if (receiverRegistered) return
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(receiverContext: Context, intent: Intent) {
                val device = intent.usbDevice() ?: return
                if (intent.action == UsbManager.ACTION_USB_DEVICE_DETACHED) {
                    closeConnection()
                    onDetached(device.deviceId)
                    return
                }
                if (intent.action == permissionAction) {
                    onPermission(
                        device.deviceId,
                        intent.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED, false),
                    )
                }
            }
        }
        val filter = IntentFilter(permissionAction).apply {
            addAction(UsbManager.ACTION_USB_DEVICE_DETACHED)
        }
        if (Build.VERSION.SDK_INT >= 33) {
            context.registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            context.registerReceiver(receiver, filter)
        }
        permissionReceiver = receiver
        receiverRegistered = true
    }

    fun requestPermission(deviceId: Int): UsbSessionResult {
        val device = findDevice(deviceId) ?: return UsbSessionResult.Failed("device_not_found")
        if (manager.hasPermission(device)) return open(device)
        val intent = PendingIntent.getBroadcast(
            context,
            deviceId,
            Intent(permissionAction).setPackage(context.packageName),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE,
        )
        manager.requestPermission(device, intent)
        return UsbSessionResult.PermissionRequired(deviceId)
    }

    fun openAuthorized(deviceId: Int): UsbSessionResult {
        val device = findDevice(deviceId) ?: return UsbSessionResult.Failed("device_not_found")
        if (!manager.hasPermission(device)) return UsbSessionResult.PermissionRequired(deviceId)
        return open(device)
    }

    private fun findDevice(deviceId: Int): UsbDevice? =
        manager.deviceList.values.firstOrNull { it.deviceId == deviceId }

    private fun open(device: UsbDevice): UsbSessionResult {
        closeConnection()
        val endpoints = findBulkEndpoints(device)
            ?: return UsbSessionResult.Failed("bulk_endpoints_missing")
        val opened = manager.openDevice(device) ?: return UsbSessionResult.Failed("open_failed")
        if (!opened.claimInterface(endpoints.usbInterface, true)) {
            opened.close()
            return UsbSessionResult.Failed("claim_failed")
        }
        connection = opened
        return UsbSessionResult.Ready(
            UsbBulkTransport(
                device.deviceId,
                opened,
                endpoints.usbInterface,
                endpoints.input,
                endpoints.output,
            ),
        )
    }

    private fun findBulkEndpoints(device: UsbDevice): Endpoints? {
        for (interfaceIndex in 0 until device.interfaceCount) {
            val usbInterface = device.getInterface(interfaceIndex)
            var input: UsbEndpoint? = null
            var output: UsbEndpoint? = null
            for (endpointIndex in 0 until usbInterface.endpointCount) {
                val endpoint = usbInterface.getEndpoint(endpointIndex)
                if (endpoint.type != UsbConstants.USB_ENDPOINT_XFER_BULK) continue
                if (endpoint.direction == UsbConstants.USB_DIR_IN) input = endpoint
                if (endpoint.direction == UsbConstants.USB_DIR_OUT) output = endpoint
            }
            if (input != null && output != null) {
                return Endpoints(usbInterface, input, output)
            }
        }
        return null
    }

    private fun closeConnection() {
        connection?.close()
        connection = null
    }

    override fun close() {
        closeConnection()
        permissionReceiver?.let { receiver ->
            if (receiverRegistered) context.unregisterReceiver(receiver)
        }
        permissionReceiver = null
        receiverRegistered = false
    }

    private fun Intent.usbDevice(): UsbDevice? = if (Build.VERSION.SDK_INT >= 33) {
        getParcelableExtra(UsbManager.EXTRA_DEVICE, UsbDevice::class.java)
    } else {
        @Suppress("DEPRECATION")
        getParcelableExtra(UsbManager.EXTRA_DEVICE)
    }

    private data class Endpoints(
        val usbInterface: UsbInterface,
        val input: UsbEndpoint,
        val output: UsbEndpoint,
    )
}

class UsbBulkTransport internal constructor(
    val deviceId: Int,
    private val connection: UsbDeviceConnection,
    private val usbInterface: UsbInterface,
    private val input: UsbEndpoint,
    private val output: UsbEndpoint,
) : AutoCloseable {
    fun read(buffer: ByteArray, timeoutMs: Int): Int {
        require(buffer.isNotEmpty() && buffer.size <= 4096)
        require(timeoutMs in 1..1000)
        return connection.bulkTransfer(input, buffer, buffer.size, timeoutMs)
    }

    fun write(buffer: ByteArray, timeoutMs: Int): Int {
        require(buffer.isNotEmpty() && buffer.size <= 4096)
        require(timeoutMs in 1..1000)
        return connection.bulkTransfer(output, buffer, buffer.size, timeoutMs)
    }

    override fun close() {
        connection.releaseInterface(usbInterface)
        connection.close()
    }
}
