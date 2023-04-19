class AdapterCAN:

    def check_bitrate(self):
        # определяем скорость шины, к которой подключен
        # адаптер - просто мониторим шину, хватаем первую попавшуюся посылку
        # - если ничего нет за определённое время, значит шины нет вообще
        # - если посылка есть и он 0 0 0 0 0 0 0, то ошибка битрейта, пробуем другой
        # - если в посылке хоть один байт есть, значит с битрейтом угадали
        pass

    def canal_open(self):
        # инициализация канала
        pass

    def close_canal_can(self):
        # чтобы это могло быть?
        pass

    def can_write(self, ID: int, data: list):
        # отправка в блок с ID посылки data, почти не использую
        pass

    def can_read(self, ID: int):
        # чтение что бормочет в кан блок с ID - вообще не использую
        pass

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        # основная функция
        # запрашиваем у блока по can_id_req message и
        # выдаём что он ответил по can_id_ans
        pass


    def check_connection() -> bool:
        # проверяю подключен ли физический адаптер
        pass
