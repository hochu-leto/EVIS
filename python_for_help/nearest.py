def get_nearest_value(iterable, value):
    if value in iterable:
        return value
    iterable.append(value)
    iterable.sort()
    ind = iterable.index(value)
    return iterable[ind-1] if ind else ind


if __name__ == '__main__':
    delimeter = 0.1           # различные тестовые условия
    max_range = 100000        # различные тестовые условия
    # test_list = [delimeter * (x + 1) for x in range(max_range)]
    test_list = [48, 5, 32, 34, 52, 55]

    test_value = 4  # любое число

    print()
    print('тестовое значение:', test_value)
    print('ближайшее значение:', get_nearest_value(test_list, test_value))
