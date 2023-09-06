import sys

from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton, QStyle, QApplication, QToolButton, QStylePainter, \
    QStyleOptionButton
from PyQt6.uic.properties import QtCore


class Widget(QWidget):

    def __init__(self, parent=None):
        super(Widget, self).__init__()

        icons = [
            'SP_ArrowBack',
            'SP_ArrowDown',
            'SP_ArrowForward',
            'SP_ArrowLeft',
            'SP_ArrowRight',
            'SP_ArrowUp',
            'SP_BrowserReload',
            'SP_BrowserStop',
            'SP_CommandLink',
            'SP_ComputerIcon',
            'SP_CustomBase',
            'SP_DesktopIcon',
            'SP_DialogApplyButton',
            'SP_DialogCancelButton',
            'SP_DialogCloseButton',
            'SP_DialogDiscardButton',
            'SP_DialogHelpButton',
            'SP_DialogNoButton',
            'SP_DialogOkButton',
            'SP_DialogOpenButton',
            'SP_DialogResetButton',
            'SP_DialogSaveButton',
            'SP_DialogYesButton',
            'SP_DirClosedIcon',
            'SP_DirHomeIcon',
            'SP_DirIcon',
            'SP_DirLinkIcon',
            'SP_DirOpenIcon',
            'SP_DockWidgetCloseButton',
            'SP_DriveCDIcon',
            'SP_DriveDVDIcon',
            'SP_DriveFDIcon',
            'SP_DriveHDIcon',
            'SP_DriveNetIcon',
            'SP_FileDialogBack',
            'SP_FileDialogContentsView',
            'SP_FileDialogDetailedView',
            'SP_FileDialogEnd',
            'SP_FileDialogInfoView',
            'SP_FileDialogListView',
            'SP_FileDialogNewFolder',
            'SP_FileDialogStart',
            'SP_FileDialogToParent',
            'SP_FileIcon',
            'SP_FileLinkIcon',
            'SP_MediaPause',
            'SP_MediaPlay',
            'SP_MediaSeekBackward',
            'SP_MediaSeekForward',
            'SP_MediaSkipBackward',
            'SP_MediaSkipForward',
            'SP_MediaStop',
            'SP_MediaVolume',
            'SP_MediaVolumeMuted',
            'SP_MessageBoxCritical',
            'SP_MessageBoxInformation',
            'SP_MessageBoxQuestion',
            'SP_MessageBoxWarning',
            'SP_TitleBarCloseButton',
            'SP_TitleBarContextHelpButton',
            'SP_TitleBarMaxButton',
            'SP_TitleBarMenuButton',
            'SP_TitleBarMinButton',
            'SP_TitleBarNormalButton',
            'SP_TitleBarShadeButton',
            'SP_TitleBarUnshadeButton',
            'SP_ToolBarHorizontalExtensionButton',
            'SP_ToolBarVerticalExtensionButton',
            'SP_TrashIcon',
            'SP_VistaShield'
        ]

        icons2 = [
            'SP_TitleBarMenuButton',
            'SP_TitleBarMinButton',
            'SP_TitleBarMaxButton',
            'SP_TitleBarCloseButton',
            'SP_TitleBarNormalButton',
            'SP_TitleBarShadeButton',
            'SP_TitleBarUnshadeButton',
            'SP_TitleBarContextHelpButton',
            'SP_DockWidgetCloseButton',
            'SP_MessageBoxInformation',
            'SP_MessageBoxWarning',
            'SP_MessageBoxCritical',
            'SP_MessageBoxQuestion',
            'SP_DesktopIcon',
            'SP_TrashIcon',
            'SP_ComputerIcon',
            'SP_DriveFDIcon',
            'SP_DriveHDIcon',
            'SP_DriveCDIcon',
            'SP_DriveDVDIcon',
            'SP_DriveNetIcon',
            'SP_DirOpenIcon',
            'SP_DirClosedIcon',
            'SP_DirLinkIcon',
            'SP_FileIcon',
            'SP_FileLinkIcon',
            'SP_ToolBarHorizontalExtensionButton',
            'SP_ToolBarVerticalExtensionButton',
            'SP_FileDialogStart',
            'SP_FileDialogEnd',
            'SP_FileDialogToParent',
            'SP_FileDialogNewFolder',
            'SP_FileDialogDetailedView',
            'SP_FileDialogInfoView',
            'SP_FileDialogContentsView',
            'SP_FileDialogListView',
            'SP_FileDialogBack',
            'SP_DirIcon',
            'SP_DialogOkButton',
            'SP_DialogCancelButton',
            'SP_DialogHelpButton',
            'SP_DialogOpenButton',
            'SP_DialogSaveButton',
            'SP_DialogCloseButton',
            'SP_DialogApplyButton',
            'SP_DialogResetButton',
            'SP_DialogDiscardButton',
            'SP_DialogYesButton',
            'SP_DialogNoButton',
            'SP_ArrowUp',
            'SP_ArrowDown',
            'SP_ArrowLeft',
            'SP_ArrowRight',
            'SP_ArrowBack',
            'SP_ArrowForward',
            'SP_DirHomeIcon',
            'SP_CommandLink',
            'SP_VistaShield',
            'SP_BrowserReload',
            'SP_BrowserStop',
            'SP_MediaPlay',
            'SP_MediaStop',
            'SP_MediaPause',
            'SP_MediaSkipForward',
            'SP_MediaSkipBackward',
            'SP_MediaSeekForward',
            'SP_MediaSeekBackward',
            'SP_MediaVolume',
            'SP_MediaVolumeMuted',
            'SP_DirLinkOpenIcon',
            'SP_LineEditClearButton',
            'SP_DialogYesToAllButton',
            'SP_DialogNoToAllButton',
            'SP_DialogSaveAllButton',
            'SP_DialogAbortButton',
            'SP_DialogRetryButton',
            'SP_DialogIgnoreButton',
            'SP_RestoreDefaultsButton',
            'SP_TabCloseButton',
            'SP_CustomBase',

        ]

        colSize = 4

        layout = QGridLayout()

        col = 0
        row = 0
        for i in icons:
            btn = QPushButton(i)
            btn.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, i)))
            # btn.setStyleSheet('QPushButton{ padding-top:16px; background-position:14px left; }')
            layout.addWidget(btn, row, col)
            col += 1
            if col > colSize:
                col = 0
                row += 1

        t_btn = QToolButton()
        t_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        t_btn.setText('Start')
        # t_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        t_btn.setFixedHeight(150)
        t_btn.setFixedWidth(150)
        # t_btn.setStyleSheet("QToolButton {margin-left: 15px; image-position:bottom; border: 2px solid #8f8f91; border-radius: 6px; text-align:bottom; background-color: rgb(255, 55, 255); top_right_radius:15px}")
        t_btn.setIconSize(QSize(50, 50))     #background-position:4px left;
        layout.addWidget(t_btn)
        self.setLayout(layout)


def QPushButtonPlus(QPaintEvent):

    # // Основа кнопки.
    StylePainter = QStylePainter()
    StyleOption = QStyleOptionButton()
    # initStyleOption(&StyleOption);
    StyleOption.text.clear()
    StyleOption.icon = QIcon()
    StylePainter.drawControl(QStyle.ControlElement.CE_PushButton, StyleOption)

    # // Прямоугольник для рисования содержимого.
    SubRect = QRect()
    SubRect.style().subElementRect(QStyle.SubElement.SE_PushButtonContents, StyleOption, self)

    # // Иконка.
    # if (!icon().isNull()) {
    #     QPixmap Pixmap = icon().pixmap(iconSize());
    #     int y = (SubRect.height() - Pixmap.height()) / 2;
    #     StylePainter.drawPixmap(SubRect.x(), SubRect.y() + y, Pixmap);
    #     SubRect.setX(Pixmap.width() + 2* SubRect.x());
    # }

    # // Текст.
    # if (!text().isEmpty()) {
    #     QTextOption TextOption;
    #     TextOption.setAlignment(Qt::AlignCenter);
    #     StylePainter.drawText(SubRect, text(), TextOption);
    # }


if __name__ == '__main__':
    app = QApplication(sys.argv)

    dialog = Widget()
    dialog.show()

    app.exec()
