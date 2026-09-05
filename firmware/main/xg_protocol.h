// SPDX-License-Identifier: MIT
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define XG_VERSION 1u
#define XG_MAX_PAYLOAD 4096u
#define XG_HEADER_SIZE 36u
#define XG_MAX_WIRE 4136u
#define XG_PARTIAL_TIMEOUT_US 500000u

typedef enum {
    XG_JPEG = 1, XG_TOF = 2, XG_IMU = 3, XG_BUTTON = 4,
    XG_STATUS = 5, XG_COMMAND = 6, XG_ACK = 7, XG_CLOCK = 8,
} xg_kind_t;

typedef struct {
    uint8_t kind;
    uint64_t session_id;
    uint32_t sequence;
    uint64_t capture_us;
    const uint8_t *payload;
    uint32_t payload_len;
} xg_packet_t;

typedef void (*xg_packet_cb_t)(const xg_packet_t *packet, void *context);

typedef struct {
    uint8_t buffer[XG_MAX_WIRE];
    size_t length;
    uint64_t partial_since_us;
    bool partial_active;
    uint32_t bad_headers;
    uint32_t bad_payloads;
    uint32_t timeouts;
    uint32_t discarded;
} xg_parser_t;

uint32_t xg_crc32(const uint8_t *data, size_t length);
size_t xg_encode(uint8_t *output, size_t capacity, const xg_packet_t *packet);
void xg_parser_reset(xg_parser_t *parser);
void xg_parser_feed(xg_parser_t *parser, const uint8_t *data, size_t length,
                    uint64_t now_us, xg_packet_cb_t callback, void *context);
void xg_parser_tick(xg_parser_t *parser, uint64_t now_us,
                    xg_packet_cb_t callback, void *context);
