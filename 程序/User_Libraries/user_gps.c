#include "user_gps.h"
#include "user_usart2.h"

extern char USART2_data[70];//GPS的串口数据

void GPS_Init()//GPS初始化
{
USART2_Config();
}



int GPS_Ready()//判断GPS数据是否可靠
{
	int i=0;
	if(USART2_data[14]=='A')
	{
	  i=1; 
	}
else if(USART2_data[14]=='V')
	{
	  i=0; 
	}
	return i;
}

int Read_GPS_UTC_Hour()//读取时
{
	int GPS_Hour;
	GPS_Hour=(int)((USART2_data[4]-0x30)*10+(USART2_data[5]-0x30));;
  return GPS_Hour;

}

int Read_GPS_UTC_MIN()//读取分
{
int GPS_MIN;
	GPS_MIN=(int)((USART2_data[6]-0x30)*10+(USART2_data[7]-0x30));
  return GPS_MIN;

}
int Read_GPS_UTC_SEC()//读取秒
{
int GPS_SEC;
	GPS_SEC=(int)((USART2_data[8]-0x30)*10+(USART2_data[9]-0x30));
  return GPS_SEC;
}

double Read_GPS_Latitude()//纬度（北纬）
{
 double GPS_Latitude;
	GPS_Latitude=(double)(((USART2_data[16]-0x30)*10)+(USART2_data[17]-0x30)+((USART2_data[18]-0x30)/10.0)+((USART2_data[19]-0x30)/100.0)+((USART2_data[20]-0x30)/1000.0)+((USART2_data[21]-0x30)/10000.0));
  return GPS_Latitude;

}
double Read_GPS_Longitude()//经度（东经）
{
double GPS_Longitude;
	GPS_Longitude=(double)(((USART2_data[29]-0x30)*100)+((USART2_data[30]-0x30)*10)+(USART2_data[31]-0x30)+((USART2_data[32]-0x30)/10.0)+((USART2_data[33]-0x30)/100.0)+((USART2_data[34]-0x30)/1000.0)+((USART2_data[35]-0x30)/10000.0));
  return GPS_Longitude;

}