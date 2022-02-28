import time

from dll_power import CANMarathon

VMU_ID_PDO = 0x00000401
drive_limit = 30000 * 0.2  # 20% момента - достаточно, чтоб заехать на горку у выхода и не разложиться без тормозов
ref_torque = 0
start_time = int(round(time.time() * 1000))
send_delay = 50  # задержка отправки в кан сообщений
# // сброс ошибок
RESET_FAULTS = 8
marathon = CANMarathon()


r_fault = RESET_FAULTS  # сбрасываем ошибки - сбросить в 0 при следующей итерации

current_time = int(round(time.time() * 1000))

torque_data = int(ref_torque)
data = [r_fault + 0b10001,
        torque_data & 0xFF, ((torque_data & 0xFF00) >> 8),
        0, 0, 0, 0, 0]

if (current_time - start_time) > send_delay:
    start_time = current_time
    marathon.can_write_fast(VMU_ID_PDO, data)
