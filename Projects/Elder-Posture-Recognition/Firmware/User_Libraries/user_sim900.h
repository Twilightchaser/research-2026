#ifndef __USER_SIM900_H
#define __USER_SIM900_H
#include "stm32f10x.h"


#define   Phone_Num  "17875855956"
#define   Note_Num  "\"17875855956\""
void SIM900_Init(void);
int SIM900_GetSignal(void);
int SIM900_GetSIM(void);
void SIM900_Call(void);
void SIM900_DeCall(void);
void SIM900_SendNote(void);
void SIM900_SendNote2(void);
void SIM900_SendNote3(void);
#endif /*__USER_SIM900_H*/
