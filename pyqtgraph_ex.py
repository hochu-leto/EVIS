import sys

import pyqtgraph.examples
from PyQt6.QtWidgets import QApplication
from numpy.random import randint

# pyqtgraph.examples.run()

"""
Various methods of drawing scrolling plots.
"""

from time import perf_counter

import numpy as np

import pyqtgraph as pg
#
# win = pg.GraphicsLayoutWidget(show=True)
# win.setWindowTitle('pyqtgraph example: Scrolling Plots')

# 3) Plot in chunks, adding one new plot curve for every 100 samples
chunkSize = 100
# Remove chunks after we have 10
maxChunks = 10
curves = []
counter = 0
parameters = [2, 3, 4, 5]
ptr5 = 0

pens = [pg.mkPen(color=(0, 255, 0)), pg.mkPen(color=(255, 0, 0)), pg.mkPen(color=(0, 0, 255)),
        pg.mkPen(color=(0, 255, 255)), pg.mkPen(color=(255, 255, 0)), pg.mkPen(color=(255, 0, 255))]


def update3(params: list):
    global x, y, ptr5, curves
    now = perf_counter()
    # пробегаемся по списку со всеми кривыми
    # и задаём им позицию х - чтоб весь график сдвинулся влево
    for curs in curves:
        for c in curs:
            c.setPos(-(now - startTime), 0)

    i = ptr5 % chunkSize
    # я так и не понимаю зачем создаётся новый массив в 100 элементов
    # как понял, потому что 400 элементов это тяжело
    # и сохраняются в памяти только последние 100
    if i == 0:
        # когда количество кривых кратно количеству 100
        # добавляется новая пачка кривых в список
        curve = []
        for _ in params:
            curve.append(plotWidget.plot())
        curves.append(curve)
        # из старого массива достаём последний элемент
        last_x = x[-1]
        last_y = y[-1]
        # создаём новый массив причём для всех графиков
        x = np.zeros((chunkSize + 1))
        y = np.zeros((chunkSize + 1, len(params)))
        # и впихиваем в него на первую позицию последний элемент старого массива
        x[0] = last_x
        y[0] = last_y

        # если количество кусков больше 10, удаляем до 10
        while len(curves) > maxChunks:
            c = curves.pop(0)
            for cc in c:
                plotWidget.removeItem(cc)
    else:
        # если сейчас не 100я кривая, то берём последний
        curve = curves[-1]

    x[i + 1] = now - startTime

    for indx, par in enumerate(params):
        y[i + 1, indx] = par
        crv = curve[indx]
        crv.setData(x=x[:i + 2], y=y[:i + 2, indx], pen=pens[indx])
    ptr5 += 1


def update():
    global counter, parameters
    parameters[counter] = randint(-5 * (counter + 1), 10 * (counter + 1))
    counter += 1
    if counter > len(parameters) - 1:
        counter = 0
        update3(parameters)


if __name__ == '__main__':
    startTime = perf_counter()
    app = QApplication(sys.argv)
    x = np.zeros((chunkSize + 1))
    y = np.zeros((chunkSize + 1, len(parameters)))
    plotWidget = pg.plot(title="GeeksCoders.com")
    plotWidget.setXRange(- chunkSize / 10, 0)
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(10)

    status = app.exec()
    sys.exit(status)
