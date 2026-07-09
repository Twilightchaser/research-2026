#ifndef __USER_ESP8266_ONENETMQTT
#define __USER_ESP8266_ONENETMQTT
#include "stm32f10x.h"
#include "user_usart_esp8266_OneNetMQTT.h"
#include "user_delay.h"

#define     OPEN                       "0"
#define     WEP                        "1"
#define     WPA_PSK                    "2"
#define     WPA2_PSK                   "3"
#define     WPA_WPA2_PSK               "4"


#define  ESP8266_SSID                 "\"YOUR_WIFI_SSID\""      //WIfI名称
#define  ESP8266_PASSWORD             "\"YOUR_WIFI_PASSWORD\""  //WIFI密码
#define  ESP8266_CHL                  "1"            //WIFI信道
#define  ESP8266_ECN                   OPEN     //WIFI加密方



#define OneNet_DeviceName               "\"YOUR_DEVICE_NAME\""
#define OneNet_DeviceName2                 "YOUR_DEVICE_NAME"
#define OneNet_ProductID               "\"YOUR_PRODUCT_ID\""
#define OneNet_ProductID2               "YOUR_PRODUCT_ID"
#define OneNet_Key                "\"YOUR_ONENET_AUTHORIZATION\""





//ESP8266 串口1


void ESP8266_OneNetMQTT_Init(void);
#endif /*____USER_ESP8266_ONENETMQTT*/
