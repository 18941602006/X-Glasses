idf_component_register(
    SRCS "main.c" "xg_protocol.c" "xg_controller.c"
    INCLUDE_DIRS "."
    REQUIRES esp_timer esp_system
)

target_compile_options(${COMPONENT_LIB} PRIVATE -Wall -Wextra -Werror)
