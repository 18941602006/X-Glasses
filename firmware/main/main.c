// SPDX-License-Identifier: MIT
#include <stdbool.h>
#include <stdint.h>

#include "esp_check.h"
#include "esp_log.h"
#include "esp_random.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "tinyusb.h"
#include "tinyusb_cdc_acm.h"
#include "tinyusb_default_config.h"
#include "tusb.h"

#include "xg_controller.h"
#include "xg_protocol.h"

static const char *TAG = "xg_usb";
static xg_parser_t parser;
static xg_controller_t controller;

static bool transmit(const xg_packet_t *packet, void *context) {
    (void)context;
    uint8_t wire[XG_MAX_WIRE];
    const size_t length = xg_encode(wire, sizeof(wire), packet);
    if (!length || !tud_cdc_connected()) return false;
    size_t offset = 0;
    const int64_t deadline = esp_timer_get_time() + 50000;
    while (offset < length && tud_cdc_connected() && esp_timer_get_time() < deadline) {
        const size_t queued = tinyusb_cdcacm_write_queue(
            TINYUSB_CDC_ACM_0, wire + offset, length - offset);
        offset += queued;
        if (tinyusb_cdcacm_write_flush(TINYUSB_CDC_ACM_0, 0) != ESP_OK || !queued)
            vTaskDelay(pdMS_TO_TICKS(1));
    }
    return offset == length;
}

static bool apply_safe_subset(uint8_t opcode, uint16_t duration_ms,
                              uint8_t intensity, void *context) {
    (void)duration_ms; (void)intensity; (void)context;
    // Until camera/haptic drivers and power are tested, only stop/cancel state transitions succeed.
    return opcode == 2 || opcode == 4;
}

static void receive_packet(const xg_packet_t *packet, void *context) {
    (void)context;
    const uint64_t received_us = (uint64_t)esp_timer_get_time();
    xg_controller_process(&controller, packet, received_us,
                          (uint64_t)esp_timer_get_time());
}

void app_main(void) {
    xg_parser_reset(&parser);
    uint64_t boot_id = ((uint64_t)esp_random() << 32) | esp_random();
    xg_controller_init(&controller, boot_id, XG_CAP_CLOCK,
                       transmit, apply_safe_subset, NULL);

    const tinyusb_config_t usb_config = TINYUSB_DEFAULT_CONFIG();
    ESP_ERROR_CHECK(tinyusb_driver_install(&usb_config));
    const tinyusb_config_cdcacm_t cdc_config = {
        .cdc_port = TINYUSB_CDC_ACM_0,
        .callback_rx = NULL,
        .callback_rx_wanted_char = NULL,
        .callback_line_state_changed = NULL,
        .callback_line_coding_changed = NULL,
    };
    ESP_ERROR_CHECK(tinyusb_cdcacm_init(&cdc_config));
    ESP_LOGW(TAG, "Protocol-only firmware: camera, ToF, IMU and haptic are disabled");

    bool was_connected = false;
    uint8_t bytes[256];
    while (true) {
        const bool connected = tud_cdc_connected();
        if (!connected && was_connected) {
            xg_controller_detach(&controller);
            xg_parser_reset(&parser);
        }
        was_connected = connected;
        if (connected) {
            size_t received = 0;
            if (tinyusb_cdcacm_read(TINYUSB_CDC_ACM_0, bytes, sizeof(bytes), &received) == ESP_OK && received)
                xg_parser_feed(&parser, bytes, received, (uint64_t)esp_timer_get_time(), receive_packet, NULL);
            xg_parser_tick(&parser, (uint64_t)esp_timer_get_time(), receive_packet, NULL);
            xg_controller_tick(&controller, (uint64_t)esp_timer_get_time());
        }
        vTaskDelay(pdMS_TO_TICKS(2));
    }
}
