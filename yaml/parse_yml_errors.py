import yaml

file = "vmu_errors.yml"

with open(file, "r", encoding="UTF8") as stream:
    try:
        canopen_vmu_ttc = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

parse_list = []
for err in canopen_vmu_ttc['vmu_errors']:
    err['name_error'] = err['name_ru']
    if err['description']:
        err['description_error'] = err['description'].strip()
    err['value_error'] = err['code']
    err['critical'] = True if err['code'] & (1 << 5) else False
    del err['description']
    del err['name_ru']
    del err['hardware_id']
    parse_list.append(err)


with open(r'errors.yaml', 'w', encoding='UTF-8') as file:
    documents = yaml.dump(parse_list, file, allow_unicode=True)
