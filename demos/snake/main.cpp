#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "e2.h"
#include "e2libs.h"
#include <string.h>

const unsigned char cie[256] = {
	0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 
	1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 
	2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 
	3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 
	5, 5, 6, 6, 6, 6, 6, 7, 7, 7, 
	7, 8, 8, 8, 8, 9, 9, 9, 10, 10, 
	10, 10, 11, 11, 11, 12, 12, 12, 13, 13, 
	13, 14, 14, 15, 15, 15, 16, 16, 17, 17, 
	17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 
	22, 23, 23, 24, 24, 25, 25, 26, 26, 27, 
	28, 28, 29, 29, 30, 31, 31, 32, 32, 33, 
	34, 34, 35, 36, 37, 37, 38, 39, 39, 40, 
	41, 42, 43, 43, 44, 45, 46, 47, 47, 48, 
	49, 50, 51, 52, 53, 54, 54, 55, 56, 57, 
	58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 
	68, 70, 71, 72, 73, 74, 75, 76, 77, 79, 
	80, 81, 82, 83, 85, 86, 87, 88, 90, 91, 
	92, 94, 95, 96, 98, 99, 100, 102, 103, 105, 
	106, 108, 109, 110, 112, 113, 115, 116, 118, 120, 
	121, 123, 124, 126, 128, 129, 131, 132, 134, 136, 
	138, 139, 141, 143, 145, 146, 148, 150, 152, 154, 
	155, 157, 159, 161, 163, 165, 167, 169, 171, 173, 
	175, 177, 179, 181, 183, 185, 187, 189, 191, 193, 
	196, 198, 200, 202, 204, 207, 209, 211, 214, 216, 
	218, 220, 223, 225, 228, 230, 232, 235, 237, 240, 
	242, 245, 247, 250, 252, 255, 
};

void master_initialize() {
	ESP_LOGI("Demo app", "Starting in master mode");
	e2_startup();
	ESP_LOGI("Demo app", "Master initialized");
}

int list_and_count_connected_slaves(bool log) {
	int i = 0;
	e2_devices_list_t dl = e2_current_devices_list();
	if (log) ESP_LOGI("Demo app", "Slaves list");
	while(dl != NULL) {
		i++;
		if (log) ESP_LOGI("Demo app", "Slave %2d Address:0x%02x Family:0x%04x Id:%d", i, dl->address, dl->family, dl->id);
		dl = dl->next;
	}
	return i;
}

struct point {
	uint8_t x;
	uint8_t y;
};

struct game {
	struct point apple;
	struct point snake[64];
	uint8_t snake_len;
	uint8_t snake_head_dir;
	uint8_t speed_reduction;
	uint8_t apple_int;
	uint8_t snake_int;
	uint8_t head_int;
	uint8_t dead;
};

void draw_mono_rainbow(int sweep_step, int percent) {
	uint8_t pixels[8][8];
	for (int i = 0; i<8; i++) {
		for (int j = 0; j<8; j++) {
			int l = (((i+j+sweep_step)%24)-12);
			l = (l<0)?-l:l;
			l *= 10;
			l += 10;
			l *= percent;
			l /= 100;
			pixels[j][i] = cie[l];
		}
	}
	E2md8x8(0).set_pixels((uint8_t*)pixels, 64);
}

void draw_game_screen(struct game * gdata) {
	uint8_t pixels[8][8];
	memset(pixels, 0, 64);
	// dead pattern
	if(gdata->dead) {
		for (int i = 0; i<8; i++) {
			for (int j = 0; j<8; j++) {
				if ((i+j+gdata->dead) % 2) {
					pixels[i][j] = cie[gdata->snake_int>>1];
				}
			}
		}
		gdata->dead = (gdata->dead==1)?2:1;
	}
	// snake himself
	for (int i = 0; i<gdata->snake_len; i++) {
		pixels[gdata->snake[i].y][gdata->snake[i].x] = cie[((i == 0)?gdata->head_int:gdata->snake_int)];
	}
	// the apple
	pixels[gdata->apple.y][gdata->apple.x] = cie[gdata->apple_int];
	E2md8x8(0).set_pixels((uint8_t*)pixels, 64);
}

void move_snake(struct game * gdata, e2_joy_state dir) {
	// move snake head
	struct point new_head = gdata->snake[0];
	switch(dir) {
		case E2_JOY_UP:
			new_head.y--;
			break;
		case E2_JOY_DOWN:
			new_head.y++;
			break;
		case E2_JOY_LEFT:
			new_head.x--;
			break;
		case E2_JOY_RIGHT:
			new_head.x++;
			break;
		default:
			return;
	}
	// move snake body
	for (int i = 63; i>0; i--) {
		gdata->snake[i] = gdata->snake[i-1];
	}
	// update head
	gdata->snake[0] = new_head;
	// wrap head
	if (gdata->snake[0].x == 255) {
		gdata->snake[0].x = 7;
	}
	if (gdata->snake[0].x == 8) {
		gdata->snake[0].x = 0;
	}
	if (gdata->snake[0].y == 255) {
		gdata->snake[0].y = 7;
	}
	if (gdata->snake[0].y == 8) {
		gdata->snake[0].y = 0;
	}
}

int points_equal(struct point a, struct point b) {
	if (a.x == b.x && a.y == b.y) {
		return 1;
	}
	return 0;
}

void make_apple(struct game * gdata) {
	gdata->apple.x = rand() % 8;
	gdata->apple.y = rand() % 8;
}

void game_loop() {
	int buzz_timeout = 0;
	int led_timeout = 0;
	e2_joy_state dirs[] = { E2_JOY_UP, E2_JOY_LEFT, E2_JOY_DOWN, E2_JOY_CENTER };
	while(true) {
		e2_api_threedigits7segmentsdisplay_display_puts(0,"---",3);
		while(E2button(0).get_button_event() != E2_BT_NOTHING);
		struct game current_game;
		make_apple(&current_game);
		current_game.snake[0].x = rand() % 8;
		current_game.snake[0].y = rand() % 8;
		current_game.snake_len = 1;
		current_game.speed_reduction = 21;
		current_game.apple_int = 255;
		current_game.snake_int = 64;
		current_game.head_int = 128;
		current_game.dead = 0;
		int speeder = 0;
		e2_joy_state direction = dirs[rand()%4];
		for(int i = 0; i<=50; i++) {
			draw_mono_rainbow(250+i, 100-(2*i));
			vTaskDelay(pdMS_TO_TICKS(10));
		}
		while(true) {
			if (led_timeout == 1) {
				e2_api_rgbled_led_set_rgb(0,0,0,0);
			}
			if (buzz_timeout == 1) {
				e2_api_buzzer_buzzer_set_sound_off(0);
			}
			if (led_timeout) {
				led_timeout--;
			}
			if (buzz_timeout) {
				buzz_timeout--;
			}
			e2_button_state b_ret = E2button(0).get_button_event();
			if (b_ret != E2_BT_NOTHING) {
				if (!current_game.dead) {
					if (b_ret == E2_BT_LONG_PRESS) {
						break;
					}
				} else {
					break;
				}
			}
			speeder+=2;
			e2_joy_state j_ret = (e2_joy_state)(E2joystick(0).get_state() & ~E2_JOY_FIRE_MASK); // ignore press
			if (j_ret != E2_JOY_CENTER) {
				direction = j_ret;
			}
			if (!current_game.dead && (speeder >= current_game.speed_reduction)) {
				// game actions
				speeder = 0;
				// move snake
				move_snake(&current_game, direction);
				// hit snake -> dead
				for (int i = 1; i<current_game.snake_len; i++) {
					if (points_equal(current_game.snake[0],current_game.snake[i])) {
						e2_api_buzzer_buzzer_set_frequency(0,4000);
						e2_api_buzzer_buzzer_set_sound_on(0);
						e2_api_rgbled_led_set_rgb(0,200,0,0);
						led_timeout = 20;
						buzz_timeout = 20;
						current_game.dead = 1;
						ESP_LOGI("Snake app", "Dead");
					}
				}
				// consumed apple -> make longer, make new apple
				if (points_equal(current_game.apple,current_game.snake[0])) {
					char scp[4];
					sprintf(scp, "%3d",current_game.snake_len);
					e2_api_threedigits7segmentsdisplay_display_puts(0,scp,3);
					current_game.snake_len++;
					current_game.speed_reduction--;
					ESP_LOGI("Snake app", "Got apple, snake is now %d segments long", current_game.snake_len);
					e2_api_buzzer_buzzer_set_frequency(0,2000);
					e2_api_buzzer_buzzer_set_sound_on(0);
					e2_api_rgbled_led_set_rgb(0,0,200,0);
					led_timeout = 5;
					buzz_timeout = 5;
					make_apple(&current_game);
				}
				// ready for next loop
			}
			draw_game_screen(&current_game);
			vTaskDelay(pdMS_TO_TICKS(10));
		}
		e2_api_buzzer_buzzer_set_sound_off(0);
		e2_api_rgbled_led_set_rgb(0,0,0,0);
		for(int i = -50; i<0; i++) {
			draw_mono_rainbow(250+i, 100+(2*i));
			vTaskDelay(pdMS_TO_TICKS(10));
		}
	}
}

void gameTask(void * p) {
	ESP_LOGI("Snake app", "Starting snake app task");
	srand(esp_random());
	e2_api_md8x8_set_all(0, 0x0);
	e2_api_buzzer_buzzer_set_frequency(0, 2500);
	e2_api_buzzer_buzzer_set_sound_on(0);
	for(int i = 0; i<250; i++) {
		draw_mono_rainbow(i, 100);
		if (i % 10 == 0) {
			e2_api_buzzer_buzzer_set_frequency(0, 2800 - (i*10));
			e2_api_rgbled_led_set_rgb(0, i, 0, 250-i);
		}
		vTaskDelay(pdMS_TO_TICKS(10));
	}
	e2_api_buzzer_buzzer_set_sound_off(0);
	e2_api_rgbled_led_set_rgb(0, 0, 0, 0);
	game_loop();
}

extern "C" void app_main()
{
	master_initialize();
	list_and_count_connected_slaves(true);
	xTaskCreate(gameTask, "snake", 8192, NULL, 2, NULL);
}
