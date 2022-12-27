"""
тот самый объект, где начиная от ошибки мы приходим к успешному решению проблемы
из эксель листа(или ямл) создаём объект с полями
определяем ошибку по value_error, озвучиваем по name_error, краткое описание по description_error
подвязываем к руководству по поиску на конфлюенс по check_link и по списку параметров important_parametr
создаём список и забрасываем его в Избранное с названием ошибки -название списка
"""

empty_error = {
    'name': 'Неизвестная ошибка',
    'value': 0,
    'description': '',
    'important_parameters': [],
    'check_link': '',
    'critical': False,
    'node': None
}


class EvoError:
    __slots__ = ('value', 'name',
                 'description', 'important_parameters',
                 'check_link', 'node', 'critical')

    def __init__(self, raw_err_dict=None, node=None):
        if raw_err_dict is None:
            raw_err_dict = empty_error

        def check_string(name: str, s=''):
            st = raw_err_dict[name] if name in list(raw_err_dict.keys()) \
                                       and str(raw_err_dict[name]) != 'nan' else s
            return st

        def check_bool(name: str, ):
            st = True if name in list(raw_err_dict.keys()) \
                         and str(raw_err_dict[name]) != 'nan' \
                         and raw_err_dict[name] else False
            return st

        def check_number(name: str, value=0):
            v = value if name not in list(raw_err_dict.keys()) or str(raw_err_dict[name]) == 'nan' \
                else (raw_err_dict[name] if not isinstance(raw_err_dict[name], str)
                      else (int(raw_err_dict[name], 16) if '0x' in raw_err_dict[name]
                            else value))
            return v

        self.name = check_string('name_error')
        self.description = check_string('description_error')
        self.value = check_number('value_error')
        self.important_parameters = [par.strip() for par in check_string('important_parametr').split(',')]
        self.check_link = [par for par in check_string('check_link').split(',')]
        self.node = node
        self.critical = check_bool('critical')
