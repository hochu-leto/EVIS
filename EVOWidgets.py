from PyQt6.QtCore import pyqtSignal, QSize, Qt, QPropertyAnimation, QEasingCurve, QObject, QPointF, pyqtProperty, \
    QRegularExpression, QStringListModel
from PyQt6.QtGui import QPainter, QPalette, QLinearGradient, QGradient, QRegularExpressionValidator, QColor
from PyQt6.QtWidgets import QComboBox, QLabel, QLineEdit, QProgressBar, QSlider, QDoubleSpinBox, QPushButton, \
    QAbstractButton, QSizePolicy, QListView

color_EVO_red = QColor(222, 73, 14)
color_EVO_green = QColor(0, 254, 0, 80)
color_EVO_red_dark = QColor(234, 76, 76, 80)
color_EVO_orange = QColor(241, 91, 34)
color_EVO_orange_shine = QColor(255, 184, 65, 80)
color_EVO_white = QColor(255, 254, 254, 80)
color_EVO_gray = QColor(98, 104, 116, 80)
color_EVO_graphite2 = QColor(54, 60, 70, 80)
color_EVO_raven = QColor(188, 125, 136, 80)


def zero_del(s):
    return f'{round(s, 5):>8}'.rstrip('0').rstrip('.').strip() if s is not None else 'NaN'


class GreenLabel(QLabel):
    def __init__(self, parent=None):
        super(QLabel, self).__init__(parent)
        self.setStyleSheet('{background-color: rgba(0, 200, 0, 50);}')


class RedLabel(QLabel):
    def __init__(self, parent=None):
        super(QLabel, self).__init__(parent)
        self.setStyleSheet('{background-color: rgba(200, 0, 0, 50);}')


class MyComboBox(QComboBox):
    ValueSelected = pyqtSignal(list)
    isInFocus = False

    def __init__(self, parent=None, parametr=None):
        super(MyComboBox, self).__init__(parent)
        self.parametr = parametr
        self.setToolTip(str(parametr.value))
        self.currentIndexChanged.connect(self.item_selected_handle)
        if hasattr(self.parametr, 'value_table'):
            v_list = list(self.parametr.value_table.values())
            self.setModel(QStringListModel(v_list))
            # Отображатель выпадающего списка QListView
            listView = QListView()
            # Включаем перенос строк
            listView.setWordWrap(True)
            # Устанавливаем отображатель списка (popup)
            self.setView(listView)
            self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
            # .AdjustToMinimumContentsLengthWithIcon + AdjustToContentsOnFirstShow + AdjustToContents)
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.setMaximumSize(250, 250)

    def item_selected_handle(self, index):
        lst = []
        if self.parametr is not None:
            key = list(self.parametr.value_table.keys())[index]
            lst = [self.parametr, key]
        self.ValueSelected.emit(lst)

    def showPopup(self):  # sPopup function
        self.isInFocus = True
        super(MyComboBox, self).showPopup()

    def hidePopup(self):
        self.isInFocus = False
        super(MyComboBox, self).hidePopup()

    def set_text(self, text=None):
        if text is not None:
            self.setCurrentText(text)
        if hasattr(self.parametr, 'value_table'):
            self.setCurrentText(self.parametr.value_table[int(self.parametr.value)])


class MyEditLine(QLineEdit):
    ValueSelected = pyqtSignal(list)
    FocusInSignal = pyqtSignal(object)
    FocusOutSignal = pyqtSignal()
    isInFocus = False

    def __init__(self, parent=None, parametr=None):
        super(QLineEdit, self).__init__(parent)
        self.parametr = parametr
        reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
        self.setValidator(QRegularExpressionValidator(reg_ex))
        self.returnPressed.connect(self.end_edited_handle)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setToolTip(f'{parametr.min_value}...{parametr.max_value}')

    def end_edited_handle(self):
        lst = []
        if self.parametr is not None:
            value = float(self.text())
            lst = [self.parametr, value]
        # self.isInFocus = False      # <<<---- проверить
        self.ValueSelected.emit(lst)

    def focusInEvent(self, event):
        self.isInFocus = True
        self.FocusInSignal.emit(self)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.isInFocus = False
        super().focusOutEvent(event)
        self.FocusOutSignal.emit()

    def set_text(self, text=None):
        if text is not None:
            self.setText(text)
        if hasattr(self.parametr, 'value'):
            if self.parametr.value_string:
                v_name = self.parametr.value_string
            elif isinstance(self.parametr.value, str):
                v_name = self.parametr.value
            elif self.parametr.value_table:
                if self.parametr.value is not None:
                    k = int(self.parametr.value)
                    if k in self.parametr.value_table:
                        v_name = self.parametr.value_table[k]
                    else:
                        v_name = f'{k} нет в словаре'
                else:
                    v_name = f'Нет ответа'
            else:
                v_name = zero_del(self.parametr.value)
            self.setText(v_name)


class MyColorBar(QProgressBar):
    full_bar = 1000

    def __init__(self, parent=None, parametr=None):
        super(QProgressBar, self).__init__(parent)
        self.parametr = parametr
        self.multiplier = (self.parametr.max_value - self.parametr.min_value) / self.full_bar
        self.setMaximum(int(self.parametr.max_value / self.multiplier))
        self.setMinimum(int(self.parametr.min_value / self.multiplier))
        self.setToolTip(str(self.parametr.description))
        self.setTextVisible(False)
        self.set_value()

    def set_value(self, value=None):
        value = value or self.parametr.value
        try:
            value = float(value) / self.multiplier
        except ValueError:
            return
        except TypeError:
            return
        value = self.maximum() if value > self.maximum() else self.minimum() if value < self.minimum() else value
        self.setValue(int(value))


class MySlider(QSlider):
    full_bar = 1000
    ValueSelected = pyqtSignal(list)
    ValueChanged = pyqtSignal()

    def __init__(self, parent=None, parametr=None):
        super(QSlider, self).__init__(parent)
        self.parametr = parametr
        self.multiplier = (self.parametr.max_value - self.parametr.min_value) / self.full_bar
        self.setMaximum(int(self.parametr.max_value / self.multiplier))
        self.setMinimum(int(self.parametr.min_value / self.multiplier))
        self.setToolTip(str(self.parametr.description))
        self.setOrientation(Qt.Orientation.Horizontal)
        self.set_value()
        self.sliderReleased.connect(self.set_new_value)
        self.valueChanged.connect(self.value_changed_handle)

    def set_value(self, value=None):
        value = value or self.parametr.value
        try:
            value = float(value) / self.multiplier
        except ValueError:
            print(Exception, value, type(value))
            return
        except TypeError:
            print(Exception, value, type(value))
            return
        value = self.maximum() if value > self.maximum() else self.minimum() if value < self.minimum() else value
        self.setValue(int(value))

    def value_changed_handle(self):
        self.parametr.value = self.value() * self.multiplier
        self.ValueChanged.emit()

    def set_new_value(self):
        lst = []
        if self.parametr is not None:
            value = float(self.value() * self.multiplier)
            lst = [self.parametr, value]
        self.ValueSelected.emit(lst)


class MyButton(QPushButton):

    def __init__(self, parent=None, parametr=None, active_value=None, button_text=None):
        super(QPushButton, self).__init__(parent)
        self.parametr = parametr
        self.active_value = active_value
        self.button_text = button_text
        if self.button_text:
            self.setText(self.button_text)


class MySwitch(QAbstractButton):
    def __init__(self, parent=None):
        QAbstractButton.__init__(self, parent=parent)
        self.dPtr = SwitchPrivate(self)
        self.setCheckable(True)
        self.clicked.connect(self.dPtr.animate)

    def sizeHint(self):
        return QSize(42, 42)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.dPtr.draw(painter)

    def resizeEvent(self, event):
        self.update()


class SwitchPrivate(QObject):
    def __init__(self, q, parent=None):
        QObject.__init__(self, parent=parent)
        self.mPointer = q
        self.mPosition = 0.0
        self.mGradient = QLinearGradient()
        self.mGradient.setSpread(QGradient.Spread.PadSpread)

        self.animation = QPropertyAnimation(self)
        self.animation.setTargetObject(self)
        self.animation.setPropertyName(b'position')
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutExpo)

        self.animation.finished.connect(self.mPointer.update)

    @pyqtProperty(float)
    def position(self):
        return self.mPosition

    @position.setter
    def position(self, value):
        self.mPosition = value
        self.mPointer.update()

    def draw(self, painter):
        r = self.mPointer.rect()
        margin = r.height() / 10
        shadow = self.mPointer.palette().color(QPalette.ColorRole.Dark)
        light = self.mPointer.palette().color(QPalette.ColorRole.Light)
        button = self.mPointer.palette().color(QPalette.ColorRole.Button)
        painter.setPen(Qt.PenStyle.NoPen)

        self.mGradient.setColorAt(0, shadow.darker(130))
        self.mGradient.setColorAt(1, light.darker(130))
        self.mGradient.setStart(0, r.height())
        self.mGradient.setFinalStop(0, 0)
        painter.setBrush(self.mGradient)
        painter.drawRoundedRect(r, r.height() / 2, r.height() / 2)

        self.mGradient.setColorAt(0, shadow.darker(140))
        self.mGradient.setColorAt(1, light.darker(160))
        self.mGradient.setStart(0, 0)
        self.mGradient.setFinalStop(0, r.height())
        painter.setBrush(self.mGradient)
        painter.drawRoundedRect(r.adjusted(margin, margin, -margin, -margin), r.height() / 2, r.height() / 2)

        self.mGradient.setColorAt(0, button.darker(130))
        self.mGradient.setColorAt(1, button)

        painter.setBrush(self.mGradient)

        x = r.height() / 2.0 + self.mPosition * (r.width() - r.height())
        painter.drawEllipse(QPointF(x, r.height() / 2), r.height() / 2 - margin, r.height() / 2 - margin)
