#include "user_key.h"


void Key_Init(void) 
{
   GPIO_InitTypeDef GPIO_InitStruct;                        //定义初始化结构体
   RCC_APB2PeriphClockCmd(KEY_GPIO_CLK,ENABLE);	        //开时钟
	 GPIO_InitStruct.GPIO_Pin = KEY_GPIO_PIN ;        //GPIO初始化矩阵键盘低四位端口
   GPIO_InitStruct.GPIO_Mode = GPIO_Mode_IPU     ;         //GPIO初始化模式为上拉输入
   GPIO_Init(KEY_GPIO_PORT, &GPIO_InitStruct);          //写入初始化结构体
}

void LED_Init(void) 
{
   GPIO_InitTypeDef GPIO_InitStruct;                        //定义初始化结构体
   RCC_APB2PeriphClockCmd(LED_GPIO_CLK,ENABLE);	        //开时钟
	 GPIO_InitStruct.GPIO_Pin = LED_GPIO_PIN ;        //GPIO初始化矩阵键盘低四位端口
   GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP;
   GPIO_InitStruct.GPIO_Speed=GPIO_Speed_50MHz;      //GPIO初始化模式为上拉输入
   GPIO_Init(LED_GPIO_PORT, &GPIO_InitStruct);          //写入初始化结构体
}


void HongWai_Init(void)
{
   GPIO_InitTypeDef GPIO_InitStruct;                        //定义初始化结构体
   RCC_APB2PeriphClockCmd(HW_GPIO_CLK,ENABLE);	        //开时钟
	 GPIO_InitStruct.GPIO_Pin = HW_GPIO_PIN ;        //GPIO初始化矩阵键盘低四位端口
   GPIO_InitStruct.GPIO_Mode = GPIO_Mode_IN_FLOATING;         //GPIO初始化模式为上拉输入
   GPIO_Init(HW_GPIO_PORT, &GPIO_InitStruct);          //写入初始化结构体
}



void BEEP_Init(void)
{
   GPIO_InitTypeDef GPIO_InitStruct;                        //定义初始化结构体
   RCC_APB2PeriphClockCmd(BEEP_GPIO_CLK,ENABLE);	        //开时钟
	 GPIO_InitStruct.GPIO_Pin = BEEP_GPIO_PIN;        //GPIO初始化矩阵键盘低四位端口
   GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP;
   GPIO_InitStruct.GPIO_Speed=GPIO_Speed_50MHz;
   GPIO_Init(BEEP_GPIO_PORT, &GPIO_InitStruct);          //写入初始化结构体
   GPIO_SetBits(BEEP_GPIO_PORT,BEEP_GPIO_PIN);
}

void SB_Init(void)
{
   GPIO_InitTypeDef GPIO_InitStruct;                        //定义初始化结构体
   RCC_APB2PeriphClockCmd(SB_GPIO_CLK,ENABLE);	        //开时钟
	 GPIO_InitStruct.GPIO_Pin = SB_GPIO_PIN;        //GPIO初始化矩阵键盘低四位端口
   GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP;
   GPIO_InitStruct.GPIO_Speed=GPIO_Speed_50MHz;
   GPIO_Init(SB_GPIO_PORT, &GPIO_InitStruct);          //写入初始化结构体
	//GPIO_SetBits(SB_GPIO_PORT,SB_GPIO_PIN);
}



