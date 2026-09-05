package com.trollhunter.xglasses.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.zip.CRC32

private val MAGIC = "XG03".encodeToByteArray()
const val XG_VERSION = 1
const val XG_HEADER_SIZE = 36
const val XG_MAX_PAYLOAD = 4096
const val XG_MAX_READ = 65536
const val XG_MAX_WIRE = XG_HEADER_SIZE + XG_MAX_PAYLOAD + 4
const val XG_PARTIAL_TIMEOUT_NS = 500_000_000L

enum class PacketKind(val wire: Int) {
    JPEG(1), TOF(2), IMU(3), BUTTON(4), STATUS(5), COMMAND(6), ACK(7), CLOCK(8);

    companion object {
        fun fromWire(value: Int): PacketKind? = entries.firstOrNull { it.wire == value }
    }
}

data class XgPacket(
    val kind: PacketKind,
    val sessionId: ULong,
    val sequence: UInt,
    val captureUs: ULong,
    val payload: ByteArray,
) {
    init {
        require(sessionId != 0uL)
        require(payload.size <= XG_MAX_PAYLOAD)
    }

    override fun equals(other: Any?): Boolean = other is XgPacket &&
        kind == other.kind && sessionId == other.sessionId && sequence == other.sequence &&
        captureUs == other.captureUs && payload.contentEquals(other.payload)

    override fun hashCode(): Int = 31 * kind.hashCode() + payload.contentHashCode()
}

fun encodePacket(packet: XgPacket): ByteArray {
    val base = ByteBuffer.allocate(32).order(ByteOrder.LITTLE_ENDIAN)
        .put(MAGIC)
        .put(XG_VERSION.toByte())
        .put(packet.kind.wire.toByte())
        .putShort(0)
        .putLong(packet.sessionId.toLong())
        .putInt(packet.sequence.toInt())
        .putLong(packet.captureUs.toLong())
        .putInt(packet.payload.size)
        .array()
    return ByteBuffer.allocate(XG_HEADER_SIZE + packet.payload.size + 4)
        .order(ByteOrder.LITTLE_ENDIAN)
        .put(base)
        .putInt(crc32(base).toInt())
        .put(packet.payload)
        .putInt(crc32(packet.payload).toInt())
        .array()
}

class XgDecoder {
    private var buffer = ByteArray(0)
    private var partialSinceNs: Long? = null
    private var lastNowNs = -1L
    var badHeaders: Int = 0
        private set
    var badPayloads: Int = 0
        private set
    var timeouts: Int = 0
        private set
    var discardedBytes: Long = 0
        private set

    fun reset() {
        buffer = ByteArray(0)
        partialSinceNs = null
        lastNowNs = -1L
    }

    fun feed(data: ByteArray, nowNs: Long): List<XgPacket> {
        require(data.size <= XG_MAX_READ && nowNs >= 0 && nowNs >= lastNowNs)
        lastNowNs = nowNs
        partialSinceNs?.let { started ->
            if (nowNs - started >= XG_PARTIAL_TIMEOUT_NS) {
                timeouts += 1
                drop(1)
            }
        }
        val packets = drain(nowNs).toMutableList()
        data.asList().chunked(XG_MAX_WIRE).forEach { chunk ->
            buffer += chunk.toByteArray()
            packets += drain(nowNs)
        }
        check(buffer.size < XG_MAX_WIRE)
        return packets
    }

    private fun drain(nowNs: Long): List<XgPacket> {
        val packets = mutableListOf<XgPacket>()
        while (buffer.isNotEmpty()) {
            val magicAt = findMagic()
            if (magicAt < 0) {
                if (buffer.size > MAGIC.size - 1) drop(buffer.size - MAGIC.size + 1)
                break
            }
            if (magicAt > 0) drop(magicAt)
            if (buffer.size < XG_HEADER_SIZE) break
            val base = buffer.copyOfRange(0, 32)
            val header = ByteBuffer.wrap(base).order(ByteOrder.LITTLE_ENDIAN)
            header.position(4)
            val version = header.get().toInt() and 0xff
            val kind = PacketKind.fromWire(header.get().toInt() and 0xff)
            val flags = header.short.toInt() and 0xffff
            val session = header.long.toULong()
            val sequence = header.int.toUInt()
            val capture = header.long.toULong()
            val length = header.int
            val expectedHeaderCrc = littleUInt(buffer, 32)
            if (
                crc32(base) != expectedHeaderCrc || version != XG_VERSION || kind == null ||
                flags != 0 || session == 0uL || length !in 0..XG_MAX_PAYLOAD
            ) {
                badHeaders += 1
                drop(1)
                continue
            }
            val wireSize = XG_HEADER_SIZE + length + 4
            if (buffer.size < wireSize) break
            val payload = buffer.copyOfRange(XG_HEADER_SIZE, XG_HEADER_SIZE + length)
            if (crc32(payload) != littleUInt(buffer, XG_HEADER_SIZE + length)) {
                badPayloads += 1
                drop(1)
                continue
            }
            packets += XgPacket(kind, session, sequence, capture, payload)
            buffer = buffer.copyOfRange(wireSize, buffer.size)
            partialSinceNs = null
        }
        if (buffer.isNotEmpty() && partialSinceNs == null) partialSinceNs = nowNs
        return packets
    }

    private fun findMagic(): Int {
        for (index in 0..buffer.size - MAGIC.size) {
            if (MAGIC.indices.all { offset -> buffer[index + offset] == MAGIC[offset] }) return index
        }
        return -1
    }

    private fun drop(count: Int) {
        buffer = buffer.copyOfRange(count.coerceAtMost(buffer.size), buffer.size)
        discardedBytes += count
        partialSinceNs = null
    }
}

private fun crc32(data: ByteArray): UInt = CRC32().run {
    update(data)
    value.toUInt()
}

private fun littleUInt(data: ByteArray, offset: Int): UInt =
    ByteBuffer.wrap(data, offset, 4).order(ByteOrder.LITTLE_ENDIAN).int.toUInt()
