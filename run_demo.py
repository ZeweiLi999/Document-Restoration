import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QPushButton, QLabel,QComboBox
from inference import inference_one_im
from PyQt6 import uic

# 定义全局变量
selected_file = None
refined_file = None
refined_file_qimg = None
task = 'deshadow'


def getFile():
    global selected_file  # 使用全局变量
    fd = QFileDialog()
    fd.setFileMode(QFileDialog.FileMode.ExistingFile)  # 设置单选
    fd.setDirectory('./')  # 设置初始化路径
    fd.setNameFilter('图片文件(*.jpg *.png *.bmp *.ico *.gif)')  # 设置只选择图片文件
    if fd.exec():  # 执行
        selected_file = fd.selectedFiles()[0]  # 获取选择的文件
        label_before.setPixmap(QtGui.QPixmap(selected_file).scaled(500, 500, QtCore.Qt.AspectRatioMode.KeepAspectRatio)) # 显示选择的图像
        print(selected_file)


def runFile():
    global refined_file, refined_file_qimg,selected_file,task  # 使用全局变量
    #task =
    if selected_file:  # 检查是否选择了文件
        _,_,_, refined_file = inference_one_im(selected_file,task)

        if refined_file is not None:
            if task == 'binarization':
                # 获取图像的高度和宽度
                height, width = refined_file.shape
                bytes_per_line = width  # 灰度图每行字节数等于图像宽度
                # 创建 QImage 对象，使用 Format_Grayscale8 来表示灰度图
                refined_file_qimg = QImage(refined_file.tobytes(), width, height, bytes_per_line,
                                           QImage.Format.Format_Grayscale8)
                # 将图像显示在 QLabel 中
                label_after.setPixmap(
                    QPixmap.fromImage(refined_file_qimg).scaled(500, 500, QtCore.Qt.AspectRatioMode.KeepAspectRatio))
            else:
                height, width, channels = refined_file.shape
                bytes_per_line = channels * width
                refined_file_qimg = QImage(refined_file.tobytes() , width, height, bytes_per_line, QImage.Format.Format_RGB888)
                label_after.setPixmap(QPixmap.fromImage(refined_file_qimg).scaled(500, 500, QtCore.Qt.AspectRatioMode.KeepAspectRatio))  # 显示推理后的图像


def downFile():
    global refined_file_qimg  # 使用全局变量
    if refined_file_qimg is not None:  # 检查是否有处理后的图像
        # 弹出保存对话框
        file_path, _ = QFileDialog.getSaveFileName(None, "保存文件", "", "图片文件(*.jpg *.png *.bmp);;所有文件(*)")
        if file_path:  # 如果用户选择了文件路径
            refined_file_qimg.save(file_path)
            print(f"文件已保存: {file_path}")
    else:
        print("没有可保存的文件。")

def getboxtext():
    global task
    print("模式已切换！")
    task_cn = comBox_function.currentText()
    if task_cn == "去阴影":
        task = 'deshadow'
    elif task_cn == "提取文字":
        task = 'binarization'
    elif task_cn == "外观增强":
        task = 'appearance'
    elif task_cn == "去模糊":
        task = 'deblurring'


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = uic.loadUi("./demo.ui")  # 加载UI
    pushButton_load: QPushButton = ui.findChild(QPushButton, 'pushButton_load')  # 获取按钮实例
    pushButton_load.clicked.connect(getFile)

    pushButton_run: QPushButton = ui.findChild(QPushButton, 'pushButton_run')
    pushButton_run.clicked.connect(runFile)

    pushButton_after: QPushButton = ui.findChild(QPushButton, 'pushButton_download')  # 获取下载按钮实例
    pushButton_after.clicked.connect(downFile)

    comBox_function: QComboBox = ui.findChild(QComboBox,"comboBox_function")
    comBox_function.currentTextChanged.connect(getboxtext)

    label_before: QLabel = ui.findChild(QLabel, "label_before")  # 获取标签实例
    label_after: QLabel = ui.findChild(QLabel, "label_after")

    ui.show()

    sys.exit(app.exec())
