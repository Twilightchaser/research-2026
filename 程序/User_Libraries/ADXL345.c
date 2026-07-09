#include <stm32f10x.h>
#include "ADXL345.h"

int X,Y,Z;
int X1,Y1,Z1;
 unsigned int ADXL345_step;
//初始化IIC

void ADXL345_SDA_OUT()
{
  GPIO_InitTypeDef GPIO_InitStruct;                        //定义初始化结构体
   RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);	        //开时钟
	 GPIO_InitStruct.GPIO_Pin = ADXL345_SDA_PIN ;        //GPIO初始化矩阵键盘低四位端口
   GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP     ;         //GPIO初始化模式为上拉输入
	 GPIO_InitStruct.GPIO_Speed=GPIO_Speed_50MHz;  
   GPIO_Init(ADXL345_SDA_PORT, &GPIO_InitStruct);          //写入初始化结构体

}

void ADXL345_SDA_IN()
{
   GPIO_InitTypeDef GPIO_InitStruct;                        //定义初始化结构体
   RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);	        //开时钟
	 GPIO_InitStruct.GPIO_Pin = ADXL345_SDA_PIN ;        //GPIO初始化矩阵键盘低四位端口
   GPIO_InitStruct.GPIO_Mode = GPIO_Mode_IN_FLOATING     ;         //GPIO初始化模式为上拉输入
   GPIO_Init(ADXL345_SDA_PORT, &GPIO_InitStruct);          //写入初始化结构体

}
void ADXL345_IIC_Init(void)
{			
	  GPIO_InitTypeDef GPIO_InitStruct; 
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO,ENABLE);
	  GPIO_PinRemapConfig(GPIO_Remap_SWJ_JTAGDisable, ENABLE);	
    ADXL345_SDA_OUT();
    //GPIO_Config(ADXL345_SCL_PORT,ADXL345_SCL_PIN,OUTPUT_UP);
	 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);	        //开时钟
	 GPIO_InitStruct.GPIO_Pin = ADXL345_SCL_PIN;        //GPIO初始化矩阵键盘低四位端口
   GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP     ;         //GPIO初始化模式为上拉输入
	 GPIO_InitStruct.GPIO_Speed=GPIO_Speed_50MHz;  
   GPIO_Init(ADXL345_SCL_PORT, &GPIO_InitStruct);          //写入初始化结构体
}

//产生IIC起始信号
void ADXL345_IIC_Start(void)
{
	ADXL345_SDA_OUT();     //sda线输出
    
	ADXL345_SDA_Set();	  	  
	ADXL345_SCL_Set();
	Delay_Soft_us(5);
 	ADXL345_SDA_Clr();//START:when CLK is high,DATA change form high to low 
	Delay_Soft_us(5);
	ADXL345_SCL_Clr();//钳住I2C总线，准备发送或接收数据 
}	  
//产生IIC停止信号
void ADXL345_IIC_Stop(void)
{
	ADXL345_SDA_OUT();//sda线输出
    
	ADXL345_SDA_Clr();
	ADXL345_SCL_Set();
 	Delay_Soft_us(5);
	ADXL345_SDA_Set();//发送I2C总线结束信号
	Delay_Soft_us(5);							   	
}
//等待应答信号到来
//返回值：1，接收应答失败
//        0，接收应答成功
u8 ADXL345_IIC_Wait_Ack(void)
{
    u8 temp;
	ADXL345_SDA_IN();      //SDA设置为输入
      
	ADXL345_SCL_Set();
    Delay_Soft_us(5);
    temp = ADXL345_SDA_Read();
	ADXL345_SCL_Clr();//时钟输出0
    Delay_Soft_us(5);    
	return temp;  
} 

//向IIC总线发送应答信号
//入口参数:ack (0:ACK 1:NAK)
void ADXL345_IIC_SendACK(u8 ack)
{
	ADXL345_SDA_OUT();
    if(ack)ADXL345_SDA_Set();
    else ADXL345_SDA_Clr();
    ADXL345_SCL_Set();    
    Delay_Soft_us(5);
    ADXL345_SCL_Clr();
    Delay_Soft_us(5);
}

//IIC发送一个字节		  
void ADXL345_IIC_Send_Byte(u8 txd)
{                        
    u8 t;   
	ADXL345_SDA_OUT();
    for(t=0;t<8;t++)
    {              
        if(txd&0x80)ADXL345_SDA_Set();
        else ADXL345_SDA_Clr();
        txd<<=1;
		ADXL345_SCL_Set();        
		Delay_Soft_us(5); 
		ADXL345_SCL_Clr();
		Delay_Soft_us(5); 
    }
    ADXL345_IIC_Wait_Ack();
} 	    
//读1个字节，ack=1时，发送ACK，ack=0，发送nACK   
u8 ADXL345_IIC_Read_Byte(void)
{
	unsigned char i,receive=0;
	ADXL345_SDA_Set();    
	ADXL345_SDA_IN();//SDA设置为输入
    for(i=0;i<8;i++ )
	{
        receive<<=1;
        ADXL345_SCL_Set(); 
        Delay_Soft_us(5);
        if(ADXL345_SDA_Read())receive++;
        ADXL345_SCL_Clr();        
		Delay_Soft_us(5); 
    }					 
 
    return receive;
}

void ADXL345_Single_Write(unsigned char REG_Address,unsigned char REG_data)
{
    ADXL345_IIC_Start();                  //起始信号
    ADXL345_IIC_Send_Byte(SlaveAddress);   //发送设备地址+写信号
    ADXL345_IIC_Send_Byte(REG_Address);    //内部寄存器地址，请参考中文pdf22页 
    ADXL345_IIC_Send_Byte(REG_data);       //内部寄存器数据，请参考中文pdf22页 
    ADXL345_IIC_Stop();                   //发送停止信号
}
unsigned char ADXL345_Single_Read(unsigned char REG_Address)
{  
	unsigned char REG_data;
	ADXL345_IIC_Start();                          //起始信号
	ADXL345_IIC_Send_Byte(SlaveAddress);           //发送设备地址+写信号
	ADXL345_IIC_Send_Byte(REG_Address);            //发送存储单元地址，从0开始	
	ADXL345_IIC_Start();                          //起始信号
	ADXL345_IIC_Send_Byte(SlaveAddress + 1);       //发送设备地址+读信号
	REG_data = ADXL345_IIC_Read_Byte();            //读出寄存器数据
    ADXL345_IIC_SendACK(1);  
	ADXL345_IIC_Stop();                           //停止信号
	return REG_data; 
}
void ADXL345_Multiple_Read(void)
{   
	unsigned char BUF[6];
    unsigned char i;
    ADXL345_IIC_Start();                          //起始信号
    ADXL345_IIC_Send_Byte(SlaveAddress);          //发送设备地址+写信号
    ADXL345_IIC_Send_Byte(0x32);                  //发送存储单元地址，从0x32开始	
    ADXL345_IIC_Start();                          //起始信号
    ADXL345_IIC_Send_Byte(SlaveAddress+1);        //发送设备地址+读信号
	for (i=0; i<6; i++)                   //连续读取6个地址数据，存储中BUF
	{
		BUF[i] = ADXL345_IIC_Read_Byte();         //BUF[0]存储0x32地址中的数据
		if (i == 5)
		{
            ADXL345_IIC_SendACK(1);//发送非应答
		}
		else
		{     
            ADXL345_IIC_SendACK(0);//发送应答
		}
	}
	ADXL345_IIC_Stop();  //停止信号
    
	X = (BUF[1]<<8)+BUF[0];  //合成16位数据（-32768~+32767）
	Y = (BUF[3]<<8)+BUF[2];
	Z = (BUF[5]<<8)+BUF[4];
   
}

//初始化ADXL345，根据需要请参考pdf进行修改************************
void ADXL345_Init(void)
{
   ADXL345_IIC_Init();
   ADXL345_Single_Write(0x31,0x0B);   //测量范围,正负16g，13位模式
   ADXL345_Single_Write(0x2C,0x08);   //速率设定为12.5 参考pdf13页
   ADXL345_Single_Write(0x2D,0x08);   //选择电源模式   参考pdf24页
   ADXL345_Single_Write(0x2E,0x80);   //使能 DATA_READY 中断
   ADXL345_Single_Write(0x1E,0x00);   //X 偏移量 根据测试传感器的状态写入pdf29页
   ADXL345_Single_Write(0x1F,0x00);   //Y 偏移量 根据测试传感器的状态写入pdf29页
   ADXL345_Single_Write(0x20,0x05);   //Z 偏移量 根据测试传感器的状态写入pdf29页  
}
//0-正确，1-错误
char ADXL345_Check(void)
{
    unsigned char sta;
    sta = ADXL345_Single_Read(0X00);
    if(sta != 0xE5)return 1;
    return 0;
}
/*
         o
        /|\
       / | \
swing o  o  o swing
         |
      recover
*/ 
 unsigned int PeopleSta;
char ADXL345_Step_Count(void)
{
    static char recover = 1;
    ADXL345_Multiple_Read();

    if(X&0x8000)X = 65535 - X;
    if(Y&0x8000)Y = 65535 - Y;
	  if(Y>180)PeopleSta=1;
	  else PeopleSta=0; 
    if(X > 150)
    {
        if(recover)
        {
            recover = 0;
            ADXL345_step ++;
            return 1;
        }            
    }
    else
    {
        recover = 1;
    } 
    return 0;
}








