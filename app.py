#!/usr/bin/env python
__author__ = "黄辉(Huang, Hui)"
__copyright__ = "Copyright (C) 2022, IUH.APP"
__credits__ = ["Tencent"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Hui Huang"
__email__ = "hhchina81@outlook.com"
__status__ = "Production"

import sys
import os
import cv2
import numpy as np

from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, 
    QHBoxLayout, 
    QMainWindow, 
    QPushButton, 
    QVBoxLayout, 
    QWidget, 
    QFileDialog, 
    QLabel, 
    QErrorMessage)
from PyQt6.QtGui import QImage, QPixmap, QMovie, QIcon
from PyQt6.QtCore import QRunnable, QObject, QThreadPool, pyqtSignal, pyqtSlot

from gfpgan_restorer import restore

basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'iuh.app.yungangdebut.1'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

def fit_image(cv2Image, viewer_witdh, viewer_height):
    image_width = cv2Image.shape[1]
    image_height = cv2Image.shape[0]
    fit_width = -1
    fit_height = -1

    if image_width >= image_height:
        scale_by_width = viewer_witdh / image_width
        fit_width = viewer_witdh
        fit_height = int(image_height * scale_by_width)
    else:
        scale_by_height = viewer_height / image_height
        fit_width = int(image_width * scale_by_height)
        fit_height = viewer_height
    
    fit_size = (fit_width, fit_height)
    resized_image = cv2.resize(cv2Image, fit_size, None, None, None, cv2.INTER_AREA)
    return resized_image

def cv2Pixmap(cv2Image):
    height, width, channel = cv2Image.shape
    bytesPerLine = 3 * width
    q_image = QImage(
        cv2Image.data, 
        width, 
        height, 
        bytesPerLine, 
        QImage.Format.Format_RGB888).rgbSwapped()
    return QPixmap(q_image)


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
    
    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            print("[ERROR!] Running restoring threading")
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class ImageViewer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(False)
    
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("云冈初见")
        icon_path = os.path.join(basedir, 'assets', "app_icon.png")
        self.setWindowIcon(QIcon(icon_path))
        main_width = 1400
        main_height = 700
        self.setFixedSize(main_width, main_height)

        self.original_image = None
        self.original_cv2Image = None
        self.processed_cv2Image = None
        # fixed image viewer size: 600x600
        self.viewer_width = 600
        self.viewer_height = 600

        main_container = QVBoxLayout()
        top_part = QHBoxLayout()
        btm_part = QHBoxLayout()
        
        self.original_viewer = ImageViewer()
        self.processed_viewer = ImageViewer()
        self.original_viewer.setFixedSize(self.viewer_width, self.viewer_height)
        self.processed_viewer.setFixedSize(self.viewer_width, self.viewer_height)

        top_left_layout = QVBoxLayout()
        top_left_layout.addWidget(QLabel("未经处理的原图片"))
        top_left_layout.addWidget(self.original_viewer)

        top_right_layout = QVBoxLayout()
        top_right_layout.addWidget(QLabel("修复处理后的图片"))
        top_right_layout.addWidget(self.processed_viewer)

        top_part.addLayout(top_left_layout)
        top_part.addLayout(top_right_layout)

        open_btn = QPushButton("打开图片")
        open_btn.setFixedSize(300, 30)
        open_btn.clicked.connect(self.load_image)

        process_btn = QPushButton("处理图片")
        process_btn.setFixedSize(300, 30)
        process_btn.clicked.connect(self.process_image)

        save_btn = QPushButton("保存图片")
        save_btn.setFixedSize(300, 30)
        save_btn.clicked.connect(self.save_image)

        btm_part.addWidget(open_btn)
        btm_part.addWidget(process_btn)
        btm_part.addWidget(save_btn)

        main_container.addLayout(top_part)
        main_container.addLayout(btm_part)

        widget = QWidget()
        widget.setLayout(main_container)
        self.setCentralWidget(widget)

    def load_image(self):
        home_dir = str(Path.home())
        source_file = QFileDialog.getOpenFileName(
            self, 
            "打开图片文件",
            home_dir,
            "Image Files (*.png *.jpg)")
        if len(source_file[0]) > 0:
            self.original_image = source_file[0]
            self.original_cv2Image = cv2.imread(self.original_image)
            resized_original = fit_image(self.original_cv2Image, self.viewer_width, self.viewer_height)
            self.original_viewer.setPixmap(cv2Pixmap(resized_original))
    
    def display_processed(self, processed_result):
        self.processed_cv2Image = processed_result
        resized_processed = fit_image(self.processed_cv2Image, self.viewer_width, self.viewer_height)
        self.processed_viewer.setPixmap(cv2Pixmap(resized_processed))

    def process_image(self):
        if self.original_cv2Image is None:
            error_dialog = QErrorMessage()
            error_dialog.showMessage("未找到需要处理的图片数据！")
            error_dialog.exec()
        else:
            gif_path = os.path.join(basedir, 'assets', "Pulse_transparent_600px.gif")
            processing_animation = QMovie(gif_path)
            self.processed_viewer.setMovie(processing_animation)
            processing_animation.start()
            
            cv2Image0 = cv2.imread(self.original_image, cv2.IMREAD_COLOR)

            self.threadpool = QThreadPool()
            worker = Worker(restore, cv2Image0)
            worker.signals.result.connect(self.display_processed)
            self.threadpool.start(worker)
            
    def save_image(self):
        if self.processed_cv2Image is None:
            error_dialog = QErrorMessage()
            error_dialog.showMessage("未找到处理后的图片数据！")
            error_dialog.exec()
        else:
            save_to = QFileDialog.getSaveFileName(
                self, 
                '保存图片文件', 
                "Untitled", 
                "Image Files (*.png *.jpg)")
            if len(save_to[0]) > 0:
                destination = save_to[0]
                cv2.imwrite(destination, self.processed_cv2Image)


app = QApplication([])

window = MainWindow()
window.show()

app.exec()