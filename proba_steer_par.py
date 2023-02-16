from EVOThreads import SteerParametr


def some_func():
    def some_sub_func():
        parametr.current_value = 2
        a = 3

    parametr = SteerParametr('Some name')
    parametr.current_value = 1
    a = 1
    print(parametr.current_value, a)
    some_sub_func()
    print(parametr.current_value, a)


if __name__ == '__main__':
    some_func()
