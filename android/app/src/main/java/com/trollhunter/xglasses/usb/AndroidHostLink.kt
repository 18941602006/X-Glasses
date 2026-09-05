package com.trollhunter.xglasses.usb

import com.trollhunter.xglasses.protocol.ControlSession
import com.trollhunter.xglasses.protocol.ControlSnapshot
import com.trollhunter.xglasses.protocol.ControlState
import com.trollhunter.xglasses.protocol.XgDecoder
import com.trollhunter.xglasses.protocol.encodePacket
import java.security.SecureRandom
import java.util.concurrent.atomic.AtomicBoolean

class AndroidHostLink(
    private val transport: UsbBulkTransport,
    private val onState: (ControlSnapshot) -> Unit,
) : AutoCloseable {
    private val running = AtomicBoolean(false)
    private val decoder = XgDecoder()
    private val control = ControlSession()
    private var worker: Thread? = null

    fun start() {
        check(running.compareAndSet(false, true)) { "host link already started" }
        val random = SecureRandom()
        val session = random.nextNonzeroULong()
        val nonce = random.nextNonzeroULong()
        val hello = control.begin(session, nonce, System.nanoTime())
        onState(control.snapshot())
        if (!writeAll(encodePacket(hello))) {
            running.set(false)
            onState(control.disconnect("hello_write_failed"))
            transport.close()
            return
        }
        worker = Thread({ readLoop() }, "xg-usb-${transport.deviceId}").apply {
            isDaemon = true
            start()
        }
    }

    private fun readLoop() {
        val chunk = ByteArray(4096)
        var lastSnapshot = control.snapshot()
        try {
            while (running.get()) {
                val count = transport.read(chunk, 100)
                val nowNs = System.nanoTime()
                val packets = decoder.feed(
                    if (count > 0) chunk.copyOf(count) else byteArrayOf(),
                    nowNs,
                )
                packets.forEach { packet -> control.accept(packet, nowNs) }
                val current = control.tick(nowNs)
                if (current != lastSnapshot) {
                    lastSnapshot = current
                    onState(current)
                }
                if (current.state in setOf(ControlState.FAILED, ControlState.DISCONNECTED)) {
                    running.set(false)
                }
            }
        } catch (_: Exception) {
            onState(control.disconnect("transport_failure"))
        } finally {
            running.set(false)
            transport.close()
        }
    }

    @Synchronized
    private fun writeAll(bytes: ByteArray): Boolean {
        var offset = 0
        while (offset < bytes.size && running.get()) {
            val size = minOf(4096, bytes.size - offset)
            val written = transport.write(bytes.copyOfRange(offset, offset + size), 500)
            if (written <= 0 || written > size) return false
            offset += written
        }
        return offset == bytes.size
    }

    override fun close() {
        if (running.getAndSet(false)) {
            transport.close()
        }
        worker = null
        onState(control.disconnect())
    }

    private fun SecureRandom.nextNonzeroULong(): ULong {
        var value = nextLong().toULong()
        while (value == 0uL) value = nextLong().toULong()
        return value
    }
}
