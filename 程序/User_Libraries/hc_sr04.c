#include "stm32f10x.h"
#include "hc_sr04.h"
#include "user_delay.h"//延时函数

 uint16_t mscount=0;//定义毫秒级计数

void HC_SR04Config(void)
{
	  GPIO_InitTypeDef GPIO_hcsr04init;//超声波时钟结构体初始化
	  TIM_TimeBaseInitTypeDef TIM_hcsr04init;//定时器时钟结构体初始化
	  NVIC_InitTypeDef NVIC_hcsr04init;//定时器中断结构体初始化
	
	  NVIC_PriorityGroupConfig(NVIC_PriorityGroup_1);//中断定时器优先级分组

	  //1.打开时钟
	  RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB,ENABLE);//打开GPIO时钟
	  RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2,ENABLE);//打开定时器时钟
	  
	
	
	  //2.配置GPIO时钟
	
	  //Trig PB11 输出端 高电平
	  GPIO_hcsr04init.GPIO_Mode  = GPIO_Mode_Out_PP;//推挽输出
	  GPIO_hcsr04init.GPIO_Pin   = GPIO_Pin_10;//引脚11
	  GPIO_hcsr04init.GPIO_Speed = GPIO_Speed_50MHz;//速度为50Mhz
	      
	  GPIO_Init(GPIOB,&GPIO_hcsr04init);//配置GPIO初始化函数
	
	  //Echo PB10 输入端 
	  GPIO_hcsr04init.GPIO_Mode  = GPIO_Mode_IN_FLOATING;//浮空输入
	  GPIO_hcsr04init.GPIO_Pin   = GPIO_Pin_11;//引脚10
	  
	  GPIO_Init(GPIOB,&GPIO_hcsr04init);//配置GPIO初始化函数
	   
	
	  //3.配置定时器结构体
		TIM_hcsr04init.TIM_ClockDivision = TIM_CKD_DIV1;//不分频
		TIM_hcsr04init.TIM_CounterMode   = TIM_CounterMode_Up;//计数模式为向上计数
		TIM_hcsr04init.TIM_Period        = 1000-1;//重装载值为99
		TIM_hcsr04init.TIM_Prescaler     = 72-1;//分频系数为71
		
	  TIM_TimeBaseInit(TIM2,&TIM_hcsr04init);//配置定时器初始化函数
		TIM_ITConfig(TIM2,TIM_IT_Update,ENABLE);//使能定时器中断
		TIM_Cmd(TIM2,DISABLE);//失能定时器
		
	   
	  //4.配置定时器中断结构体
		NVIC_hcsr04init.NVIC_IRQChannel     =  TIM2_IRQn;//配置通道4
		NVIC_hcsr04init.NVIC_IRQChannelCmd  =  ENABLE;//使能定时器中断
		NVIC_hcsr04init.NVIC_IRQChannelPreemptionPriority  = 0;//抢占优先级为0
		NVIC_hcsr04init.NVIC_IRQChannelSubPriority         = 0;//子优先级为0
		 
		NVIC_Init(&NVIC_hcsr04init);//配置中断初始化
	
}


void Open_Tim2(void)//定时器开启
{
		TIM_SetCounter(TIM2,0);//开启定时器
	  mscount=0;
	  TIM_Cmd(TIM2,ENABLE);//打开定时器
	  
}

void Close_Tim2(void)//定时器关闭
{
		TIM_Cmd(TIM2,DISABLE);//失能定时器

}


void TIM2_IRQHandler(void)//中断服务函数（判断是否发生中断）
{
		if(TIM_GetITStatus(TIM2,TIM_IT_Update)!=RESET)
		{
				 TIM_ClearITPendingBit(TIM2,TIM_IT_Update);//清除中断标志位
				 mscount++;
		}

}


int GetEcho_time(void)//获取定时器的数值
{
		uint32_t t=0;
	  t=mscount*1000;//中断时间
	  t+= TIM_GetCounter(TIM2);//得到定时器计数时间
	  TIM2->CNT=0;//重装载值为0
	  Delay_Soft_ms(50);//延迟50ms
	
	  return t;

}



float Getlength(void)//获取距离长度
{
	int E_i=0;
	 int i=0;//定义次数i
	 uint32_t t=0;//定义时间t
	 float length=0; //定义长度length
	 float sum=0;//距离求和
	 while(i!=5)//发送5次超声波
	 {
			TRIG_Send(1);//发送超声波
		  Delay_Soft_us(20);//发送20us
		  TRIG_Send(0);//停止发送超声波
	
		  while(ECHO_Reci==0)
			{
			  E_i++;
				if(E_i>10000)
				{
					E_i=0;
				 break;
				}
			
			}//当超声波发出后
			Open_Tim2();//打开定时器
		  i=i+1; //次数加一
			
			
			while(ECHO_Reci==1)
			{
			{
			  E_i++;
				if(E_i>10000)
				{
					E_i=0;
				 break;
				}
			
			}
			}//当收到超声波返回信号
			Close_Tim2();//关闭定时器
			t=GetEcho_time();//获取定时器计数数值
		  length=((float)t/5.0);//计算出距离长度
		  sum=sum+length;//距离长度求和
			
	 }
	 length=sum;//计算距离平均值
	 return length;//返回距离长度

}
 


