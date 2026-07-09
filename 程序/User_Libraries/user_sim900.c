#include "user_sim900.h"
#include "user_usart1.h"
#include "user_delay.h"

extern char USART1_flag;
extern char USART1_data[50];
void SIM900_Init()//初始化
{
USART1_Config();
}


int SIM900_GetSIM()//是否插入SIM卡
{
	int i=0;
Usart1_SendString(DEBUG_USART1,"AT+CPIN?\r\n");
	if(USART1_data[18]=='R')
	{
	  i=1;
	}
	else if(USART1_data[11]=='E')
	{
	i=0;
	}
		return i;
}

int SIM900_GetSignal()//是否获取信号
{
	int i=0;
Usart1_SendString(DEBUG_USART1,"AT+CSQ\r\n");
	if(USART1_data[22]=='0')
	{
	  i=0;
	}
	else 
	{
	i=1;
	}
	return i;
}


void SIM900_Call()//打电话
{
Usart1_SendString(DEBUG_USART1,"ATD");
Usart1_SendString(DEBUG_USART1,Phone_Num);
Usart1_SendString(DEBUG_USART1,";\r\n");	
}

void SIM900_DeCall()//挂断电话
{
Usart1_SendString(DEBUG_USART1,"ATH\r\n");	
}

void SIM900_SendNote()//发短信
{
	//短信配置
	Usart1_SendString(DEBUG_USART1,"AT+CSCS=\"GSM\"\r\n");
	Delay_Soft_ms (10);
Usart1_SendString(DEBUG_USART1,"AT+CMGF=1\r\n");
	Delay_Soft_ms (10);
	Usart1_SendString(DEBUG_USART1,"AT+CMGS=");
	Usart1_SendString(DEBUG_USART1,Note_Num);
	Usart1_SendString(DEBUG_USART1,"\r\n");
	Delay_Soft_ms (10);
	//短信内容
	Usart1_SendString(DEBUG_USART1,"Watch out for users falling!");


	Delay_Soft_ms (10);
	Usart1_SendByte( DEBUG_USART1,0x1A);//发送
}


void SIM900_SendNote2()//发短信
{
	//短信配置
	Usart1_SendString(DEBUG_USART1,"AT+CSCS=\"GSM\"\r\n");
	Delay_Soft_ms (10);
Usart1_SendString(DEBUG_USART1,"AT+CMGF=1\r\n");
	Delay_Soft_ms (10);
	Usart1_SendString(DEBUG_USART1,"AT+CMGS=");
	Usart1_SendString(DEBUG_USART1,Note_Num);
	Usart1_SendString(DEBUG_USART1,"\r\n");
	Delay_Soft_ms (10);
	//短信内容
	Usart1_SendString(DEBUG_USART1,"The trash can is full!");


	Delay_Soft_ms (10);
	Usart1_SendByte( DEBUG_USART1,0x1A);//发送
}

void SIM900_SendNote3()//发短信
{
	//短信配置
	Usart1_SendString(DEBUG_USART1,"AT+CSCS=\"GSM\"\r\n");
	Delay_Soft_ms (10);
Usart1_SendString(DEBUG_USART1,"AT+CMGF=1\r\n");
	Delay_Soft_ms (10);
	Usart1_SendString(DEBUG_USART1,"AT+CMGS=");
	Usart1_SendString(DEBUG_USART1,Note_Num);
	Usart1_SendString(DEBUG_USART1,"\r\n");
	Delay_Soft_ms (10);
	//短信内容
	Usart1_SendString(DEBUG_USART1,"The garbage is packed.");


	Delay_Soft_ms (10);
	Usart1_SendByte( DEBUG_USART1,0x1A);//发送
}