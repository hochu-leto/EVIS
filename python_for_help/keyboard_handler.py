import time

from EvCON import BRAKE_TIMER

# шляпа нерабочая

class KeyboardHandler():

    def __init__(self, window):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.window = window

    def keyboard_event_received(self, event):
        if event.event_type == 'down':
            # print(event.name)
            if event.name == 'space':
                self.window.vmu_req_thread.brake_timer = int(round(time.time() * 1000)) + BRAKE_TIMER
                self.window.speed_slider.setValue(0)
                self.window.power_slider.setValue(0)
            elif event.name == 'esc':
                self.window.record_vmu_params = False
                self.window.thread_to_record.running = False
                self.window.thread_to_record.terminate()
                self.marathon.close_marathon_canal()
                self.window.close()

            # elif event.name == 'up':
            #     if window.speed_slider.isEnabled():
            #         window.speed_slider.setValue(window.speed_slider.value() + window.speed_slider.singleStep())
            #     if window.power_slider.isEnabled():
            #         window.power_slider.setValue(window.power_slider.value() + window.power_slider.singleStep())
            # elif event.name == 'down':
            #     if window.speed_slider.isEnabled():
            #         window.speed_slider.setValue(window.speed_slider.value() - window.speed_slider.singleStep())
            #     if window.power_slider.isEnabled():
            #         window.power_slider.setValue(window.power_slider.value() - window.power_slider.singleStep())
            # elif event.name == 'left':
            #     if window.steer_allow_cb.isChecked():
            #         window.front_steer_slider.setValue(window.front_steer_slider.value() -
            #                                            5 * window.front_steer_slider.singleStep())
            #     if window.circle_mode_rb.isChecked():
            #         window.rear_steer_slider.setValue(-1 * window.front_steer_slider.value())
            #     elif window.crab_mode_rb.isChecked():
            #         window.rear_steer_slider.setValue(window.front_steer_slider.value())
            # elif event.name == 'right':
            #     if window.steer_allow_cb.isChecked():
            #         window.front_steer_slider.setValue(window.front_steer_slider.value() +
            #                                            5 * window.front_steer_slider.singleStep())
            #     if window.circle_mode_rb.isChecked():
            #         window.rear_steer_slider.setValue(-1 * window.front_steer_slider.value())
            #     elif window.crab_mode_rb.isChecked():
            #         window.rear_steer_slider.setValue(window.front_steer_slider.value())


    def ctrl_left():
        if window.steer_allow_cb.isChecked():
            window.front_steer_slider.setValue(window.front_steer_slider.value() -
                                               window.front_steer_slider.pageStep())
        if window.circle_mode_rb.isChecked():
            window.rear_steer_slider.setValue(-1 * window.front_steer_slider.value())
        elif window.crab_mode_rb.isChecked():
            window.rear_steer_slider.setValue(window.front_steer_slider.value())


    def ctrl_right():
        if window.steer_allow_cb.isChecked():
            window.front_steer_slider.setValue(window.front_steer_slider.value() +
                                               window.front_steer_slider.pageStep())
        if window.circle_mode_rb.isChecked():
            window.rear_steer_slider.setValue(-1 * window.front_steer_slider.value())
        elif window.crab_mode_rb.isChecked():
            window.rear_steer_slider.setValue(window.front_steer_slider.value())


    def ctrl_up():
        if window.speed_slider.isEnabled():
            window.speed_slider.setValue(window.speed_slider.value() + window.speed_slider.pageStep())
        if window.power_slider.isEnabled():
            window.power_slider.setValue(window.power_slider.value() + window.power_slider.pageStep())


    def ctrl_down():
        if window.speed_slider.isEnabled():
            window.speed_slider.setValue(window.speed_slider.value() - window.speed_slider.pageStep())
        if window.power_slider.isEnabled():
            window.power_slider.setValue(window.power_slider.value() - window.power_slider.pageStep())



    # kh = KeyboardHandler(window)
    # window.hook = keyboard.on_press(kh.keyboard_event_received)
    # keyboard.add_hotkey('ctrl + up', ctrl_up)
    # keyboard.add_hotkey('ctrl + down', ctrl_down)
    # keyboard.add_hotkey('ctrl + left', ctrl_left)
    # keyboard.add_hotkey('ctrl + right', ctrl_right)
    # window.steer_allow_cb.stateChanged.connect(steer_allowed_changed)
    # window.suspesion_allow_cb.stateChanged.connect(suspension_allowed_changed)
    # window.blocks_list.currentItemChanged.connect(params_list_changed)
