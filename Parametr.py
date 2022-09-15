from pyqt5_plugins.examplebutton import QtWidgets

from EVONode import EVONode

empty_par = {'name': '',
             'address': '',
             'editable': '',
             'description': '',
             'scale': '',
             'scaleB': '',
             'unit': '',
             'value': '',
             'type': '',
             'group': '',
             'period': '',
             'size': '',
             'degree': ''}

example_par = {'name': 'fghjk',
               'address': '34567',
               'editable': 1,
               'description': 'ytfjll hkvlbjkkj',
               'scale': 10,
               'scaleB': -40,
               'unit': 'A',
               'value': '23',
               'type': 'SIGNED16',
               'group': '1',
               'period': '20',
               'size': 'nan',
               'degree': 3}


class Parametr:

    def __init__(self, param=None, node=None):
        if param is None:
            param = empty_par
        if node is None:
            node = EVONode

        def check_value(value, name: str):
            v = value if name not in list(param.keys()) \
                         or str(param[name]) == 'nan' \
                else (param[name] if not isinstance(param[name], str)
                      else (param[name] if param[name].isdigit()
                            else value))
            return v

        def check_string(name: str, s=''):
            st = param[name] if name in list(param.keys()) \
                                and str(param[name]) != 'nan' else s
            return st

        self.name = param['name']
        self.address = param['address']
        self.type = param['type']

        self.editable = True if 'editable' in list(param.keys()) else False

        self.unit = check_string('unit')
        self.description = param['description'] if 'description' in list(param.keys()) \
                                                   and str(param['description']) != 'nan' else ''
        self.group = param['group'] if 'group' in list(param.keys()) \
                                       and str(param['group']) != 'nan' else ''
        #
        self.size = param['size'] if 'size' in list(param.keys()) \
                                     and str(param['size']) != 'nan' else ''
        self.value = 0
        self.scale = float(check_value(1, 'scale'))
        self.scaleB = float(check_value(0, 'scaleB'))
        self.period = int(check_value(1, 'period'))
        self.period = 1000 if self.period > 1000 else self.period
        self.degree = int(check_value(0, 'degree'))
        # из типа
        self.min_value = 0
        self.max_value = 1000000
        # из editable и соответствующего списка
        self.widget = QtWidgets
        # что ставить, если node не передали
        self.node = node
        self.req_list = []
        self.set_list = []

    def get_value(self):
        pass

    def set_value(self):
        pass
