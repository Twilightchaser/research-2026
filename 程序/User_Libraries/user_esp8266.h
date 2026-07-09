#ifndef __USER_ESP8266_H
#define __USER_ESP8266_H
#include "stm32f10x.h"
#include "user_usart_esp8266_OneNetMQTT.h"
#include "user_delay.h"

#define     OPEN                       "0"
#define     WEP                        "1"
#define     WPA_PSK                    "2"
#define     WPA2_PSK                   "3"
#define     WPA_WPA2_PSK               "4"


#define  ESP8266_SSID                  "\"YOUR_WIFI_SSID\""      //WIfI名称
#define  ESP8266_PASSWORD             "\"YOUR_WIFI_PASSWORD\""  //WIFI密码
#define  ESP8266_CHL                  "1"            //WIFI信道
#define  ESP8266_ECN                   OPEN     //WIFI加密方
//ESP8266 串口1


void ESP8266_AP_Init(void);
#endif /*__USER_ESP8266_H*/
