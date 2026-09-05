// SPDX-License-Identifier: MIT
#include "xg_protocol.h"

#include <string.h>

static const uint8_t k_magic[4] = {'X', 'G', '0', '3'};

static uint16_t get16(const uint8_t *p) { return (uint16_t)p[0] | (uint16_t)p[1] << 8; }
static uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static uint64_t get64(const uint8_t *p) { return (uint64_t)get32(p) | (uint64_t)get32(p + 4) << 32; }
static void put16(uint8_t *p, uint16_t v) { p[0] = v; p[1] = v >> 8; }
static void put32(uint8_t *p, uint32_t v) {
    p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24;
}
static void put64(uint8_t *p, uint64_t v) { put32(p, v); put32(p + 4, v >> 32); }

uint32_t xg_crc32(const uint8_t *data, size_t length) {
    uint32_t crc = UINT32_MAX;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (unsigned bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

size_t xg_encode(uint8_t *out, size_t cap, const xg_packet_t *packet) {
    if (!out || !packet || !packet->session_id || packet->payload_len > XG_MAX_PAYLOAD ||
        (packet->payload_len && !packet->payload)) return 0;
    const size_t size = XG_HEADER_SIZE + packet->payload_len + 4;
    if (cap < size || packet->kind < XG_JPEG || packet->kind > XG_CLOCK) return 0;
    memcpy(out, k_magic, 4); out[4] = XG_VERSION; out[5] = packet->kind; put16(out + 6, 0);
    put64(out + 8, packet->session_id); put32(out + 16, packet->sequence);
    put64(out + 20, packet->capture_us); put32(out + 28, packet->payload_len);
    put32(out + 32, xg_crc32(out, 32));
    if (packet->payload_len) memcpy(out + XG_HEADER_SIZE, packet->payload, packet->payload_len);
    put32(out + XG_HEADER_SIZE + packet->payload_len, xg_crc32(packet->payload, packet->payload_len));
    return size;
}

void xg_parser_reset(xg_parser_t *parser) { memset(parser, 0, sizeof(*parser)); }

static void drop(xg_parser_t *p) {
    memmove(p->buffer, p->buffer + 1, --p->length);
    p->discarded++;
    p->partial_active = false;
}

static void process(xg_parser_t *p, uint64_t now, xg_packet_cb_t cb, void *ctx) {
    while (p->length) {
        if (p->length < 4) break;
        if (memcmp(p->buffer, k_magic, 4)) { drop(p); continue; }
        if (p->length < XG_HEADER_SIZE) break;
        const uint32_t payload_len = get32(p->buffer + 28);
        const bool bad = p->buffer[4] != XG_VERSION || p->buffer[5] < XG_JPEG ||
            p->buffer[5] > XG_CLOCK || get16(p->buffer + 6) || !get64(p->buffer + 8) ||
            payload_len > XG_MAX_PAYLOAD || get32(p->buffer + 32) != xg_crc32(p->buffer, 32);
        if (bad) { p->bad_headers++; drop(p); continue; }
        const size_t wire = XG_HEADER_SIZE + payload_len + 4;
        if (p->length < wire) break;
        if (get32(p->buffer + XG_HEADER_SIZE + payload_len) !=
            xg_crc32(p->buffer + XG_HEADER_SIZE, payload_len)) {
            p->bad_payloads++; drop(p); continue;
        }
        const xg_packet_t packet = {.kind = p->buffer[5], .session_id = get64(p->buffer + 8),
            .sequence = get32(p->buffer + 16), .capture_us = get64(p->buffer + 20),
            .payload = p->buffer + XG_HEADER_SIZE, .payload_len = payload_len};
        cb(&packet, ctx);
        memmove(p->buffer, p->buffer + wire, p->length - wire);
        p->length -= wire;
        p->partial_active = false;
    }
    if (p->length && !p->partial_active) {
        p->partial_since_us = now;
        p->partial_active = true;
    }
}

void xg_parser_feed(xg_parser_t *p, const uint8_t *data, size_t length,
                    uint64_t now, xg_packet_cb_t cb, void *ctx) {
    if (!p || (!data && length) || !cb) return;
    if (p->partial_active && now >= p->partial_since_us &&
        now - p->partial_since_us >= XG_PARTIAL_TIMEOUT_US) {
        p->timeouts++; drop(p); process(p, now, cb, ctx);
    }
    for (size_t i = 0; i < length; ++i) {
        if (p->length == XG_MAX_WIRE) drop(p);
        p->buffer[p->length++] = data[i]; process(p, now, cb, ctx);
    }
}

void xg_parser_tick(xg_parser_t *p, uint64_t now, xg_packet_cb_t cb, void *ctx) {
    xg_parser_feed(p, NULL, 0, now, cb, ctx);
}
