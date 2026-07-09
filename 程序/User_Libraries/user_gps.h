#ifndef __USER_GPS_H
#define __USER_GPS_H
#include "stm32f10x.h"

void GPS_Init(void);
int Read_GPS_UTC_Hour(void);
int Read_GPS_UTC_MIN(void);
int Read_GPS_UTC_SEC(void);
double Read_GPS_Latitude(void);
double Read_GPS_Longitude(void);
int GPS_Ready(void);
#endif /*__USER_GPS_H*/
