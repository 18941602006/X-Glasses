package com.trollhunter.xglasses.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder
import org.junit.Assert.assertEquals
import org.junit.Test

class ControlSessionTest {
    @Test
    fun nonceCapabilitiesAndHeartbeatGateReady() {
        val control = ControlSession()
        val hello = control.begin(7uL, 9uL, 0)
        assertEquals(PacketKind.STATUS, hello.kind)
        assertEquals(ControlState.HANDSHAKING, control.snapshot().state)
        val missing = welcome(7uL, 1u, 9uL, 4uL, CAP_CLOCK)
        assertEquals(ControlState.FAILED, control.accept(missing, 1).state)

        val ready = ControlSession()
        ready.begin(7uL, 9uL, 0)
        val capabilities = REQUIRED_SAFETY_CAPABILITIES or CAP_BUTTON
        assertEquals(ControlState.READY, ready.accept(welcome(7uL, 1u, 9uL, 4uL, capabilities), 1).state)
        assertEquals(ControlState.READY, ready.accept(heartbeat(7uL, 2u, 4uL), 2).state)
        assertEquals(ControlState.FAILED, ready.accept(heartbeat(7uL, 3u, 5uL), 3).state)
    }

    @Test
    fun staleNonceWrongSessionDuplicateAndTimeoutNeverReady() {
        val control = ControlSession()
        control.begin(7uL, 9uL, 0)
        val validCaps = REQUIRED_SAFETY_CAPABILITIES
        assertEquals(ControlState.HANDSHAKING, control.accept(welcome(8uL, 1u, 9uL, 4uL, validCaps), 1).state)
        assertEquals(ControlState.FAILED, control.accept(welcome(7uL, 1u, 8uL, 4uL, validCaps), 2).state)

        val timeout = ControlSession()
        timeout.begin(7uL, 9uL, 0)
        assertEquals(ControlState.FAILED, timeout.tick(HANDSHAKE_TIMEOUT_NS).state)
    }

    @Test
    fun sequenceWrapIsAcceptedButDuplicatesAreIgnored() {
        val control = ControlSession()
        control.begin(7uL, 9uL, 0)
        val capabilities = REQUIRED_SAFETY_CAPABILITIES
        assertEquals(ControlState.READY, control.accept(welcome(7uL, UInt.MAX_VALUE, 9uL, 4uL, capabilities), 1).state)
        assertEquals(ControlState.READY, control.accept(heartbeat(7uL, 0u, 4uL), 2).state)
        assertEquals(ControlState.READY, control.accept(heartbeat(7uL, 0u, 5uL), 3).state)
        assertEquals(4uL, control.snapshot().bootId)
    }

    private fun welcome(
        session: ULong,
        sequence: UInt,
        nonce: ULong,
        boot: ULong,
        capabilities: Int,
    ): XgPacket {
        val payload = ByteBuffer.allocate(21).order(ByteOrder.LITTLE_ENDIAN)
            .put(2)
            .putLong(nonce.toLong())
            .putLong(boot.toLong())
            .putInt(capabilities)
            .array()
        return XgPacket(PacketKind.STATUS, session, sequence, 0uL, payload)
    }

    private fun heartbeat(session: ULong, sequence: UInt, boot: ULong): XgPacket {
        val payload = ByteBuffer.allocate(9).order(ByteOrder.LITTLE_ENDIAN)
            .put(3)
            .putLong(boot.toLong())
            .array()
        return XgPacket(PacketKind.STATUS, session, sequence, 0uL, payload)
    }
}
