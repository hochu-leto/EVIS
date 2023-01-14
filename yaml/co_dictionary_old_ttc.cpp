/**
 * @file co_dictionary.cpp
 * @author Sergey Pluzhnikov (sergey.pluzhnikov@evocargo.com)
 * \brief Interface to initialize Canopen stack dictionary
 * @version 0.1
 * @date 2021-05-12
 *
 * @copyright Copyright (c) 2021
 *
 */

/** \defgroup canopen_dict CanOpen dictionary
 * \ingroup  CanOpenStack
 * \details Defines all objects, available for the stack.
 *
 * \section dict_rec Record structure
 * See documentation for the \b canopen_emb_office project for more details.
 * Each record contains the following fields:
 * <table>
 * <tr>
 *   <td> \c uint32_t \c Key </td>
 *   <td>
 *     Value, containing Index, Subindex and additional flags. Normally initialized as <tt> CO_KEY(Index, Subindex,
 *     Flags) </tt>. Flags contain the following information:
 *     \li variable size in bytes ( \c CO_UNSIGNED32/16/8 or \c CO_SIGNED32/16/8)
 *     \li read / write access ( \c CO_OBJ____R_ or \c CO_OBJ_____W or \c CO_OBJ____RW
 *     \li direct access ( \c CO_OBJ_D____) the variable value is stored in \c Data field. It is pointed by \c DataPtr
 *     otherwise.
 *     \li Should a Node Id be added to the \c Data field ( \c CO_OBJ__N____ ) \li Is the record mappable to PDO ( \c
 *     CO_OBJ___P____ )
 *   </td>
 * </tr>
 * <tr>
 *   <td> \c CO_OBJ_TYPE_T* \c Type </td>
 *   <td>
 *     Defines special handlers to use for value access. Contains callbacks,that are used for object read/write and
 *     size estimation
 *   </td>
 * </tr>
 * <tr> <td> \c uint32_t \c Data <td> Data storage for objects with direct access
 * <tr> <td> \c VoidPtr \c DataPtr <td> Pointer to data storage for objects without direct access
 * <tr>
 *   <td> \c uint16_t \c ExtraFlags </td>
 *   <td>
 *    Additional flags, not required by the stack itself, but used by the application. We use \c
 *    INIT_FROM_DB_FLAG to indicate, that the value has to be initialized with a database value.
 *   </td>
 * </tr>
 * </table>
 *
 * \section co_dict_examples Record definition examples
 * \par Constant example
 * \code{.cpp} {CO_KEY(0x1000, 0, CO_UNSIGNED32 | CO_OBJ_D__R_), 0, 0x198, 0, 0}, \endcode
 * \par Pointer-to-variable example
 * \code{.cpp}  {CO_KEY(0x1005, 0, CO_UNSIGNED32 | CO_OBJ____R_), 0, 0,  &variable, 0}, \endcode
 * \par Database example
 * \code{.cpp}
 * {CO_KEY(0x1017, 0, CO_UNSIGNED16 | CO_OBJ____R_), 0, db::eIndex::CO_PRODUCER_HB, nullptr, INIT_FROM_DB_FLAG},
 * \endcode
 */

#include "canopen/include/canopen_api.h"
#include "board_config.h"
#include "database/db_data.hpp"
#include "database/database.hpp"
#include "database/data_ids.h"
#include "utils.h"

#include "steering_tomsk_task.hpp"
#include "motor_control/motor_control_types.hpp"

#include "canopen/co_dict_internal.hpp"

#include "version.h"

namespace db = evo_db;

namespace evo_db {
extern Database<eIndex, KeyType, Storage, MapData> db;
}

using DatabaseType = db::Database<db::eIndex, db::KeyType, db::Storage, db::MapData>;

namespace evo_canopen {

/** \defgroup CanOpenStack CanOpen stack
 *  @{
 */

using eIndex = db::eIndex;

/** \ingroup canopen_drivers
 * \brief CanOpen stack CAN driver */
extern const CO_IF_CAN_DRV CanOpenDriver;

/** \ingroup canopen_drivers
 * \brief CanOpen stack Timer driver */
extern const CO_IF_TIMER_DRV CanOpenTimerDriver;

namespace {

/** Driver implementations for stack operation  */
struct CO_IF_DRV_T CO_drivers = {&CanOpenDriver, &CanOpenTimerDriver};

/**
 * \brief Transform IO_Library baudrate value to baudrate in Bit/s
 *
 * \param iolib_baud - one of values, specified in IO_CAN.h. specifies baudrate in kBit/s
 *                      example: <tt> define IO_CAN_BIT_500_KB     500U </tt>
 * \return uint32_t - baudrate value in Bit/s
 */
static constexpr uint32_t get_co_baudrate(uint16_t iolib_baud) { return iolib_baud * 1000U; }

/******************************************************************************
 * PRIVATE VARIABLES
 ******************************************************************************/

/** \brief Device name available via CanOpen */
const uint8_t k_device_name[] = "VMU_N1";

/** \brief Hardware version available via CanOpen */
const uint8_t k_device_hw_version[] = "2.0.0";

/** \brief Software version available via CanOpen */
const uint8_t k_device_sw_version[] = SW_VERSION;

/** \brief Commit SHA available via CanOpen */
uint32_t k_commit_hash = COMMIT_HASH;

/** \brief Commit timestamp available via CanOpen */
uint8_t k_commit_time[] = {COMMIT_TIME_DAY, COMMIT_TIME_MONTH, COMMIT_TIME_YEAR};

/** \brief Structures to access to strings from CanOpen stack */
CO_OBJ_STR manuf_data[] = {
    {0, k_device_name},
    {0, k_device_hw_version},
    {0, k_device_sw_version},
};

// clang-format off
/** \brief The structure, holding all records for CanOpen dictionary.*/
CO_OBJ_T co_dict[] = {
    {CO_KEY(0x1000, 0, CO_UNSIGNED32 | CO_OBJ_D__R_), 0, 0x198, 0, 0},
    {CO_KEY(0x1005, 0, CO_UNSIGNED32 | CO_OBJ_D__R_), 0, 0x80, 0, 0},

    {CO_KEY(0x1008, 0, CO_STRING | CO_OBJ____R_), CO_TSTRING, 0, (manuf_data), 0},
    {CO_KEY(0x1009, 0, CO_STRING | CO_OBJ____R_), CO_TSTRING, 0, (manuf_data + 1), 0},
    {CO_KEY(0x100A, 0, CO_STRING | CO_OBJ____R_), CO_TSTRING, 0, (manuf_data + 2), 0},

    {CO_KEY(0x1017, 0, CO_UNSIGNED16 | CO_OBJ____R_),  0, static_cast<uint32_t>(eIndex::CO_PRODUCER_HB), nullptr, INIT_FROM_DB_FLAG},

    {CO_KEY(0x1018, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 4, 0, 0},
    {CO_KEY(0x1018, 1, CO_UNSIGNED32 | CO_OBJ_D__R_), 0, 0, 0, 0},
    {CO_KEY(0x1018, 2, CO_UNSIGNED32 | CO_OBJ_D__R_), 0, 0, 0, 0},
    {CO_KEY(0x1018, 3, CO_UNSIGNED32 | CO_OBJ_D__R_), 0, 0, 0, 0},
    {CO_KEY(0x1018, 4, CO_UNSIGNED32 | CO_OBJ_D__R_), 0, 0, 0, 0},

    {CO_KEY(0x1200, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 2, 0, 0},
    {CO_KEY(0x1200, 1, CO_UNSIGNED32 | CO_OBJ_DN_R_), 0, CO_COBID_SDO_REQUEST(),  0, 0},
    {CO_KEY(0x1200, 2, CO_UNSIGNED32 | CO_OBJ_DN_R_), 0, CO_COBID_SDO_RESPONSE(), 0, 0},

    /* IMPORTANT !!! 

       RPDO will not work as CanDriver configured to receive only SDO requests 
       (see common_files/src/canopen/drivers/co_can.cpp)
    */

    // Global manual enable
    {CO_KEY(0x2100, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 2, 0, 0},
    {CO_KEY(0x2100, 1, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::GLOBAL_MANUAL_ENABLE), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2100, 2, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::JOYSTICK_ENABLE),      nullptr, INIT_FROM_DB_FLAG},

    // Turn indicators
    {CO_KEY(0x2101, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 1, 0, 0},
    {CO_KEY(0x2101, 1, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::LIGHTS_TURNS_PERIOD_MS), nullptr, INIT_FROM_DB_FLAG},

    // EEPROM
    {CO_KEY(0x2102, 0, CO_UNSIGNED8 | CO_OBJ_D__R_), 0, 2, 0, 0},
    {CO_KEY(0x2102, 1, CO_UNSIGNED32 | CO_OBJ____RW), CO_COUNTER, static_cast<uint32_t>(eIndex::EEPROM_CMD_READ),  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2102, 2, CO_UNSIGNED32 | CO_OBJ____RW), CO_COUNTER, static_cast<uint32_t>(eIndex::EEPROM_CMD_WRITE), nullptr, INIT_FROM_DB_FLAG},

    // Commit info
    {CO_KEY(0x2103, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 4, 0, 0},
    {CO_KEY(0x2103, 1, CO_UNSIGNED32 | CO_OBJ____R_), 0, 0, &k_commit_hash,      0},  /* Commit short SHA */
    {CO_KEY(0x2103, 2, CO_UNSIGNED8  | CO_OBJ____R_), 0, 0, (k_commit_time),     0},  /* Commit timestamp day */
    {CO_KEY(0x2103, 3, CO_UNSIGNED8  | CO_OBJ____R_), 0, 0, (k_commit_time + 1), 0},  /* Commit timestamp month */
    {CO_KEY(0x2103, 4, CO_UNSIGNED8  | CO_OBJ____R_), 0, 0, (k_commit_time + 2), 0},  /* Commit timestamp year */

    // PSTED (outputs)
    {CO_KEY(0x2107,  0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 8, 0, 0},
    {CO_KEY(0x2107,  1, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_OUT_RUN),                  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2107,  2, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_OUT_EM_STOP),              nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2107,  3, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_OUT_REF_MAIN_VALUE),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2107,  4, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_OUT_REF_FLUX_CURRENT),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2107,  5, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_OUT_BMS_VOLTAGE),          nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2107,  6, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SYSTEM_PSTED_ONLINE),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2107,  7, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_OUT_REF_ANGLE),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2107,  8, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_OUT_MOTOR_VELOCITY_LIMIT), nullptr, INIT_FROM_DB_FLAG},

    // PSTED (inputs)
    {CO_KEY(0x2108,  0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 16, 0, 0},
    {CO_KEY(0x2108,  1, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_STATUS),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108,  2, CO_SIGNED8    | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_TORQUE),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108,  3, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_MOTOR_SPEED),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108,  4, CO_SIGNED8    | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_CURRENT),           nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108,  5, CO_SIGNED8    | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_POWER),             nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108,  6, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_VOLTAGE),           nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108,  7, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_PHASE_VOLTAGE),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108,  8, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_MOTOR_TEMP),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108,  9, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_FLUXCOIL_TEMP),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108, 10, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_INV_RADIATOR_TEMP), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108, 11, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_INV_INTERNAL_TEMP), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108, 12, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_ISOLATION_STATUS),  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108, 13, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_ERRORS_1),          nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108, 14, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_ERRORS_2),          nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108, 15, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PSTED_WARNINGS),          nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2108, 16, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_MANUAL_REFTORQUE),  nullptr, INIT_FROM_DB_FLAG},

    // PSTED (paramaters)
    {CO_KEY(0x2109,  0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 9, 0, 0},
    {CO_KEY(0x2109,  1, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_TORQUE_INVERT),                nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2109,  2, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_RAMP_MAX_TORQUE),              nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2109,  3, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_RAMP_TIME_MS),                 nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2109,  4, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_ONLINE_TIMEOUT_MS),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2109,  5, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_CONTROL_MODE),                 nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2109,  6, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_MAX_STATOR_CURRENT),           nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2109,  7, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_IF_TO_IQ_MULT),                nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2109,  8, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_DEFAULT_ANGLE),                nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2109,  9, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PSTED_DEFAULT_MOTOR_VELOCITY_LIMIT), nullptr, INIT_FROM_DB_FLAG},

    // Steering common
    {CO_KEY(0x2110, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 4, 0, 0},
    {CO_KEY(0x2110, 1, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_MANUAL_CMD_FRONT),       nullptr, INIT_FROM_DB_FLAG}, 
    {CO_KEY(0x2110, 2, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_MANUAL_CMD_REAR),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2110, 3, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_MSG_TIMEOUT),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2110, 4, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_REAR_TASK_ACTIVE), nullptr, INIT_FROM_DB_FLAG},

    // Steering front
    {CO_KEY(0x2111, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 14, 0, 0},
    {CO_KEY(0x2111, 1, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_AUTOPILOT_CMD_FRONT),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 2, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_AUTOPILOT_CUR_POS_FRONT), nullptr, INIT_FROM_DB_FLAG}, 
    {CO_KEY(0x2111, 3, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_CMD_FRONT),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 4, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_CUR_POS_FRONT),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 5, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_RUN_FRONT),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 6, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_ONLINE_FRONT) ,     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 7, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_ZERO_FRONT),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 8, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_MAX_FRONT),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 9, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_MIN_FRONT),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 10, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_INVERT_FRONT),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 11, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_STATUS_FRONT),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 12, CO_SIGNED16  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_CURRENT_FRONT),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 13, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_TEMP_FRONT),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2111, 14, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_MOTORTEMP_FRONT),   nullptr, INIT_FROM_DB_FLAG},

    // Steering rear
    {CO_KEY(0x2112, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 14, 0, 0},
    {CO_KEY(0x2112, 1, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_AUTOPILOT_CMD_REAR),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 2, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_AUTOPILOT_CUR_POS_REAR), nullptr, INIT_FROM_DB_FLAG}, 
    {CO_KEY(0x2112, 3, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_CMD_REAR),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 4, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_CUR_POS_REAR),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 5, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_RUN_REAR),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 6, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_ONLINE_REAR),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 7, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_ZERO_REAR),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 8, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_MAX_REAR),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 9, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_MIN_REAR),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 10, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::STEERING_PARAM_INVERT_REAR),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 11, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_STATUS_REAR),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 12, CO_SIGNED16  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_CURRENT_REAR),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 13, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_TEMP_REAR),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2112, 14, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::STEERING_SERVO_MOTORTEMP_REAR),   nullptr, INIT_FROM_DB_FLAG},

    // io lib errors
    {CO_KEY(0x2113, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 5, 0, 0},
    {CO_KEY(0x2113, 1, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::IOLIB_ERROR_CODE),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2113, 2, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::IOLIB_ERROR_DEVICE),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2113, 3, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::IOLIB_CFG_FLASH_ERRORS), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2113, 4, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::IOLIB_FLASH_ERRORS),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2113, 5, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::IOLIB_RAM_ERRORS),       nullptr, INIT_FROM_DB_FLAG},

    // Main FSM
    {CO_KEY(0x2114, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 3, 0, 0},
    {CO_KEY(0x2114, 1, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::MAINFSM_CURRENT_STATE),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2114, 2, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::MAINFSM_STARTUP_TIMEOUT_MS), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2114, 3, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::VEHICLE_STOP_TIMEOUT_MS),    nullptr, INIT_FROM_DB_FLAG},

    // Error monitoring
    {CO_KEY(0x2115, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 5, 0, 0},
    {CO_KEY(0x2115, 1, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::CANOPEN_LISTER_FAULT_VALUE),    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2115, 2, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::CANOPEN_LISTER_FAULT_NUM),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2115, 3, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::CANOPEN_LISTER_WARNING_VALUE),  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2115, 4, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::CANOPEN_LISTER_WARNING_NUM),    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2115, 5, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::CANOPEN_LISTER_TIMEOUT_MS),     nullptr, INIT_FROM_DB_FLAG},

    
    // Brakes
    // parameters
    {CO_KEY(0x2116, 0,  CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 23, 0, 0},
    {CO_KEY(0x2116, 1,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_ACC_PRESSURE_MAX),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 2,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_ACC_PRESSURE_MIN),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 3,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_ACC_PRESSURE_CRITICAL),   nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 4,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_ACC_CRITICAL_TIMEOUT_MS), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 5,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_SLA_VOLT_MAX),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 6,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_SLA_VOLT_MIN),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 7,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_SLR_VOLT_MAX),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 8,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_SLR_VOLT_MIN),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 9,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_PID_PROP_NUM),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 10, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_PID_PROP_DENOM),          nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 11, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_PID_INT_NUM),             nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 12, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_PID_INT_DENOM),           nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 13, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_DIRECT_UNITS_CONTROL),    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 14, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_TASK_ACTIVE),             nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 15, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_ADC_FILTER_FACTOR),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 16, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_MIN_VALID_CMD_VALUE),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 17, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_MAX_ALLOW_PRESSURE_AT_ZERO), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 18, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_EMERGENCY_STOP_POWER),    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 19, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_FRONT_CONTOUR_ENABLE),    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 20, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_REAR_CONTOUR_ENABLE),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 21, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_PUMP_LOWER_THRES),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 22, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_PUMP_UPPER_THRES),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2116, 23, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_VELOCITY_CONTROL_ENABLE), nullptr, INIT_FROM_DB_FLAG},
    // signals
    {CO_KEY(0x2117, 0,  CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 15, 0, 0},
    {CO_KEY(0x2117, 1,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CMD_CANOPEN),                     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 2,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::BRAKE_CONT_REAR_CUR_PRESSURE_CANOPEN),  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 3,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::BRAKE_CONT_FRONT_CUR_PRESSURE_CANOPEN), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 4,  CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::BRAKE_PUMP_ENABLED),                    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 5,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::BRAKE_ACC_CUR_PRESSURE),                nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 6,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_MANUAL_PUMP_EN),                  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 9,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_SOL_ACCUM_REAR_MANUAL_CTRL),      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 10, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_SOL_REL_REAR_MANUAL_CTRL),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 11, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_SOL_ACCUM_FRONT_MANUAL_CTRL),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 12, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_SOL_REL_FRONT_MANUAL_CTRL),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 13, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::BRAKE_ACC_ERRORS),                      nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 14, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::BRAKE_CONT_FRONT_ERRORS),               nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2117, 15, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::BRAKE_CONT_REAR_ERRORS),                nullptr, INIT_FROM_DB_FLAG},
    // Graceful stop curve
    {CO_KEY(0x2118, 0,  CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 10, 0, 0},
    {CO_KEY(0x2118, 1,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_TIME_1),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 2,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_TIME_2),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 3,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_TIME_3),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 4,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_TIME_4),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 5,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_TIME_5),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 6,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_PRESSURE_1), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 7,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_PRESSURE_2), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 8,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_PRESSURE_3), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 9,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_PRESSURE_4), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2118, 10, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_CURVE_PRESSURE_5), nullptr, INIT_FROM_DB_FLAG},

     // System monitoring
    {CO_KEY(0x2120, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 4, 0, 0},
    {CO_KEY(0x2120, 1, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SYSTEM_BKU_ONLINE),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2120, 2, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::POWER_BKU_TURNOFF_TIMEOUT_MS), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2120, 3, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SYSTEM_BKU_MSG_TIMEOUT),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2120, 4, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::JOYSTICK_TIMEOUT_MS),          nullptr, INIT_FROM_DB_FLAG},

    {CO_KEY(0x2121, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 2, 0, 0},
    {CO_KEY(0x2121, 1, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SYSTEM_MAINLOOP_TIME),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2121, 2, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SYSTEM_MAINLOOP_MAX_TIME), nullptr, INIT_FROM_DB_FLAG},


    {CO_KEY(0x2125, 0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 1, 0, 0},
    {CO_KEY(0x2125, 1, CO_UNSIGNED32 | CO_OBJ____RW), CO_COUNTER, static_cast<uint32_t>(eIndex::RESET_ERRORS_CMD_CANOPEN), nullptr, INIT_FROM_DB_FLAG},

    {CO_KEY(0x2126, 0,  CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 11, 0, 0},
    {CO_KEY(0x2126, 1,  CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_LAST_IDX), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 2,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_0), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 3,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_1), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 4,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_2), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 5,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_3), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 6,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_4), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 7,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_5), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 8,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_6), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 9,  CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_7), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 10, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_8), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2126, 11, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::LOG_FAULT_9), nullptr, INIT_FROM_DB_FLAG},

    // Suspension control (inputs)
    {CO_KEY(0x2130,  0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 10, 0, 0},
    {CO_KEY(0x2130,  1, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_ENABLE_PIN_SIGNAL),    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130,  2, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_CUR_1),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130,  3, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_CUR_2),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130,  4, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_CUR_3),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130,  5, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_CUR_4),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130,  6, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_PRESSURE_CUR_1),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130,  7, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_PRESSURE_CUR_2),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130,  8, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_PRESSURE_CUR_3),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130,  9, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_PRESSURE_CUR_4),       nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2130, 10, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SUSPENSION_TASK_DETAILED_STATUS), nullptr, INIT_FROM_DB_FLAG},

    // Suspension control (settings)
    {CO_KEY(0x2131,  0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 13, 0, 0},
    {CO_KEY(0x2131,  1, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_PRESSURE_MAX),                 nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131,  2, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_PRESSURE_MIN),                 nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131,  3, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_TOLERANCE),             nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131,  4, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_PRESSURE_SENSOR_FILTER_PARAM), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131,  5, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_SENSOR_FILTER_PARAM),   nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131,  6, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_INVERT_1),              nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131,  7, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_INVERT_2),              nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131,  8, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_INVERT_3),              nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131,  9, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_INVERT_4),              nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131, 10, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_H_OFFSET_1),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131, 11, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_H_OFFSET_2),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131, 12, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_H_OFFSET_3),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2131, 13, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SUSPENSION_HEIGHT_H_OFFSET_4),            nullptr, INIT_FROM_DB_FLAG},

    // Voltage monitoring
    {CO_KEY(0x2135,  0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 6, 0, 0},
    {CO_KEY(0x2135,  1, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SYSTEM_24V_VOLTAGE),           nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2135,  2, CO_UNSIGNED16 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SYSTEM_12V_VOLTAGE),           nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2135,  3, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SYSTEM_24V_VOLTAGE_LOWER_LIM), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2135,  4, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SYSTEM_24V_VOLTAGE_UPPER_LIM), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2135,  5, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SYSTEM_12V_VOLTAGE_LOWER_LIM), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2135,  6, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::SYSTEM_12V_VOLTAGE_UPPER_LIM), nullptr, INIT_FROM_DB_FLAG},

    // BMS
    {CO_KEY(0x2140,  0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 7, 0, 0},
    {CO_KEY(0x2140,  1, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BMS_TIMEOUT_MS),                     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2140,  2, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::CHARGER_TIMEOUT_MS),                 nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2140,  3, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::CHARGER_PSTED_VOLTAGE_THRES),        nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2140,  4, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::CHARGER_IGNORE_VOLT_ERR_TIMEOUT_MS), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2140,  5, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SYSTEM_BMS_ONLINE),                  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2140,  6, CO_UNSIGNED8  | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::SYSTEM_BZU_ONLINE),                  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2140,  7, CO_UNSIGNED32 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::BMS_MULTIMSG_PAGE_DEBUG),            nullptr, INIT_FROM_DB_FLAG},

    // Parking brakes
    {CO_KEY(0x2145,  0, CO_UNSIGNED8 | CO_OBJ_D__R_), 0, 2, 0, 0},
    {CO_KEY(0x2145,  1, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::PARKING_BRAKE_CMD_HOLD_CANOPEN), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2145,  2, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::PARKING_BRAKE_HELD_CANOPEN),     nullptr, INIT_FROM_DB_FLAG},

    // Discrete brakes
    {CO_KEY(0x2146,  0, CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 2, 0, 0},
    {CO_KEY(0x2146,  1, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_DISCRETE_ACCUM_TIMEOUT_MS), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2146,  2, CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::BRAKE_DISCRETE_TOTAL_TIMEOUT_MS), nullptr, INIT_FROM_DB_FLAG},

    // Discrete input signals
    {CO_KEY(0x2150,  0, CO_UNSIGNED8 | CO_OBJ_D__R_), 0, 3, 0, 0},
    {CO_KEY(0x2150,  1, CO_UNSIGNED32| CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::INPUT_RED_BUTTON),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2150,  2, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::INPUT_ANTIFREEZE_SENSOR),  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2150,  3, CO_UNSIGNED8 | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::INPUT_BRAKE_FLUID_SENSOR), nullptr, INIT_FROM_DB_FLAG},

    // ABS
    {CO_KEY(0x2160, 0,  CO_UNSIGNED8  | CO_OBJ_D__R_), 0, 17, 0, 0},
    {CO_KEY(0x2160, 1,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_WHEEL_TICK_COUNT),          nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 2,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_WHEEL_DIAMETER),            nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 3,  CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_WHEEL_MIN_SPEED_THRESHOLD), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 4,  CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_MOTOR_MIN_SPEED_THRESHOLD), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 5,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_WARNING_COUNT_THRESHOLD),   nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 6,  CO_UNSIGNED16 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_FAILURE_COUNT_THRESHOLD),   nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 7,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_SENSOR_MAPPING_FL),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 8,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_SENSOR_MAPPING_FR),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 9,  CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_SENSOR_MAPPING_RL),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 10, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_SENSOR_MAPPING_RR),         nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 11, CO_UNSIGNED8  | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_FILTER_FACTOR),             nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 12, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::ABS_VELOCITY),                  nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 13, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::ABS_WHEEL_FREQ_FL_CANOPEN),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 14, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::ABS_WHEEL_FREQ_FR_CANOPEN),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 15, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::ABS_WHEEL_FREQ_RL_CANOPEN),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 16, CO_SIGNED16   | CO_OBJ____R_), 0, static_cast<uint32_t>(eIndex::ABS_WHEEL_FREQ_RR_CANOPEN),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2160, 17, CO_SIGNED16   | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::ABS_MIN_VELOCITY_THRESHOLD),    nullptr, INIT_FROM_DB_FLAG},
    
    // Cooling fan
    {CO_KEY(0x2165,  0, CO_UNSIGNED8 | CO_OBJ_D__R_), 0, 7, 0, 0},
    {CO_KEY(0x2165,  1, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::COOLING_MOTOR_TEMP_MIN),    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2165,  2, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::COOLING_MOTOR_TEMP_MAX),    nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2165,  3, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::COOLING_INVERTOR_TEMP_MIN), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2165,  4, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::COOLING_INVERTOR_TEMP_MAX), nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2165,  5, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::COOLING_COIL_TEMP_MIN),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2165,  6, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::COOLING_COIL_TEMP_MAX),     nullptr, INIT_FROM_DB_FLAG},
    {CO_KEY(0x2165,  7, CO_UNSIGNED8 | CO_OBJ____RW), 0, static_cast<uint32_t>(eIndex::COOLING_FAN_ENABLE),        nullptr, INIT_FROM_DB_FLAG},

     
    CO_OBJ_DIR_ENDMARK /* mark end of used objects */
};
// clang-format on

/** \brief Size of the dictionary */
const uint16_t k_dict_size = sizeof(co_dict) / sizeof(co_dict[0]);

}  // namespace

/******************************************************************************
 * PUBLIC VARIABLES
 ******************************************************************************/

/** \ingroup CanOpenInitAPI
 * \brief Canopen stack parameters required for correct initialisation.
 */
constexpr extern const evo_canopenstack::CanopenInitializer stack_initializer = {
    evo_boardconfig::k_nodeid,                            /** default Node-Id                */
    get_co_baudrate(evo_boardconfig::k_canopen_baudrate), /** default Baudrate               */
    &co_dict[0],                                          /** pointer to object dictionary   */
    k_dict_size,                                          /** object dictionary length       */
    1000000,                                              /** timer clock frequency in Hz    */
    &CO_drivers,                                          /** select drivers for application */
};

/** @} */

}  // namespace evo_canopen
