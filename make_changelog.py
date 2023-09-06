import datetime

from mdutils.mdutils import MdUtils

from EVONode import EVONode

mdFile = MdUtils(file_name='Changelog_my.md', title='Что установлено на ВАТС')

mdFile.new_paragraph("При изменении ПО либо изменении настроек любого блока на ВАТС следует это записать здесь")
mdFile.new_paragraph()

mdFile.new_header(level=1, title="ВАТС:")
main_list = [
    f'Номер: 51',
    f'Дата изменения файла: 26.08.2023'
]
mdFile.new_list(items=main_list)
mdFile.new_paragraph()

mdFile.new_header(level=1, title="Установлено:")
nodes_properties_list = [
    f'Двигатель(drive_motor)',
    [
        f'Производитель: CHINA',
        f'Тип: Синхронный Тяговый На Постоянных Магнитах',
        f'Серийный номер: 19500974',
        f'Датчик положения: Резольвер'
    ],
    f'Инвертор(traction_drive_control_unit)',
    [
        f'Производитель: CHINA',
        f'Ревизия: --',
        f'Версия ПО: 2',
        f'Номер инвертора: 2023020219'
    ],
    f'Плата контроля изоляции:',
    [
        f'Производитель: CHINA'
    ],
    f'Контроллер Верхнего Уровня(TTControl)',
    [
        f'	Производитель: ТТС',
        f'Версия ПО: 1.5.3',
        f'Серийный номер: 05224210000108'
    ],
    f'Блок Управления Рулевой Рейкой перед(Front_Power_Steering_Control)',
    [
        f'Производитель: Мехатроника',
        f'Ревизия: МОДИФИЦИРОВАН(S)',
        f'Версия ПО: 55',
        f'Серийный номер: 49'
    ]
    ,
    f'Блок Управления Рулевой Рейкой зад(Rear_Power_Steering_Control)',
    [
        f'Производитель: Мехатроника',
        f'Ревизия: МОДИФИЦИРОВАН(S)',
        f'Версия ПО: 55',
        f'Серийный номер: 50'
    ],
    f'Тяговая аккумуляторная батарея',
    [
        f'Производитель: Evocargo,',
        f'Версия ПО BMS: 1.58.3',
        f'Серийный номер: 051'
    ]
]

mdFile.new_list(items=nodes_properties_list)

mdFile.create_md_file()


class EvoNode():
    # __slots__ = ('name', 'manufacturer', 'software', 'serial_number', 'revision', 'type')

    def __init__(self, name, manufacturer=None, serial_number=None, software=None, revision=None, unit_type=None):
        self.name = name
        self.manufacturer = manufacturer
        self.serial_number = serial_number
        self.type = unit_type
        self.software = software
        self.revision = revision


class ChangelogMaker(MdUtils):
    def __init__(self, vats_number: int, nodes_dict: dict[str:EVONode], file_name: str = None):
        if file_name is None:
            file_name = 'Changelog_my.md'
        super().__init__(file_name, title='Что установлено на ВАТС')
        self.new_paragraph("При изменении ПО либо изменении настроек любого блока на ВАТС следует это записать здесь")
        self.new_paragraph()

        self.new_header(level=1, title="ВАТС:")
        main_list = [
            f'Номер: {vats_number}',
            f'Дата изменения файла: {datetime.datetime.today().strftime("%Y-%m-%d-%H.%M.%S")}'
        ]
        self.new_list(items=main_list)
        self.new_paragraph()

        self.new_header(level=1, title="Установлено:")
        motor = EvoNode(name='Двигатель(drive_motor)')
        if 'Инвертор_МЭИ' in nodes_dict.keys():
            motor.manufacturer='Evocargo'
            motor.type = 'Синхронный Тяговый Вентильный Индукторный'
            motor.serial_number = param_from_address(nodes_dict['Инвертор_МЭИ'], )
        else:
            motor.manufacturer='CHINA'
            motor.type = 'Синхронный Тяговый На Постоянных Магнитах'
