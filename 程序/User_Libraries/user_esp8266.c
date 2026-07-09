#include "user_esp8266.h"
#include "user_usart_esp8266_OneNetMQTT.h"


void ESP8266_AP_Init()
{
	Delay_Soft_ms (20);
   USART_Config();
	Usart_SendString( DEBUG_USARTx,"AT+RST\r\n");
	Delay_Soft_ms (500);
	Usart_SendString( DEBUG_USARTx,"AT\r\n");
	Delay_Soft_ms (20);
	Usart_SendString( DEBUG_USARTx,"AT+CWMODE=2\r\n");
	Delay_Soft_ms (20);
	Usart_SendString( DEBUG_USARTx,"AT+CWSAP=");
	Usart_SendString( DEBUG_USARTx,ESP8266_SSID);
	Usart_SendString( DEBUG_USARTx,",");
	Usart_SendString( DEBUG_USARTx,ESP8266_PASSWORD);
	Usart_SendString( DEBUG_USARTx,",");
	Usart_SendString( DEBUG_USARTx,ESP8266_CHL);
	Usart_SendString( DEBUG_USARTx,",");
	Usart_SendString( DEBUG_USARTx,ESP8266_ECN);
	Usart_SendString( DEBUG_USARTx,"\r\n");
	Delay_Soft_ms (20);
	Usart_SendString( DEBUG_USARTx,"AT+RST\r\n");
	Delay_Soft_ms (500);
	Usart_SendString( DEBUG_USARTx,"AT+CIPMUX=1\r\n");
	Delay_Soft_ms (20);
	Usart_SendString( DEBUG_USARTx,"AT+CIPSERVER=1,8080\r\n");
	Delay_Soft_ms (20);
}

