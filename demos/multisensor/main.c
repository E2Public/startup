#include "e2libs.h"
#include "micropython.h"

#include "esp_system.h"
#include "nvs_flash.h"

void esp32_specific_init() {
	// TODO - move this to HAL
	esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        nvs_flash_init();
    }
}

void app_main()
{
	esp32_specific_init();
	e2_startup();
	micropython_repl();
}
