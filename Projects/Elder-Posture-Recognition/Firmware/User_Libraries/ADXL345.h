#ifndef __ADXL345_H__
#define __ADXL345_H__
#include "sys.h"
#include "user_delay.h"


/*=========================步数检测==========================*/
//定义接口
#define ADXL345_SCL_PORT    GPIOA
#define ADXL345_SCL_PIN     GPIO_Pin_6
#define ADXL345_SDA_PORT    GPIOA
#define ADXL345_SDA_PIN     GPIO_Pin_7
//其他宏定义，无需修改，除非你知道自己在干什么
#define ADXL345_SCL_Clr() GPIO_ResetBits(ADXL345_SCL_PORT,ADXL345_SCL_PIN)//SCL
#define ADXL345_SCL_Set() GPIO_SetBits(ADXL345_SCL_PORT,ADXL345_SCL_PIN)

#define ADXL345_SDA_Clr() GPIO_ResetBits(ADXL345_SDA_PORT,ADXL345_SDA_PIN)//SDA
#define ADXL345_SDA_Set() GPIO_SetBits(ADXL345_SDA_PORT,ADXL345_SDA_PIN)

#define ADXL345_SDA_Read() GPIO_ReadInputDataBit(ADXL345_SDA_PORT,ADXL345_SDA_PIN)

#define	SlaveAddress   0xA6	  //定义器件在IIC总线中的从地址,根据ALT  ADDRESS地址引脚不同修改

#define JudgeP_M  0x8000   //正负数判断
#define Left_cmp  0x006e   //方向数据比较值，数值越小，越灵敏
#define Right_cmp 0x006e
#define Go_cmp    0x006e
#define Back_cmp  0x006e
extern unsigned int ADXL345_step;
//可用函数的声明
void ADXL345_Init(void);
char ADXL345_Check(void);
char ADXL345_Step_Count(void);
void ADXL345_Multiple_Read(void);







#endif

