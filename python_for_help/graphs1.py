"""
Demonstrates some customized mouse interaction by drawing a crosshair that follows
the mouse.
"""
from pprint import pprint

import numpy as np

import pyqtgraph as pg
from PyQt6.QtWidgets import QGraphicsProxyWidget, QPushButton

# generate layout
app = pg.mkQApp("Crosshair Example")
win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle('pyqtgraph example: crosshair')
p1 = win.addPlot(row=1, col=0)

label_c_x = pg.LabelItem(parent=p1, color='s')
label_c_y1 = pg.LabelItem(parent=p1, color='g')
label_c_y2 = pg.LabelItem(parent=p1, color='b')
label_c_x.setPos(40, -10)
label_c_y1.setPos(40, 10)
label_c_y2.setPos(40, 30)

label_x = pg.LabelItem(parent=p1, color='s')
label_y1 = pg.LabelItem(parent=p1, color='g')
label_y2 = pg.LabelItem(parent=p1, color='b')
label_x.setPos(140, -10)
label_y1.setPos(140, 10)
label_y2.setPos(140, 30)

label2_x = pg.LabelItem(parent=p1, color='s')
label2_y1 = pg.LabelItem(parent=p1, color='g')
label2_y2 = pg.LabelItem(parent=p1, color='b')
label2_x.setPos(240, -10)
label2_y1.setPos(240, 10)
label2_y2.setPos(240, 30)

text = pg.TextItem(
    html='<div style="text-align: center"><span style="color: #FFF;">This is the</span><br><span style="color: #FF0; '
         'font-size: 16pt;">PEAK</span></div>',
    anchor=(-0.7, 0.5), border='w', fill=(0, 0, 255, 100))
p1.addItem(text)
text.setPos(2000, 20000)

start_stop_btn = pg.ColorButton('СТОП')
# customize the averaged curve that can be activated from the context menu:
p1.avgPen = pg.mkPen('#FFFFFF')
p1.avgShadowPen = pg.mkPen('#8080DD', width=10)

p2 = win.addPlot(row=2, col=0)

region = pg.LinearRegionItem()
region.setZValue(20)
# Add the LinearRegionItem to the ViewBox, but tell the ViewBox to exclude this
# item when doing auto-range calculations.
p2.addItem(region, ignoreBounds=True)

p1.setAutoVisible(y=True)

# create numpy arrays
# make the numbers large to show that the range shows data from 10000 to all the way 0
data1 = 10000 + 15000 * pg.gaussianFilter(np.random.random(size=10000), 10) + 3000 * np.random.random(size=10000)
data2 = 15000 + 15000 * pg.gaussianFilter(np.random.random(size=10000), 10) + 3000 * np.random.random(size=10000)

p1.plot(data1, pen="r")
p1.plot(data2, pen="g")

p2d = p2.plot(data1, pen="w")
# bound the LinearRegionItem to the plotted data
region.setClipItem(p2d)


def update():
    region.setZValue(20)
    minX, maxX = region.getRegion()
    p1.setXRange(minX, maxX, padding=0)


region.sigRegionChanged.connect(update)


def updateRegion(window, viewRange):
    rgn = viewRange[0]
    region.setRegion(rgn)


p1.sigRangeChanged.connect(updateRegion)

region.setRegion([1000, 2000])

# cross hair
vLine = pg.InfiniteLine()
firstLine = pg.InfiniteLine(pen='r')
secondLine = pg.InfiniteLine(pen='g')
p1.addItem(vLine, ignoreBounds=True)

proxy = QGraphicsProxyWidget(parent=p1)
button = QPushButton('СБРОС')
button.setBaseSize(50, 50)
proxy.setWidget(button)

proxy.setPos(0, 0)
vb = p1.vb


def del_lines():
    if firstLine in p1.items:
        p1.removeItem(firstLine)
    if secondLine in p1.items:
        p1.removeItem(secondLine)
    label_x.hide()
    label_y1.hide()
    label_y2.hide()

    label2_x.hide()
    label2_y1.hide()
    label2_y2.hide()


def mouseMoved(pos):
    if p1.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        index = int(mousePoint.x())
        if 0 < index < len(data1):
            label_c_x.setText(f'x={round(mousePoint.x(), 2)}')
            label_c_y1.setText(f'y1={round(data1[index], 2)}')
            label_c_y2.setText(f'y2={round(data2[index], 2)}')
        vLine.setPos(mousePoint.x())


def mouseClicked(evt):
    pos = evt.scenePos()

    if p1.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        index = int(mousePoint.x())
        if firstLine not in p1.items:
            p1.addItem(firstLine, ignoreBounds=True)
            firstLine.setPos(mousePoint.x())
            if 0 < index < len(data1):  # сделать вторую метку, где при нажатии мыши
                # будут сохраняться заданная первая, вторая позиция и их разница
                label_x.setText(f'x={round(mousePoint.x(), 2)}')
                label_y1.setText(f'y1={round(data1[index], 2)}')
                label_y2.setText(f'y2={round(data2[index], 2)}')
                label_x.show()
                label_y1.show()
                label_y2.show()
        else:
            if secondLine not in p1.items:
                p1.addItem(secondLine, ignoreBounds=True)
            secondLine.setPos(firstLine.getXPos())
            firstLine.setPos(mousePoint.x())
            old_x = float(label_x.text.split('=')[1])
            old_y1 = float(label_y1.text.split('=')[1])
            old_y2 = float(label_y2.text.split('=')[1])
            if 0 < index < len(data1):
                label_x.setText(f'1x={round(old_x, 2)}')
                label_y1.setText(f'1y1={round(old_y1, 2)}')
                label_y2.setText(f'1y2={round(old_y2, 2)}')

                label2_x.setText(f'2x={round(mousePoint.x(), 2)}, delta x={round(mousePoint.x() - old_x, 2)}')
                label2_y1.setText(f'2y1={round(data1[index], 2)}, delta y1={round(data1[index] - old_y1, 2)}')
                label2_y2.setText(f'2y2={round(data2[index], 2)}, delta y2={round(data2[index] - old_y2, 2)}')
                label2_x.show()
                label2_y1.show()
                label2_y2.show()


p1.scene().sigMouseMoved.connect(mouseMoved)
p1.scene().sigMouseClicked.connect(mouseClicked)
button.clicked.connect(del_lines)

if __name__ == '__main__':
    pg.exec()
