#ifndef _DS18B20_H_
#define _DS18B20_H_

#include "stm32f10x.h"

/*  DS18B20时钟端口、引脚定义 */
#define DS18B20_PORT 			GPIOA  
#define DS18B20_PIN 			(GPIO_Pin_8)
#define DS18B20_PORT_RCC	RCC_APB2Periph_GPIOA



#define BITBAND(addr, bitnum) ((addr & 0xF0000000)+0x2000000+((addr&0xFFFFF)<<5)+(bitnum<<2))
#define MEM_ADDR(addr) *((volatile unsigned long *)(addr))
#define BIT_ADDR(addr, bitnum) MEM_ADDR(BITBAND(addr, bitnum))
//F103XXIO 口地址映射
#define GPIOA_ODR_Addr (GPIOA_BASE+0x0C) //0x40020014
#define GPIOB_ODR_Addr (GPIOB_BASE+0x0C) //0x40020414 
#define GPIOC_ODR_Addr (GPIOC_BASE+0x0C) //0x40020814
#define GPIOD_ODR_Addr (GPIOD_BASE+0x0C) //0x40020C14
#define GPIOE_ODR_Addr (GPIOE_BASE+0x0C) //0x40021014
#define GPIOA_IDR_Addr (GPIOA_BASE+0x08) //0x40020010
#define GPIOB_IDR_Addr (GPIOB_BASE+0x08) //0x40020410
#define GPIOC_IDR_Addr (GPIOC_BASE+0x08) //0x40020810
#define GPIOD_IDR_Addr (GPIOD_BASE+0x08) //0x40020C10
#define GPIOE_IDR_Addr (GPIOE_BASE+0x08) //0x40021010

//F103XXIO 口操作,只对单一的IO 口,n 的值范围[0-15]
#define PAout(n) 		BIT_ADDR(GPIOA_ODR_Addr,n) //GPIOA 某一位输出
#define PAin(n) 		BIT_ADDR(GPIOA_IDR_Addr,n) //GPIOA 某一位输入
#define PBout(n) 		BIT_ADDR(GPIOB_ODR_Addr,n) //GPIOB 某一位输出
#define	PBin(n) 		BIT_ADDR(GPIOB_IDR_Addr,n) //GPIOB 某一位输入
#define PCout(n)		BIT_ADDR(GPIOC_ODR_Addr,n) //GPIOC 某一位输出
#define PCin(n) 		BIT_ADDR(GPIOC_IDR_Addr,n) //GPIOC 某一位输入
#define PDout(n) 		BIT_ADDR(GPIOD_ODR_Addr,n) //GPIOD 某一位输出
#define PDin(n) 		BIT_ADDR(GPIOD_IDR_Addr,n) //GPIOD 某一位输入
#define PEout(n) 		BIT_ADDR(GPIOE_ODR_Addr,n) //GPIOE 某一位输出
#define PEin(n) 		BIT_ADDR(GPIOE_IDR_Addr,n) //GPIOE 某一位输入

////IO操作函数											   
#define	DS18B20_DQ_OUT PAout(8) //数据端口	
#define	DS18B20_DQ_IN  PAin(8)  //数据端口	 
   	
u8 DS18B20_Init(void);			//初始化DS18B20
float DS18B20_GetTemperture(void);	//获取温度
void DS18B20_Start(void);		//开始温度转换
void DS18B20_Write_Byte(u8 dat);//写入一个字节
u8 DS18B20_Read_Byte(void);		//读出一个字节
u8 DS18B20_Read_Bit(void);		//读出一个位
u8 DS18B20_Check(void);			//检测是否存在DS18B20
void DS18B20_Reset(void);			//复位DS18B20   

#endif

