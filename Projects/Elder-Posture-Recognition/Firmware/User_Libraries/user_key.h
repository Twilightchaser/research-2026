#ifndef __USER_KEY_H__
#define __USER_KEY_H__

#include "stm32f10x.h"
#include "user_delay.h"



#define KEY_GPIO_CLK        RCC_APB2Periph_GPIOA                               //定义键盘时钟端口
#define KEY_GPIO_PIN        GPIO_Pin_0|GPIO_Pin_1|GPIO_Pin_2|GPIO_Pin_3|GPIO_Pin_4|GPIO_Pin_5|GPIO_Pin_6|GPIO_Pin_7
#define KEY_GPIO_PORT       GPIOA                                              //定义键盘端口


#define HW_GPIO_CLK        RCC_APB2Periph_GPIOB                               //定义键盘时钟端口
#define HW_GPIO_PIN        GPIO_Pin_7            
#define HW_GPIO_PORT       GPIOB   

#define LED_GPIO_CLK        RCC_APB2Periph_GPIOB                              //定义键盘时钟端口
#define LED_GPIO_PIN        GPIO_Pin_12              
#define LED_GPIO_PORT       GPIOB  


#define BEEP_GPIO_CLK        RCC_APB2Periph_GPIOB                                //定义键盘时钟端口
#define BEEP_GPIO_PIN        GPIO_Pin_0|GPIO_Pin_1  
#define BEEP_GPIO_PORT       GPIOB   

#define SB_GPIO_CLK        RCC_APB2Periph_GPIOA                             //定义键盘时钟端口
#define SB_GPIO_PIN        GPIO_Pin_7                                                                                                   
#define SB_GPIO_PORT       GPIOA  


void Key_Init(void);
void LED_Init(void);
void HongWai_Init(void);
void BEEP_Init(void);

void SB_Init(void);
#endif
 