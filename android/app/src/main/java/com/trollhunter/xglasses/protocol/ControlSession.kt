package com.trollhunter.xglasses.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

const val CAP_CLOCK = 1
const val CAP_TOF = 1 shl 1
const val CAP_IMU = 1 shl 2
const val CAP_BUTTON = 1 shl 3
const val CAP_CAMERA = 1 shl 4
const val CAP_HAPTIC = 1 shl 5
const val ALL_CAPABILITIES = CAP_CLOCK or CAP_TOF or CAP_IMU or CAP_BUTTON or CAP_CAMERA or CAP_HAPTIC
const val REQUIRED_SAFETY_CAPABILITIES = CAP_CLOCK or CAP_TOF or CAP_CAMERA
const val HANDSHAKE_TIMEOUT_NS = 2_000_000_000L
const val HEARTBEAT_TIMEOUT_NS = 1_500_000_000L

enum class ControlState { DISCONNECTED, HANDSHAKING, READY, FAILED }

data class ControlSnapshot(
    val state: ControlState,
    val reason: String,
    val sessionId: ULong? = null,
    val bootId: ULong? = null,
    val capabilities: Int = 0,
)

class ControlSession {
    private var sessionId = 0uL
    private var nonce = 0uL
    private var handshakeDeadlineNs = 0L
    private var lastHeartbeatNs = 0L
    private var lastInboundSequence: UInt? = null
    private var snapshot = ControlSnapshot(ControlState.DISCONNECTED, "not_connected")

    fun begin(session: ULong, hostNonce: ULong, nowNs: Long): XgPacket {
        require(session != 0uL && hostNonce != 0uL && nowNs >= 0)
        sessionId = session
        nonce = hostNonce
        handshakeDeadlineNs = nowNs + HANDSHAKE_TIMEOUT_NS
        lastHeartbeatNs = 0
        lastInboundSequence = null
        snapshot = ControlSnapshot(ControlState.HANDSHAKING, "welcome_pending", session)
        val payload = ByteBuffer.allocate(9).order(ByteOrder.LITTLE_ENDIAN)
            .put(1)
            .putLong(hostNonce.toLong())
            .array()
        return XgPacket(PacketKind.STATUS, session, 0u, 0uL, payload)
    }

    fun snapshot(): ControlSnapshot = snapshot

    fun accept(packet: XgPacket, nowNs: Long): ControlSnapshot {
        require(nowNs >= 0)
        if (snapshot.state !in setOf(ControlState.HANDSHAKING, ControlState.READY)) return snapshot
        if (packet.sessionId != sessionId || !acceptSequence(packet.sequence)) return snapshot
        return when (snapshot.state) {
            ControlState.HANDSHAKING -> acceptWelcome(packet, nowNs)
            ControlState.READY -> acceptReadyPacket(packet, nowNs)
            else -> snapshot
        }
    }

    fun tick(nowNs: Long): ControlSnapshot {
        require(nowNs >= 0)
        if (snapshot.state == ControlState.HANDSHAKING && nowNs >= handshakeDeadlineNs) {
            fail("handshake_timeout")
        } else if (
            snapshot.state == ControlState.READY &&
            nowNs - lastHeartbeatNs >= HEARTBEAT_TIMEOUT_NS
        ) {
            fail("heartbeat_timeout")
        }
        return snapshot
    }

    fun disconnect(reason: String = "disconnected"): ControlSnapshot {
        snapshot = ControlSnapshot(ControlState.DISCONNECTED, reason)
        sessionId = 0uL
        nonce = 0uL
        lastInboundSequence = null
        return snapshot
    }

    private fun acceptWelcome(packet: XgPacket, nowNs: Long): ControlSnapshot {
        if (packet.kind != PacketKind.STATUS || packet.payload.size != 21) return snapshot
        val payload = ByteBuffer.wrap(packet.payload).order(ByteOrder.LITTLE_ENDIAN)
        val subtype = payload.get().toInt() and 0xff
        val echoedNonce = payload.long.toULong()
        val bootId = payload.long.toULong()
        val capabilities = payload.int
        if (
            subtype != 2 || echoedNonce != nonce || bootId == 0uL ||
            capabilities and ALL_CAPABILITIES.inv() != 0
        ) {
            return fail("welcome_invalid")
        }
        if (capabilities and REQUIRED_SAFETY_CAPABILITIES != REQUIRED_SAFETY_CAPABILITIES) {
            return fail("required_capability_missing")
        }
        lastHeartbeatNs = nowNs
        snapshot = ControlSnapshot(
            ControlState.READY,
            "connected",
            sessionId,
            bootId,
            capabilities,
        )
        return snapshot
    }

    private fun acceptReadyPacket(packet: XgPacket, nowNs: Long): ControlSnapshot {
        if (packet.kind != PacketKind.STATUS || packet.payload.size != 9) return snapshot
        val payload = ByteBuffer.wrap(packet.payload).order(ByteOrder.LITTLE_ENDIAN)
        val subtype = payload.get().toInt() and 0xff
        val bootId = payload.long.toULong()
        if (subtype != 3) return snapshot
        if (bootId != snapshot.bootId) return fail("boot_changed")
        lastHeartbeatNs = nowNs
        return snapshot
    }

    private fun acceptSequence(current: UInt): Boolean {
        val previous = lastInboundSequence
        if (previous == null) {
            lastInboundSequence = current
            return true
        }
        val delta = current - previous
        if (delta == 0u || delta >= 0x80000000u) return false
        lastInboundSequence = current
        return true
    }

    private fun fail(reason: String): ControlSnapshot {
        snapshot = ControlSnapshot(ControlState.FAILED, reason)
        return snapshot
    }
}
