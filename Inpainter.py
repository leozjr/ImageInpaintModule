from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import time
import cv2
import os

from PyQt5.QtCore import QThreadPool, QRunnable
import functools

class InpaintBatchTask(QRunnable):
    def __init__(self, inpainting, input_data, save_path, callback):
        super().__init__()
        self.inpainting = inpainting
        self.input_data = input_data
        self.callback = callback
        self.save_path = save_path

    def run(self):
        result = self.inpainting(self.input_data)
        vis_img = result[OutputKeys.OUTPUT_IMG]
        cv2.imwrite(self.save_path, vis_img)
        self.callback()

class InpaintSingleThread(QThread):
    finished = pyqtSignal(object)  # 用于在任务完成时发送信号，可以传递任意对象作为参数
    def __init__(self, inpainting, input_data):
        super().__init__()
        self.inpainting = inpainting
        self.input_data = input_data

    def run(self):
        result = self.inpainting(self.input_data)
        vis_img = result[OutputKeys.OUTPUT_IMG]
        self.finished.emit(vis_img)  # 发送完成信号，携带结果

class Inpainter():
    def __init__(self, parent):
        # 建立.temp_result文件夹
        if not os.path.exists('./.temp_result'):
            os.makedirs('./.temp_result')

        self.parent = parent
        self.inpainting = pipeline(Tasks.image_inpainting, model='cv_fft_inpainting_lama/')
        self.thread_pool = QThreadPool()

        self.completed_tasks = 0
        self.total_tasks = 0
        self.start_time = None
    
    # 单张修复
    def inpaint_single(self, input_location, input_mask_location):
        input_data = {
            'img': input_location,
            'mask': input_mask_location,
        }
        # 创建并启动修复线程
        self.thread = InpaintSingleThread(self.inpainting, input_data)
        self.thread.finished.connect(self.handle_single_finish)  # 连接信号到处理函数
        self.start = time.time()
        self.thread.start()

    def handle_single_finish(self, vis_img):
        # 处理修复完成的情况，更新GUI等
        self.end = time.time()
        self.parent.statusBar().showMessage("修复完成，耗时%.2f秒" % (self.end - self.start))
        cv2.imwrite('./.temp_result/repaired.png', vis_img)
        self.parent.central_widget.file_name = '.temp_result/repaired.png'
        self.parent.central_widget.load_image(vis_img)
    
    ## 批量修复
    def inpaint_batch(self, input_locations, input_mask_locations, save_path):
        self.total_tasks = len(input_locations)
        self.completed_tasks = 0
        
        self.start_time = time.time()
        for input_location, input_mask_location in zip(input_locations, input_mask_locations):
            input_data = {
                'img': input_location,
                'mask': input_mask_location,
            }
            task = InpaintBatchTask(self.inpainting, input_data, os.path.join(save_path, os.path.basename(input_location)), self.handle_batch_finish)
            self.thread_pool.start(task)

    def handle_batch_finish(self):
        self.completed_tasks += 1

        if self.completed_tasks == self.total_tasks:
            elapsed_time = time.time() - self.start_time
            self.parent.statusBar().showMessage(f"所有修复任务完成，总耗时{elapsed_time:.2f}秒, 平均{elapsed_time / self.total_tasks:.2f}秒/张")
            # 重置计数器和开始时间
            self.completed_tasks = 0
            self.start_time = None