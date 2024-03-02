from PyQt5 import QtWidgets
from GraphicsView import GraphicsView
from Inpainter import Inpainter
import sys
import os
import cv2

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        # 清理.temp_result文件夹
        if os.path.exists('./.temp_result'):
            for file in os.listdir('./.temp_result'):
                os.remove(os.path.join('./.temp_result', file))
        
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Image Inpainter")

        screen = QtWidgets.QDesktopWidget().screenGeometry()
        window_rect = self.geometry()
        x = (screen.width() - window_rect.width()) // 2
        y = (screen.height() - window_rect.height()) // 2
        self.move(x, y)

        self.central_widget = GraphicsView(self)
        self.inpainter = Inpainter(self)

        self.setCentralWidget(self.central_widget)
        self.statusBar() 

        self.create_actions()
        self.create_menus()
    

    def create_actions(self):
        self.open_image_action = QtWidgets.QAction("Open Image", self)
        self.open_image_action.setShortcut("Ctrl+O")
        self.open_image_action.triggered.connect(self.central_widget.open_image)

        self.save_mask_action = QtWidgets.QAction("Save Mask", self)
        self.save_mask_action.triggered.connect(self.central_widget.save_mask)

        self.save_image_action = QtWidgets.QAction("Save Image", self)
        self.save_image_action.setShortcut("Ctrl+S")
        self.save_image_action.triggered.connect(self.central_widget.save_image)

        self.increase_radius_action = QtWidgets.QAction("Increase Radius", self)
        self.increase_radius_action.setShortcut("Ctrl+=")
        self.increase_radius_action.triggered.connect(self.central_widget.increase_radius)

        self.decrease_radius_action = QtWidgets.QAction("Decrease Radius", self)
        self.decrease_radius_action.setShortcut("Ctrl+-")
        self.decrease_radius_action.triggered.connect(self.central_widget.decrease_radius)

         # 新增动作
        self.repair_action = QtWidgets.QAction("Inpaint", self)
        self.repair_action.triggered.connect(self.inpaint_single)  # 连接到修复函数

        self.batch_process_action = QtWidgets.QAction("Batch Inpaint", self)
        self.batch_process_action.triggered.connect(self.inpaint_batch)  # 连接到批处理函数

    def create_menus(self):
        self.file_menu = self.menuBar().addMenu("File")
        self.file_menu.addAction(self.open_image_action)
        self.file_menu.addAction(self.save_mask_action)
        self.file_menu.addAction(self.save_image_action)
        
        self.edit_menu = self.menuBar().addMenu("Edit")  # 新增编辑菜单
        self.edit_menu.addAction(self.increase_radius_action)
        self.edit_menu.addAction(self.decrease_radius_action)

        # 新增Inpaint菜单
        self.inpaint_menu = self.menuBar().addMenu("ImageInpaint")
        self.inpaint_menu.addAction(self.repair_action)
        self.inpaint_menu.addAction(self.batch_process_action)

    def inpaint_single(self):
        input_location = self.central_widget.file_name
        if input_location is None:
            self.statusBar().showMessage("No image to inpaint")
            return
        # self.parent.statusBar().showMessage("image path: " + input_location)

        options = QtWidgets.QFileDialog.Options()        
        # 打开掩模文件选择对话框
        input_mask_location, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择Mask", "", "Image Files (*.png *.jpg *.jpeg)", options=options)
        if not input_mask_location:
            return  # 如果没有选择文件，就直接返回
    
        # 检查文件是否以.png结尾
        _, file_extension = os.path.splitext(input_mask_location)
        if file_extension.lower() != '.png':
            self.statusBar().showMessage("mask must be a .png file")
            return
        
        mask_img = cv2.imread(input_mask_location, cv2.IMREAD_UNCHANGED)
        input_img = cv2.imread(input_location, cv2.IMREAD_UNCHANGED)

        if input_img is None or mask_img is None or mask_img.shape[:2] != input_img.shape[:2]:
            self.statusBar().showMessage("mask and image must have the same size")
            return

        self.statusBar().showMessage("正在修复，请稍等...")
        self.inpainter.inpaint_single(input_location, input_mask_location)
    
    def inpaint_batch(self):
        # 选择包含图片的文件夹
        options = QtWidgets.QFileDialog.Options()
        images_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "选择图片文件夹", options=options)
        if not images_dir:
            return  # 用户取消操作

        # 选择包含掩码的文件夹
        masks_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "选择掩码文件夹", options=options)
        if not masks_dir:
            return  # 用户取消操作

        # 选择保存结果的文件夹
        save_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "选择保存位置", options=options)
        if not save_dir:
            return  # 用户取消操作

        self.statusBar().showMessage("正在检查文件格式，请稍等...")
        # 获取图片和掩码文件列表
        image_files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
        mask_files = [f for f in os.listdir(masks_dir) if os.path.isfile(os.path.join(masks_dir, f)) and f.endswith('.png')]

        # 检查图片和掩码数量是否一致
        if len(image_files) != len(mask_files):
            self.statusBar().showMessage("图片和掩码数量不一致")
            return

        # 检查每张图片是否有对应的掩码
        for image_file in image_files:
            mask_file = os.path.splitext(image_file)[0] + '.png'
            if mask_file not in mask_files:
                self.statusBar().showMessage(f"图片 {image_file} 没有对应的掩码")
                return

        # 检查图片和掩码尺寸是否一致
        for image_file in image_files:
            image_path = os.path.join(images_dir, image_file)
            mask_path = os.path.join(masks_dir, os.path.splitext(image_file)[0] + '.png')

            image = cv2.imread(image_path)
            mask = cv2.imread(mask_path)

            if image is None or mask is None or image.shape[:2] != mask.shape[:2]:
                self.statusBar().showMessage(f"图片和掩码 {image_file} 尺寸不一致")
                return

        self.statusBar().showMessage("检查通过，开始修复...")
        
        # 所有检查通过，执行批处理
        input_locations = [os.path.join(images_dir, f) for f in image_files]
        input_mask_locations = [os.path.join(masks_dir, os.path.splitext(f)[0] + '.png') for f in image_files]
        self.inpainter.inpaint_batch(input_locations, input_mask_locations, save_dir)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())
