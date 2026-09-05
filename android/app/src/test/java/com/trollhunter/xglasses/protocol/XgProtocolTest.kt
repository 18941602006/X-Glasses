package com.trollhunter.xglasses.protocol

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class XgProtocolTest {
    @Test
    fun matchesPythonGoldenVector() {
        val packet = XgPacket(PacketKind.STATUS, 1uL, 2u, 3uL, "abc".encodeToByteArray())
        val expected = hex(
            "5847303301050000010000000000000002000000030000000000000003000000" +
                "26184fbc616263c2412435",
        )
        assertArrayEquals(expected, encodePacket(packet))
        assertEquals(listOf(packet), XgDecoder().feed(expected, 0))
    }

    @Test
    fun handlesEverySplitAndRejectsCorruption() {
        val packet = XgPacket(PacketKind.STATUS, 7uL, 1u, 9uL, byteArrayOf(1, 2, 3))
        val wire = encodePacket(packet)
        for (split in 0..wire.size) {
            val decoder = XgDecoder()
            val output = decoder.feed(wire.copyOfRange(0, split), 0) +
                decoder.feed(wire.copyOfRange(split, wire.size), 1)
            assertEquals(listOf(packet), output)
        }
        val bad = wire.copyOf().also { it[36] = (it[36].toInt() xor 0x80).toByte() }
        val decoder = XgDecoder()
        assertEquals(listOf(packet), decoder.feed(bad + wire, 0))
        assertTrue(decoder.badPayloads > 0)
    }

    @Test
    fun partialPacketExpiresAndRecovers() {
        val packet = XgPacket(PacketKind.STATUS, 7uL, 1u, 9uL, byteArrayOf())
        val wire = encodePacket(packet)
        val decoder = XgDecoder()
        assertEquals(emptyList<XgPacket>(), decoder.feed(wire.copyOfRange(0, 20), 0))
        decoder.feed(byteArrayOf(), XG_PARTIAL_TIMEOUT_NS)
        assertEquals(listOf(packet), decoder.feed(wire, XG_PARTIAL_TIMEOUT_NS + 1))
        assertEquals(1, decoder.timeouts)
    }

    private fun hex(value: String): ByteArray =
        value.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
}
