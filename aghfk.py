a = 11
match a:
    case range(-10000000, 0):
        print('minus')
    case range(0, 10):
        print('under 10')
    case range(10, 100):
        print('from 10 to 100')
    case range(100, 100000):
        print('big')