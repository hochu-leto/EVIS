import math
import yaml
import pandas as pd
from tkinter import filedialog


def yaml_to_xlsx(yams_file: str) -> dict[str:dict] | None:
    empty_dict = dict(
        value='Значение',
        units='Ед. изм.',
        type='Тип',
        widget='Вид',
        index='Адрес',
        editable='Запись',
        min_value='Мин.',
        max_value='Макс.',
        multiplier='Коэф-т',
        value_table='Строки',
        description='Описание',
    )

    x_dict = {e: '' for e in empty_dict.values()}
    yaml_file = open(yams_file, "r", encoding='UTF-8')
    python_dict = yaml.load(yaml_file, Loader=yaml.FullLoader)
    main_dict = {}
    try:
        python_dict = python_dict['device']['parameters']
    except KeyError:
        print('Неправильный  yaml-файл')
        return None

    for group, params in python_dict.items():
        main_dict[group] = x_dict
        for param in params:
            par = x_dict.copy()
            for key in empty_dict.keys():
                if key in param.keys():
                    if key == 'multiplier':
                        if param[key]:
                            par[empty_dict[key]] = math.log10(1 / param[key])
                    elif key == 'editable':
                        par[empty_dict[key]] = 1 if param[key] else ''
                    else:
                        par[empty_dict[key]] = param[key]
            main_dict[param['name']] = par.copy()
    return main_dict


if __name__ == '__main__':
    file_name = filedialog.askopenfilename()
    d = yaml_to_xlsx(file_name)
    if d:
        df = pd.DataFrame.from_dict(d, orient="index")
        df.to_excel(file_name.split('yaml')[0] + 'xlsx')
