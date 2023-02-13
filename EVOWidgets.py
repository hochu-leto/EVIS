from PyQt6.QtCore import pyqtSignal, QSize, Qt, QPropertyAnimation, QEasingCurve, QObject, QPointF, pyqtProperty, \
    QRegularExpression, QStringListModel
from PyQt6.QtGui import QPainter, QPalette, QLinearGradient, QGradient, QRegularExpressionValidator
from PyQt6.QtWidgets import QComboBox, QLabel, QLineEdit, QProgressBar, QSlider, QDoubleSpinBox, QPushButton, \
    QAbstractButton, QSizePolicy, QListView


def zero_del(s):
    return f'{round(s, 5):>8}'.rstrip('0').rstrip('.') if s is not None else 'NaN'


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

    def setText(self, text=None):
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
        self.editingFinished.connect(self.end_edited_handle)

    def end_edited_handle(self):
        lst = []
        if self.parametr is not None:
            value = float(self.text())
            lst = [self.parametr, value]
        self.ValueSelected.emit(lst)

    def focusInEvent(self, event):
        self.isInFocus = True
        self.FocusInSignal.emit(self)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.isInFocus = False
        super().focusOutEvent(event)
        self.FocusOutSignal.emit()

    def setText(self, text=None):
        if text is not None:
            self.setText(text)
        if hasattr(self.parametr, 'value'):
            if self.parametr.value_string:
                v_name = self.parametr.value_string
            elif isinstance(self.parametr.value, str):
                v_name = self.parametr.value
            elif self.parametr.value_table:
                k = int(self.parametr.value)
                if k in self.parametr.value_table:
                    v_name = self.parametr.value_table[k]
                else:
                    v_name = f'{k} нет в словаре'
            else:
                v_name = zero_del(self.parametr.value)
            self.setText(v_name)


class MyColorBar(QProgressBar):

    def __init__(self, parent=None, parametr=None, max_limit=None, min_limit=None, color_bar=None):
        super(QProgressBar, self).__init__(parent)
        self.parametr = parametr
        self.max_limit = max_limit
        self.min_limit = min_limit
        self.color_bar = color_bar


class MySlider(QSlider, QDoubleSpinBox):

    def __init__(self, parent=None, parametr=None, max_limit=None, min_limit=None, color_bar=None):
        super(QSlider, self).__init__(parent)
        super(QDoubleSpinBox, self).__init__(parent)
        self.parametr = parametr
        self.max_limit = max_limit
        self.min_limit = min_limit
        self.color_bar = color_bar


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
        margin = r.height()/10
        shadow = self.mPointer.palette().color(QPalette.ColorRole.Dark)
        light = self.mPointer.palette().color(QPalette.ColorRole.Light)
        button = self.mPointer.palette().color(QPalette.ColorRole.Button)
        painter.setPen(Qt.PenStyle.NoPen)

        self.mGradient.setColorAt(0, shadow.darker(130))
        self.mGradient.setColorAt(1, light.darker(130))
        self.mGradient.setStart(0, r.height())
        self.mGradient.setFinalStop(0, 0)
        painter.setBrush(self.mGradient)
        painter.drawRoundedRect(r, r.height()/2, r.height()/2)

        self.mGradient.setColorAt(0, shadow.darker(140))
        self.mGradient.setColorAt(1, light.darker(160))
        self.mGradient.setStart(0, 0)
        self.mGradient.setFinalStop(0, r.height())
        painter.setBrush(self.mGradient)
        painter.drawRoundedRect(r.adjusted(margin, margin, -margin, -margin), r.height()/2, r.height()/2)

        self.mGradient.setColorAt(0, button.darker(130))
        self.mGradient.setColorAt(1, button)

        painter.setBrush(self.mGradient)

        x = r.height()/2.0 + self.mPosition*(r.width()-r.height())
        painter.drawEllipse(QPointF(x, r.height()/2), r.height()/2-margin, r.height()/2-margin)


