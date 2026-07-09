#include "user_esp8266_OneNetMQTT.h"
#include "user_usart_esp8266_OneNetMQTT.h"
void ESP8266_OneNetMQTT_Init()
{
	Delay_Soft_ms (50);
   USART_Config();
	Usart_SendString( DEBUG_USARTx,"AT+RST\r\n");
	Delay_Soft_ms (1000);
	Usart_SendString( DEBUG_USARTx,"AT\r\n");
	Delay_Soft_ms (50);
	Usart_SendString( DEBUG_USARTx,"AT+CWMODE=1\r\n");
	Delay_Soft_ms (50);
		Usart_SendString( DEBUG_USARTx,"AT+CWDHCP=1,1\r\n");
	Delay_Soft_ms (50);
	Usart_SendString( DEBUG_USARTx,"AT+CWJAP=");
	Usart_SendString( DEBUG_USARTx,ESP8266_SSID);
	Usart_SendString( DEBUG_USARTx,",");
	Usart_SendString( DEBUG_USARTx,ESP8266_PASSWORD);
	Usart_SendString( DEBUG_USARTx,"\r\n");
	 Delay_Soft_ms (3000);

	Usart_SendString( DEBUG_USARTx,"AT+MQTTUSERCFG=0,1,");
	Usart_SendString( DEBUG_USARTx,OneNet_DeviceName);
	Usart_SendString( DEBUG_USARTx,",");
	Usart_SendString( DEBUG_USARTx,OneNet_ProductID);
	Usart_SendString( DEBUG_USARTx,",");
	Usart_SendString( DEBUG_USARTx,OneNet_Key);
	Usart_SendString( DEBUG_USARTx,",0,0,\"\"");
	Usart_SendString( DEBUG_USARTx,"\r\n");
	Delay_Soft_ms (50);
	Usart_SendString( DEBUG_USARTx,"AT+MQTTCONN=0,\"mqtts.heclouds.com\",1883,1\r\n");
	Delay_Soft_ms (2000);
	
	//数据上报
	Usart_SendString( DEBUG_USARTx,"AT+MQTTSUB=0,\"$sys/");
	Usart_SendString( DEBUG_USARTx,OneNet_ProductID2);
	Usart_SendString( DEBUG_USARTx,"/");
		Usart_SendString( DEBUG_USARTx,OneNet_DeviceName2);
		Usart_SendString( DEBUG_USARTx,"/thing/property/post/reply\",1\r\n");
	Delay_Soft_ms (200);
	//命令下发
	Usart_SendString( DEBUG_USARTx,"AT+MQTTSUB=0,\"$sys/");
	Usart_SendString( DEBUG_USARTx,OneNet_ProductID2);
	Usart_SendString( DEBUG_USARTx,"/");
		Usart_SendString( DEBUG_USARTx,OneNet_DeviceName2);
		Usart_SendString( DEBUG_USARTx,"/thing/property/set\",1\r\n");
	Delay_Soft_ms (200);
}


//AT+MQTTPUB=0,\"/sys/k0g9vECLvoj/ceshi01/thing/event/property/post\",\"{\\\"method\\\":\\\"thing.event.property.post\\\"\\,\\\"id\\\":\\\"1234\\\"\\,\\\"params\\\":{\\\"Humidity\\\":70}\\,\\\"version\\\":\\\"1.0.0\\\"}\",1,0
