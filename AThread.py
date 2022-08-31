import ctypes

from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop


class AThread(QThread):
    threadSignalAThread = pyqtSignal(list)
    err_thread_signal = pyqtSignal(str)
    max_iteration = 1000
    iter_count = 1

    def __init__(self):
        super().__init__()

    def run(self):
        def emitting():
            self.threadSignalAThread.emit(self.ans_list)
            self.params_counter = 0
            self.errors_counter = 0
            self.ans_list = []
            self.iter_count += 1
            if self.iter_count > self.max_iteration:
                self.iter_count = 1

        def request_node():
            if not self.iter_count == 1:
                while not self.iter_count % vmu_params_list[self.params_counter]['period'] == 0:
                    self.ans_list.append(bytearray([0, 0, 0, 0, 0, 0, 0, 0]))
                    self.params_counter += 1
                    if self.params_counter >= self.len_param_list:
                        self.params_counter = 0
                        emitting()
                        return

            param = can_adapter.can_request(self.current_node.req_id, self.current_node.ans_id,
                                            req_list[self.params_counter])
            self.ans_list.append(param)
            self.params_counter += 1

            if isinstance(param, str):
                self.errors_counter += 1
                if self.errors_counter > 3:
                    self.threadSignalAThread.emit([param])
                    return
            else:
                self.errors_counter = 0

            if self.params_counter >= self.len_param_list:
                self.params_counter = 0
                emitting()

        def request_errors():
            timer.stop()
            errors_str = window.err_str
            for nd in evo_nodes.values():
                if str(nd.errors_req) != 'nan' and str(nd.errors_list) != 'nan':
                    if ';' in nd.errors_req:
                        err_req_list = nd.errors_req.split(';')
                    else:
                        err_req_list = [nd.errors_req]
                    import ast
                    node_errors_list = ast.literal_eval(nd.errors_list)
                    for errors_req in err_req_list:
                        err_req = [int(i, 16) for i in errors_req.split(', ')]

                        errors = can_adapter.can_request(nd.req_id, nd.ans_id, err_req)
                        if not isinstance(errors, str):
                            if nd.protocol == 'CANOpen':
                                errors = (errors[5] << 8) + errors[4]
                            elif nd.protocol == 'MODBUS':
                                errors = errors[0]
                            else:
                                errors = ctypes.c_int32(errors)
                            if errors != 0:
                                for err_nom, err_str in node_errors_list.items():
                                    if errors & err_nom:
                                        if (nd.name + ':  ' + err_str) not in errors_str:
                                            errors_str += nd.name + ':  ' + err_str + '\n'
            self.err_thread_signal.emit(errors_str)
            timer.start(send_delay)

        send_delay = 10  # задержка отправки в кан сообщений
        err_req_delay = 1500
        self.len_param_list = len(req_list)
        self.current_node = evo_nodes[window.nodes_tree.currentItem().parent().text(0)]
        self.errors_counter = 0
        self.params_counter = 0
        self.ans_list = []

        timer = QTimer()
        timer.timeout.connect(request_node)
        timer.start(send_delay)
        err_timer = QTimer()
        err_timer.timeout.connect(request_errors)
        err_timer.start(err_req_delay)
        loop = QEventLoop()
        loop.exec_()


