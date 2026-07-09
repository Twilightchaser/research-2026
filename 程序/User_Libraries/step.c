#include "stm32f10x.h"
#include "stdbool.h"
#include "user_delay.h"
#include "step.h"
//IN4: PA6  d
//IN3: PA5  c
//IN2: PA4  b
//IN1: PA3   a
//四相八拍
unsigned char  phasecw[8] ={0x08,0x0c,0x04,0x06,0x02,0x03,0x01,0x09};// 逆时针
//1000,1100,0100,0110,0010,0011,0001,1001
unsigned phaseccw[8]={0x09,0x01,0x03,0x02,0x06,0x04,0x0c,0x08};// 顺时针
//1001,0001,0011,0010,0110,0100,1100,1000

//引脚初始化
void Step_Motor_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8|GPIO_Pin_7|GPIO_Pin_6|GPIO_Pin_5;
    GPIO_Init(GPIOA,&GPIO_InitStructure);   
}
//引脚映射
void SetMotor(unsigned char InputData)//根据传送的数据Inputdata设置脉冲引脚输出
{//根据传送的数据Inputdata设置PB5-PB8引脚输出
    if(InputData&0x01)
    {
        GPIO_SetBits(GPIOA,GPIO_Pin_5);
    }
    else
    {
        GPIO_ResetBits(GPIOA,GPIO_Pin_5);
    }
    if(InputData&0x02)
    {
        GPIO_SetBits(GPIOA,GPIO_Pin_6);
    }
    else
    {
        GPIO_ResetBits(GPIOA,GPIO_Pin_6);

    }
    if(InputData&0x04)
    {
        GPIO_SetBits(GPIOA,GPIO_Pin_7);
    }
    else
    {
        GPIO_ResetBits(GPIOA,GPIO_Pin_7);
    }
    if(InputData&0x08)
    {
        GPIO_SetBits(GPIOA,GPIO_Pin_8);
    }
    else
    {
        GPIO_ResetBits(GPIOA,GPIO_Pin_8);
    }
}
//步距角5.625 360/5.625=64 减速比1/64 
//故64*64个脉冲转一圈
//n圈数 
//position 方向
void motorNcircle(int n,bool position)//n为步进电机转动的  ，position为正转或者反转
{
    int i,j,k=0;
    for(j=0;j<n;j++)
    {
       for(i=0;i<64*5.625;i++)
       // for(i=0;i<8;i++)
        {
					for(k=0;k<8;k++)
            {
                if(1 == position)
                {
                    SetMotor(phasecw[k]);
                }
                else
                {
                    SetMotor(phaseccw[k]);
                }
                Delay_Soft_us(700);//延时：速度控制，数值越大速度越慢。电流0.65A
            }
        }
    }
}


