// SPDX-License-Identifier: MIT
#pragma once

#include "xg_protocol.h"

#define XG_CAP_CLOCK (1u << 0)
#define XG_CAP_TOF (1u << 1)
#define XG_CAP_IMU (1u << 2)
#define XG_CAP_BUTTON (1u << 3)
#define XG_CAP_CAMERA (1u << 4)
#define XG_CAP_HAPTIC (1u << 5)

typedef bool (*xg_tx_cb_t)(const xg_packet_t *packet, void *context);
typedef bool (*xg_apply_cb_t)(uint8_t opcode, uint16_t duration_ms,
                              uint8_t intensity, void *context);

typedef struct {
    uint64_t request_id;
    uint32_t payload_crc;
    uint8_t opcode;
    uint8_t result;
} xg_ack_cache_t;

typedef struct {
    uint64_t boot_id;
    uint64_t session_id;
    uint64_t host_nonce;
    uint64_t max_request_id;
    uint64_t last_heartbeat_us;
    uint32_t capabilities;
    uint32_t tx_sequence;
    uint32_t rx_sequence;
    bool ready;
    bool have_rx_sequence;
    xg_ack_cache_t cache[8];
    size_t cache_next;
    xg_tx_cb_t transmit;
    xg_apply_cb_t apply;
    void *context;
} xg_controller_t;

void xg_controller_init(xg_controller_t *controller, uint64_t boot_id,
                        uint32_t capabilities, xg_tx_cb_t transmit,
                        xg_apply_cb_t apply, void *context);
void xg_controller_detach(xg_controller_t *controller);
void xg_controller_process(xg_controller_t *controller,
                           const xg_packet_t *packet, uint64_t received_us,
                           uint64_t responding_us);
void xg_controller_tick(xg_controller_t *controller, uint64_t now_us);
