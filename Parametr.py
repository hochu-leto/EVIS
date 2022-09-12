class Parametr:
    # if str(param['type']) != 'nan':
    #     param['type'] = param['type'].strip()
    # if str(param['name']) != 'nan':
    #
    #  if str(par['unit']) != 'nan':
    #             unit = str(par['unit'])
    #         else:
    #             unit = ''
    #
    def __init__(self, param: dict):
        self.name = param['name']
        self.address = param['address']
        self.type = param['type']
        self.unit = param['unit']
        self.editable = param['editable']
        self.description = param['description']
        self.scale = param['scale']
        self.scaleB = param['scaleB']
        self.value = param['value']
        self.period = param['period']
        self.group = param['group']
        self.size = param['size']
        self.degree = param['degree']

        pass

    def get_value(self):
        pass

    def set_value(self):
        pass
