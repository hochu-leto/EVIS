"""
тот самый объект, где начиная от ошибки мы приходим к успешному решению проблемы
из эксель листа(или ямл) создаём объект с полями
определяем ошибку по value_error, озвучиваем по name_error, краткое описание по description_error
подвязываем к руководству по поиску на конфлюенс по check_link и по списку параметров important_parametr
создаём список и забрасываем его в Избранное с названием ошибки -название списка
"""


class EvoError:
    __slots__ = ('value_error', 'name_error', 'description_error', 'important_parametr', 'check_link')

    def __init__(self, raw_err_list: dict):
        pass
