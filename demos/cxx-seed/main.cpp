#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "e2.h"
#include "e2libs.h"

void master_initialize() {
	printf("Starting in master mode... ");
	e2_startup();
	printf("Done!\n");
}

int list_and_count_connected_slaves() {
	int i = 0;
	printf("Slaves list:\n");
	e2_devices_list_t dl = e2_current_devices_list();
	while(dl != NULL) {
		i++;
		printf("Slave %2d:\taddress:0x%02x, family:0x%04x, id:%d\n", i, dl->address, dl->family, dl->id);
		dl = dl->next;
	}
	return i;
}

void appTask(void * p) {
	while(1) {
		vTaskDelay(10);
	}	
}

extern "C" void app_main()
{
	master_initialize();
	list_and_count_connected_slaves();
	xTaskCreate(appTask, "demoapp", 8192, NULL, 2, NULL);
}

