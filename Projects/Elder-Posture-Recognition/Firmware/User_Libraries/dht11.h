#ifndef __DHT11_H
#define __DHT11_H 
#include "sys.h"   
#include "stdio.h"

#define GPIO_CLOCK      RCC_APB2Periph_GPIOA//时钟
#define GPIO_WHAT       GPIOA //GPIO组
#define GPIO_PIN        GPIO_Pin_4////GPIO脚
#define GPIO_PIN_DATA   4
#define	DHT11_DQ_OUT    PAout(4)//数据端口	PA5 
#define	DHT11_DQ_IN     PAin(4)//数据端口	PA5 

#if (GPIO_PIN_DATA < 8 )
#define GPIO_DATA (0xFFFFFFFF & (~(0x0f << 4 * GPIO_PIN_DATA)))
#define DHT11_IO_IN()  {GPIO_WHAT->CRL&=GPIO_DATA;GPIO_WHAT->CRL|=8<<4*GPIO_PIN_DATA;}
#define DHT11_IO_OUT() {GPIO_WHAT->CRL&=GPIO_DATA;GPIO_WHAT->CRL|=3<<4*GPIO_PIN_DATA;}//X乘以4=20
#endif

#if (GPIO_PIN_DATA >= 8 )
#define GPIO_DATA (0xFFFFFFFF & (~(0x0f << 4 * (GPIO_PIN_DATA-8))))
#define DHT11_IO_IN()  {GPIO_WHAT->CRL&=GPIO_DATA;GPIO_WHAT->CRL|=8<<4*(GPIO_PIN_DATA-8);}
#define DHT11_IO_OUT() {GPIO_WHAT->CRL&=GPIO_DATA;GPIO_WHAT->CRL|=3<<4*(GPIO_PIN_DATA-8);}////X乘以4=20
#endif

void DHT11_Init(void);//初始化DHT11
u8 DHT11_Read_Data(u8 *tempH,u8 *tempL,u8 *humi);//读取温湿度
u8 DHT11_Check(void);//检测是否存在DHT11

#endif
