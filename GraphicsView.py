from PyQt5 import QtWidgets, QtGui, QtCore

class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.parent = parent
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)
        self.image_item = QtWidgets.QGraphicsPixmapItem()
        self.mask_item = QtWidgets.QGraphicsPixmapItem()  # 新增mask层
        self.mask_item.setVisible(False)  # 设置mask图层的可见性
        
        self.scene.addItem(self.image_item)
        self.scene.addItem(self.mask_item)  # 将mask层添加到场景中

        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform | QtGui.QPainter.TextAntialiasing)
        self.setOptimizationFlags(QtWidgets.QGraphicsView.DontAdjustForAntialiasing | QtWidgets.QGraphicsView.DontSavePainterState)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.image = QtGui.QPixmap()
        self.mask = QtGui.QPixmap()  # 新增mask QPixmap
        self.painter = QtGui.QPainter()

        self.pen = QtGui.QPen()
        self.pen.setWidth(10)
        self.pen.setColor(QtGui.QColor(QtCore.Qt.white))
        self.last_point = None
        self.drawing_radius = 5  # 新增绘制半径
        self.file_name = None

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        factor = pow(1.0015, angle)
        self.scale(factor, factor)

    def open_image(self):
        options = QtWidgets.QFileDialog.Options()
        self.file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)", options=options)
        if self.file_name:
            self.image.load(self.file_name)
            self.image_item.setPixmap(self.image)
            self.mask = QtGui.QPixmap(self.image.size())  # 初始化mask大小与图像相同
            self.mask.fill(QtCore.Qt.black)  # 使用黑色填充mask
            self.mask_item.setPixmap(self.mask)
            
            self.reset_graphics()

    
    def load_image(self, image):
        # 将修补后的图像（NumPy数组）转换为QImage
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_img = QtGui.QImage(image.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888).rgbSwapped()

        # 将QImage转换为QPixmap，并在GraphicsView中显示
        self.image = QtGui.QPixmap.fromImage(q_img)
        self.image_item.setPixmap(self.image)
        self.mask = QtGui.QPixmap(self.image.size())  # 初始化mask大小与图像相同
        self.mask.fill(QtCore.Qt.black)  # 使用黑色填充mask
        self.mask_item.setPixmap(self.mask)

        self.reset_graphics()

    def reset_graphics(self):
        # 重置视图的变换状态
        self.resetTransform()
        # 更新场景的矩形区域以匹配新图像的尺寸
        rect = self.image.rect()
        # 将QRect的坐标和尺寸提取出来，并传递给setSceneRect
        self.setSceneRect(QtCore.QRectF(rect.x(), rect.y(), rect.width(), rect.height()))
        # 根据需要调整滚动条政策
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

    def save_mask(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Mask", "mask.png", "PNG Files (*.png)", options=options)  # 修改为保存PNG格式
        if file_path:
            self.mask.save(file_path)  # 保存mask层
    
    def save_image(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Image", "image.png", "PNG Files (*.png *.jpg *.jpeg *.bmp)", options=options)
        if file_path:
            self.image.save(file_path)

    def mousePressEvent(self, event):
        self.last_point = self.mapToScene(event.pos())

    def mouseMoveEvent(self, event):
        if self.last_point:
            current_point = self.mapToScene(event.pos())
            # 在原始图像上进行绘制
            self.painter.begin(self.image)
            self.painter.setPen(self.pen)
            self.painter.drawLine(self.last_point, current_point)
            self.painter.end()
            # 在mask层上进行相同的绘制
            self.painter.begin(self.mask)
            self.painter.setPen(self.pen)
            self.painter.drawLine(self.last_point, current_point)
            self.painter.end()
            self.last_point = current_point
            self.image_item.setPixmap(self.image)
            self.mask_item.setPixmap(self.mask)  # 更新mask层显示

    def mouseReleaseEvent(self, event):
        self.last_point = None

    def increase_radius(self):
        self.drawing_radius += 5
        self.pen.setWidth(self.drawing_radius * 2)
        self.parent.statusBar().showMessage(f"Drawing Radius: {self.drawing_radius}")

    def decrease_radius(self):
        self.drawing_radius = max(5, self.drawing_radius - 5)
        self.pen.setWidth(self.drawing_radius * 2)
        self.parent.statusBar().showMessage(f"Drawing Radius: {self.drawing_radius}")