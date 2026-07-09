#include "stm32f10x.h"//固件库
#include "OLED.h"//OLED驱动
#include "user_delay.h"//延时函数
#include "user_usart.h"//串口1
#include "ADXL345.h"//ADXL345传感器
#include <stdio.h>
#include <stdlib.h>
#include "user_esp8266_OneNetMQTT.h"
#include "user_esp8266.h"
#include "user_usart_esp8266_OneNetMQTT.h"

#define FALL_ANGLE_SET          50
#define SIT_TIME_SET            20
#define STATIC_DELTA_SET        25

extern int X,Y,Z;//ADXL三轴坐标数据

double Val_Num[10];
int Val_ID=1;

int jiaodu;
int body_state=0;//0 normal, 1 fall, 2 sedentary
volatile int static_time=0;

static int ADXL345_ToSigned(int value)
{
	if(value&0x8000)
	{
		return value-65536;
	}
	return value;
}

void Timer_Init(void)//云平台定时上传
{
	NVIC_InitTypeDef NVIC_InitStructure;
	TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM1,ENABLE);
	TIM_InternalClockConfig(TIM1);
	TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
	TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;
	TIM_TimeBaseInitStructure.TIM_Period = 3000-1;
	TIM_TimeBaseInitStructure.TIM_Prescaler = 7200-1;
	TIM_TimeBaseInitStructure.TIM_RepetitionCounter = 0;
	TIM_TimeBaseInit(TIM1,&TIM_TimeBaseInitStructure);
	TIM_ClearFlag(TIM1,TIM_FLAG_Update);
	TIM_ITConfig(TIM1,TIM_IT_Update,ENABLE);
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
	NVIC_InitStructure.NVIC_IRQChannel = TIM1_UP_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 2;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
 	NVIC_Init(&NVIC_InitStructure);
	TIM_Cmd(TIM1,ENABLE);
}

void TIM1_UP_IRQHandler(void)
{
	if(TIM_GetITStatus(TIM1,TIM_IT_Update)==SET)
	{
		TIM_ClearITPendingBit(TIM1,TIM_IT_Update);
		printf("AT+MQTTPUB=0,\"$sys/%s/%s/thing/property/post\",\"{\\\"id\\\":\\\"123\\\"\\,\\\"params\\\":{\\\"Val%d\\\":{\\\"value\\\":%.2lf\\}}}\",0,0\r\n",OneNet_ProductID2,OneNet_DeviceName2,Val_ID,Val_Num[Val_ID]);
		Val_ID++;
		if(Val_ID>2)
		{
			Val_ID=1;
		}
	}
}

void Timer3_Init(void)//久坐计时，1s
{
	TIM_TimeBaseInitTypeDef TimerBaseInitStructure;
	NVIC_InitTypeDef NVICInitStructure;

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);
	TimerBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
	TimerBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;
	TimerBaseInitStructure.TIM_Period = 10000-1;
	TimerBaseInitStructure.TIM_Prescaler = 7200-1;
	TIM_TimeBaseInit(TIM3, &TimerBaseInitStructure);
	TIM_ClearFlag(TIM3,TIM_FLAG_Update);
	TIM_ITConfig(TIM3,TIM_IT_Update,ENABLE);
	TIM_Cmd(TIM3,ENABLE);
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
	NVICInitStructure.NVIC_IRQChannel = TIM3_IRQn;
	NVICInitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVICInitStructure.NVIC_IRQChannelPreemptionPriority = 2;
	NVICInitStructure.NVIC_IRQChannelSubPriority = 2;
	NVIC_Init(&NVICInitStructure);
}

void TIM3_IRQHandler(void)
{
	if(TIM_GetITStatus(TIM3,TIM_IT_Update) != RESET)
	{
		TIM_ClearITPendingBit(TIM3,TIM_IT_Update);
		if(static_time<999)
		{
			static_time++;
		}
	}
}

void OLED_ShowState(void)
{
	OLED_ShowString(1, 1, "State:");
	//OLED_ShowNum(1, 7, body_state, 1);
	
	
	if(body_state==1)
	{
		OLED_ShowString(1, 9, "FALL  ");
	}
	else if(body_state==2)
	{
		OLED_ShowString(1, 9, "SIT   ");
	}
	else
	{
		OLED_ShowString(1, 9, "NORMAL");
	}
	OLED_ShowString(2, 1, "Angle:");
	OLED_ShowNum(2, 8, jiaodu, 3);
	OLED_ShowString(3, 1, "Still:");
	OLED_ShowNum(3, 8, static_time, 3);
	OLED_ShowString(3, 11, "s");
}

int main(void)
{
	int x,y,z;
	int last_x=0,last_y=0,last_z=0;
	int delta;
	unsigned char first_read=1;

	OLED_Init();
	OLED_ShowString(1,1,"Loading...");
	Delay_Soft_ms(200);
	ESP8266_OneNetMQTT_Init();
	OLED_Clear();
	Timer_Init();
	ADXL345_Init();
	Timer3_Init();
	OLED_Clear();

	while (1)
	{
		Val_Num[1]=body_state;
		ADXL345_Multiple_Read();
		x=ADXL345_ToSigned(X);
		y=ADXL345_ToSigned(Y);
		z=ADXL345_ToSigned(Z);

		jiaodu=abs(z)/3;
		delta=abs(x-last_x)+abs(y-last_y)+abs(z-last_z);
		if(first_read)
		{
			first_read=0;
			static_time=0;
		}
		else if(delta>STATIC_DELTA_SET)
		{
			static_time=0;
		}
		last_x=x;
		last_y=y;
		last_z=z;

		if(jiaodu<FALL_ANGLE_SET)
		{
			body_state=1;
		}
		else if(static_time>SIT_TIME_SET)
		{
			body_state=2;
		}
		else
		{
			body_state=0;
		}

		Val_Num[1]=body_state;
		Val_Num[2]=jiaodu;
		Val_Num[3]=static_time;
		OLED_ShowState();
		Delay_Soft_ms(100);
	}
}