// SPDX-License-Identifier: MIT
#include "xg_controller.h"

#include <string.h>

enum { STATUS_HELLO = 1, STATUS_WELCOME = 2, STATUS_HEARTBEAT = 3 };
enum { OP_START = 1, OP_STOP = 2, OP_HAPTIC = 3, OP_CANCEL = 4 };
enum { ACK_APPLIED = 1, ACK_REJECTED = 2, ACK_EXPIRED = 3 };

static uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static uint64_t get64(const uint8_t *p) { return (uint64_t)get32(p) | (uint64_t)get32(p + 4) << 32; }
static uint16_t get16(const uint8_t *p) { return (uint16_t)p[0] | (uint16_t)p[1] << 8; }
static void put16(uint8_t *p, uint16_t v) { p[0] = v; p[1] = v >> 8; }
static void put32(uint8_t *p, uint32_t v) { p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24; }
static void put64(uint8_t *p, uint64_t v) { put32(p, v); put32(p + 4, v >> 32); }

static bool emit(xg_controller_t *c, uint8_t kind, uint64_t capture_us,
                 const uint8_t *payload, uint32_t length) {
    if (!c->ready || !c->transmit) return false;
    const xg_packet_t packet = {.kind = kind, .session_id = c->session_id,
        .sequence = c->tx_sequence++, .capture_us = capture_us,
        .payload = payload, .payload_len = length};
    return c->transmit(&packet, c->context);
}

static bool newer32(uint32_t value, uint32_t old) {
    const uint32_t difference = value - old;
    return difference && difference < UINT32_C(0x80000000);
}

void xg_controller_init(xg_controller_t *c, uint64_t boot_id,
                        uint32_t capabilities, xg_tx_cb_t transmit,
                        xg_apply_cb_t apply, void *context) {
    memset(c, 0, sizeof(*c));
    c->boot_id = boot_id ? boot_id : 1;
    c->capabilities = capabilities;
    c->transmit = transmit;
    c->apply = apply;
    c->context = context;
}

void xg_controller_detach(xg_controller_t *c) {
    c->ready = false;
    c->session_id = c->host_nonce = c->max_request_id = 0;
    c->tx_sequence = c->rx_sequence = 0;
    c->have_rx_sequence = false;
    c->cache_next = 0;
    memset(c->cache, 0, sizeof(c->cache));
}

static void welcome(xg_controller_t *c) {
    uint8_t payload[21] = {STATUS_WELCOME};
    put64(payload + 1, c->host_nonce);
    put64(payload + 9, c->boot_id);
    put32(payload + 17, c->capabilities);
    (void)emit(c, XG_STATUS, 0, payload, sizeof(payload));
}

static void begin(xg_controller_t *c, const xg_packet_t *packet) {
    if (packet->payload_len != 9 || packet->payload[0] != STATUS_HELLO || !packet->session_id) return;
    xg_controller_detach(c);
    c->ready = true;
    c->session_id = packet->session_id;
    c->host_nonce = get64(packet->payload + 1);
    if (!c->host_nonce) { xg_controller_detach(c); return; }
    c->rx_sequence = packet->sequence;
    c->have_rx_sequence = true;
    welcome(c);
}

static void acknowledge(xg_controller_t *c, uint64_t request, uint8_t opcode, uint8_t result) {
    uint8_t payload[10];
    put64(payload, request); payload[8] = opcode; payload[9] = result;
    (void)emit(c, XG_ACK, 0, payload, sizeof(payload));
}

static bool declared(const xg_controller_t *c, uint8_t opcode) {
    if (opcode == OP_START) return (c->capabilities & XG_CAP_CAMERA) != 0;
    if (opcode == OP_HAPTIC) return (c->capabilities & XG_CAP_HAPTIC) != 0;
    return opcode == OP_STOP || opcode == OP_CANCEL;
}

static void command(xg_controller_t *c, const xg_packet_t *packet, uint64_t now) {
    if (packet->payload_len != 20) return;
    const uint64_t request = get64(packet->payload);
    const uint8_t opcode = packet->payload[8];
    const uint64_t deadline = get64(packet->payload + 9);
    const uint16_t duration = get16(packet->payload + 17);
    const uint8_t intensity = packet->payload[19];
    const uint32_t fingerprint = xg_crc32(packet->payload, packet->payload_len);
    for (size_t i = 0; i < 8; ++i) {
        if (c->cache[i].request_id == request) {
            acknowledge(c, request, opcode,
                c->cache[i].opcode == opcode && c->cache[i].payload_crc == fingerprint
                    ? c->cache[i].result : ACK_REJECTED);
            return;
        }
    }
    uint8_t result = ACK_REJECTED;
    const bool parameters = opcode == OP_HAPTIC
        ? duration >= 1 && duration <= 500 && intensity >= 1 && deadline
        : duration == 0 && intensity == 0;
    const bool needs_deadline = opcode == OP_START || opcode == OP_HAPTIC;
    if (!request || request <= c->max_request_id || !declared(c, opcode) || !parameters) {
        result = ACK_REJECTED;
    } else if (needs_deadline && (deadline < now || deadline - now > 500000)) {
        result = deadline < now ? ACK_EXPIRED : ACK_REJECTED;
    } else if (!needs_deadline && deadline) {
        result = ACK_REJECTED;
    } else {
        result = c->apply && c->apply(opcode, duration, intensity, c->context)
            ? ACK_APPLIED : ACK_REJECTED;
    }
    if (request > c->max_request_id) c->max_request_id = request;
    xg_ack_cache_t *entry = &c->cache[c->cache_next++ % 8];
    *entry = (xg_ack_cache_t){request, fingerprint, opcode, result};
    acknowledge(c, request, opcode, result);
}

static void clock_response(xg_controller_t *c, const xg_packet_t *packet,
                           uint64_t received_us, uint64_t responding_us) {
    if (!(c->capabilities & XG_CAP_CLOCK) || packet->payload_len != 16) return;
    uint8_t payload[32];
    memcpy(payload, packet->payload, 16);
    put64(payload + 16, received_us);
    put64(payload + 24, responding_us);
    (void)emit(c, XG_CLOCK, responding_us, payload, sizeof(payload));
}

void xg_controller_process(xg_controller_t *c, const xg_packet_t *packet,
                           uint64_t received_us, uint64_t responding_us) {
    if (!c || !packet) return;
    if (packet->kind == XG_STATUS) {
        if (!c->ready || packet->session_id != c->session_id ||
            packet->payload_len != 9 || packet->payload[0] != STATUS_HELLO ||
            get64(packet->payload + 1) != c->host_nonce) begin(c, packet);
        else welcome(c);  // Exact retry is idempotent and does not reset device state.
        return;
    }
    if (!c->ready || packet->session_id != c->session_id || packet->capture_us != 0) return;
    if (c->have_rx_sequence && !newer32(packet->sequence, c->rx_sequence)) return;
    c->rx_sequence = packet->sequence; c->have_rx_sequence = true;
    if (packet->kind == XG_CLOCK) clock_response(c, packet, received_us, responding_us);
    else if (packet->kind == XG_COMMAND) command(c, packet, received_us);
}

void xg_controller_tick(xg_controller_t *c, uint64_t now_us) {
    if (!c || !c->ready || now_us - c->last_heartbeat_us < 500000) return;
    uint8_t payload[9] = {STATUS_HEARTBEAT};
    put64(payload + 1, c->boot_id);
    if (emit(c, XG_STATUS, now_us, payload, sizeof(payload))) c->last_heartbeat_us = now_us;
}
