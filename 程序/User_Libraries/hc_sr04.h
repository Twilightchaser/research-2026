#include "stm32f10x.h"
#ifndef _HC_SR04_H
#define _HC_SR04_H

void HC_SR04Config(void);
void Open_Tim2(void);
void Close_Tim2(void);
int GetEcho_time(void);
float Getlength(void);

#define TRIG_Send(a)   if(a)\
											 GPIO_SetBits(GPIOB,GPIO_Pin_10);\
											 else\
											 GPIO_ResetBits(GPIOB,GPIO_Pin_10)
        
				
#define ECHO_Reci GPIO_ReadInputDataBit(GPIOB,GPIO_Pin_11)				
  


#endif



