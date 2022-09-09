/*!
 \file warnings.h
 \brief Software module for calculate warnings

 \author Aleksey
 \version 1.0
 \date 05.09.2020
 \defgroup
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

// bit_WARNING1 - устанавливает общее предупреждение ТД, а что за авариЯ берём с ТД
// 1
#define WARNING1_PSTED 0x1
#define WARNING1_SERVO_STR1 0x2
#define WARNING1_SERVO_STR2 0x4
#define WARNING1_SERVO_BRK1 0x8
#define WARNING1_SERVO_BRK2 0x10
#define WARNING1_FAULT_DISABLE 0x20
#define WARNING1_BMS_CAN_LOST 0x40
#define WARNING1_CHARGER_CAN_LOST 0x80
#define WARNING1_CHARGER_ERROR 0x100
#define WARNING1_ISOLATION_FAULT 0x200
#define WARNING1_TD11 0x400
#define WARNING1_TD12 0x800
#define WARNING1_TD13 0x1000
#define WARNING1_TD14 0x2000
#define WARNING1_WRONG_CONFIGURATION 0x4000
#define WARNING1_SD_CARD 0x8000
// 16
/*
//bit_WARNING2 - устанавливает общее предупреждение устройства, а что за авариЯ берём с устройства
//17
#define WARNING2_KDVS			0x1
#define WARNING2_KSN			0x2
#define WARNING2_KTR			0x4
#define WARNING2_KVP			0x8
//#define WARNING2_KZAKB		0x10
#define WARNING2_KTG			0x20
#define WARNING2_BIUS			0x40
#define WARNING2_MN			0x80
#define WARNING2_OV			0x100
#define WARNING2_TG1_1		0x200
#define WARNING2_TG1_2		0x400
//#define WARNING2_DVS		0x800
#define WARNING_WRONG_CONFIGURATION		0x1000
#define WARNING_SD_CARD					0x2000
//#define WARNING_PDPINT_HEAT_CH1				0x4000
//#define WARNING_PDPINT_HEAT_CH2				0x8000
//32
*/

// SUB_SM_PROT
#define WARNINGS_OFF 0
#define WARNINGS_ON_OK 1
#define WARNINGS_FAIL 2

struct Swarnings {
  Uint16 warning_code;  //!< листающийся код аварии
  Uint16 bit_warnings1;
  Uint16 bit_warnings2;
  Uint16 warnings_time;

  Uint16 reset;
  Uint16 reset_temp;
  Uint16 error;
  Uint32 bit_warnings_mix;

  Uint16 masked_bit_warnings1;  //!<Слово аварий после маскированиЯ
  Uint16 masked_bit_warnings2;  //!<Слово аварий после маскированиЯ

  Uint16 bit_warnings_written1;
  Uint16 bit_warnings_written2;

  Uint16 mask_bit_warnings1;  //!<Слово аварий после маскированиЯ
  Uint16 mask_bit_warnings2;  //!<Слово аварий после маскированиЯ

  // ДА
  Uint16 E;
  Uint16 enable;
  Uint16 state;
  Uint16 state_prev;
  Uint16 powered_okCounter;
  Uint16 Counter_ms;
  Uint16 WrongConfigurationFlag;

  void (*calc_init)(volatile struct Swarnings*); /* Pointer to the init funcion           */
  void (*calc_BG)(volatile struct Swarnings*);   /* Pointer to the calc funtion           */
  void (*calc_1k)(volatile struct Swarnings*);   /* Pointer to the calc funtion           */
};

typedef volatile struct Swarnings Twarnings;
/*-----------------------------------------------------------------------------
 DeWARNING initializer for the
 -----------------------------------------------------------------------------*/
#define DEFAULTS_WARNINGS                                                                                              \
  {                                                                                                                    \
    .state_prev = 0xFFFF, .calc_init = Warnings_calc_init, .calc_BG = Warnings_calc_BG, .calc_1k = Warnings_calc_1k,   \
    .bit_warnings1 = 0, .bit_warnings2 = 0, .mask_bit_warnings1 = 0xFFFF, .mask_bit_warnings2 = 0xFFFF,                \
  }

// Прототипы функций
void Warnings_calc_init(Twarnings*);
void Warnings_calc_BG(Twarnings*);
void Warnings_calc_1k(Twarnings*);

#ifdef __cplusplus
}
#endif
