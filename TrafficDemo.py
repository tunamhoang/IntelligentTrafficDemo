# coding=utf-8
import sys
from PyQt5.QtWidgets import QMainWindow,QApplication, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread,pyqtSignal

from IntelligentTrafficUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Struct import *
from NetSDK.SDK_Enum import *
from NetSDK.SDK_Callback import *
import time
from queue import Queue

global wnd
callback_num = 0


class TrafficCallBackAlarmInfo:
    def __init__(self):
        """Khởi tạo các thuộc tính lưu thông tin sự kiện.

        :return: None
        """
        self.time_str = ""
        self.plate_number_str = ""
        self.plate_color_str = ""
        self.object_subType_str = ""
        self.vehicle_color_str = ""
        self.country_str = ""

    def get_alarm_info(self, alarm_info):
        """Phân tích dữ liệu cảnh báo từ SDK.

        :param alarm_info: cấu trúc DEV_EVENT_TRAFFICJUNCTION_INFO
        :return: None
        """
        self.time_str = '{}-{}-{} {}:{}:{}'.format(alarm_info.UTC.dwYear, alarm_info.UTC.dwMonth, alarm_info.UTC.dwDay,
                                                   alarm_info.UTC.dwHour, alarm_info.UTC.dwMinute, alarm_info.UTC.dwSecond)
        self.plate_number_str = str(alarm_info.stTrafficCar.szPlateNumber.decode('gb2312'))
        self.plate_color_str = str(alarm_info.stTrafficCar.szPlateColor, 'utf-8')
        self.object_subType_str = str(alarm_info.stuVehicle.szObjectSubType, 'utf-8')
        self.vehicle_color_str = str(alarm_info.stTrafficCar.szVehicleColor, 'utf-8')
        self.country_str = str(alarm_info.stCommInfo.szCountry, 'utf-8')

class BackUpdateUIThread(QThread):
    # Định nghĩa tín hiệu thông qua thuộc tính lớp
    update_date = pyqtSignal(int, object, int, bool, bool)

    # Xử lý nghiệp vụ
    def run(self):
        """Thread dùng cho việc cập nhật giao diện.

        :return: None
        """
        pass



@CB_FUNCTYPE(None, C_LLONG, C_DWORD, c_void_p, POINTER(c_ubyte), C_DWORD, C_LDWORD, c_int, c_void_p)
def AnalyzerDataCallBack(lAnalyzerHandle, dwAlarmType, pAlarmInfo, pBuffer, dwBufSize, dwUser, nSequence, reserved):
    """Callback nhận dữ liệu sự kiện từ thiết bị.

    :param lAnalyzerHandle: handle đăng ký
    :param dwAlarmType: loại sự kiện
    :param pAlarmInfo: con trỏ thông tin sự kiện
    :param pBuffer: dữ liệu hình ảnh
    :param dwBufSize: kích thước buffer
    :param dwUser: tham số người dùng
    :param nSequence: số thứ tự gói
    :param reserved: dự phòng
    :return: None
    """
    print('Enter AnalyzerDataCallBack')
    # Nếu loại cảnh báo là sự kiện giao thông thì hiển thị thông tin lên giao diện
    if(lAnalyzerHandle == wnd.attachID)and(dwAlarmType == EM_EVENT_IVS_TYPE.TRAFFICJUNCTION):
        global callback_num
        local_path = os.path.abspath('.')
        is_global = False
        is_small = False
        show_info = TrafficCallBackAlarmInfo()
        callback_num += 1
        alarm_info = cast(pAlarmInfo, POINTER(DEV_EVENT_TRAFFICJUNCTION_INFO)).contents
        show_info.get_alarm_info(alarm_info)
        if alarm_info.stuObject.bPicEnble:
            is_global = True
            GlobalScene_buf = cast(pBuffer,POINTER(c_ubyte * alarm_info.stuObject.stPicInfo.dwOffSet)).contents
            if not os.path.isdir(os.path.join(local_path, 'Global')):
                os.mkdir(os.path.join(local_path, 'Global'))
            with open('./Global/Global_Img' + str(callback_num) + '.jpg', 'wb+') as global_pic:
                global_pic.write(bytes(GlobalScene_buf))
            if (alarm_info.stuObject.stPicInfo.dwFileLenth > 0):
                is_small = True
                small_buf = pBuffer[alarm_info.stuObject.stPicInfo.dwOffSet:alarm_info.stuObject.stPicInfo.dwOffSet +
                                                                        alarm_info.stuObject.stPicInfo.dwFileLenth]
                if not os.path.isdir(os.path.join(local_path, 'Small')):
                    os.mkdir(os.path.join(local_path, 'Small'))
                with open('./Small/Small_Img' + str(callback_num) + '.jpg', 'wb+') as small_pic:
                    small_pic.write(bytes(small_buf))
        elif (dwBufSize > 0):
            is_global = True
            GlobalScene_buf = cast(pBuffer, POINTER(c_ubyte * dwBufSize)).contents
            if not os.path.isdir(os.path.join(local_path, 'Global')):
                os.mkdir(os.path.join(local_path, 'Global'))
            with open('./Global/Global_Img' + str(callback_num) + '.jpg', 'wb+') as global_pic:
                global_pic.write(bytes(GlobalScene_buf))
        wnd.backthread.update_date.emit(dwAlarmType, show_info, callback_num, is_global, is_small)
        return

class TrafficWnd(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        """Khởi tạo cửa sổ chính và cấu hình SDK.

        :param parent: QWidget cha nếu có
        :return: None
        """
        super(TrafficWnd, self).__init__(parent)
        self.setupUi(self)
        # Khởi tạo giao diện
        self._init_ui()

        # Các biến và callback của NetSDK
        self.loginID = C_LLONG()
        self.playID = C_LLONG()
        self.freePort = c_int()
        self.attachID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)
        self.m_DecodingCallBack = fDecCBFun(self.DecodingCallBack)
        self.m_RealDataCallBack = fRealDataCallBackEx2(self.RealDataCallBack)

        # Lấy đối tượng NetSDK và khởi tạo
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

        # Tạo luồng
        self.backthread = BackUpdateUIThread()
        # Kết nối tín hiệu
        self.backthread.update_date.connect(self.update_UItable)
        self.thread = QThread()
        self.backthread.moveToThread(self.thread)
        # Bắt đầu luồng
        self.thread.started.connect(self.backthread.run)
        self.thread.start()


    # Hàm khởi tạo giao diện
    def _init_ui(self):
        """Thiết lập trạng thái ban đầu cho giao diện.

        :return: None
        """
        self.row = 0
        self.column = 0
        self.Login_pushButton.setEnabled(True)
        self.Play_pushButton.setEnabled(False)
        self.Logout_pushButton.setEnabled(False)
        self.StopPlay_pushButton.setEnabled(False)
        self.Attach_pushButton.setEnabled(False)
        self.Detach_pushButton.setEnabled(False)

        self.IP_lineEdit.setText('192.168.128.61')
        self.Port_lineEdit.setText('37777')
        self.User_lineEdit.setText('admin')
        self.Pwd_lineEdit.setText('admin123')

        self.setWindowFlag(Qt.WindowMinimizeButtonHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint)
        self.setFixedSize(self.width(), self.height())

        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Logout_pushButton.clicked.connect(self.logout_btn_onclick)
        self.Play_pushButton.clicked.connect(self.play_btn_onclick)
        self.StopPlay_pushButton.clicked.connect(self.stop_play_btn_onclick)
        self.Attach_pushButton.clicked.connect(self.attach_btn_onclick)
        self.Detach_pushButton.clicked.connect(self.detach_btn_onclick)

    def log_open(self):
        """Bật ghi log của SDK ra file.

        :return: None
        """
        log_info = LOG_SET_PRINT_INFO()
        log_info.dwSize = sizeof(LOG_SET_PRINT_INFO)
        log_info.bSetFilePath = 1
        log_info.szLogFilePath = os.path.join(os.getcwd(), 'sdk_log.log').encode('gbk')
        result = self.sdk.LogOpen(log_info)

    # Đăng nhập thiết bị
    def login_btn_onclick(self):
        """Đăng nhập thiết bị bằng thông tin trên giao diện.

        :return: None
        """
        self.Attach_tableWidget.setHorizontalHeaderLabels([
            'Thời gian',
            'Sự kiện',
            'Biển số',
            'Màu biển số',
            'Loại xe',
            'Màu xe'
        ])
        ip = self.IP_lineEdit.text()
        port = int(self.Port_lineEdit.text())
        username = self.User_lineEdit.text()
        password = self.Pwd_lineEdit.text()
        stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        stuInParam.szIP = ip.encode()
        stuInParam.nPort = port
        stuInParam.szUserName = username.encode()
        stuInParam.szPassword = password.encode()
        stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
        stuInParam.pCapParam = None

        stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        self.loginID, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)
        if self.loginID:
            self.setWindowTitle('Giao thông thông minh - Trực tuyến')
            self.Logout_pushButton.setEnabled(True)
            self.Login_pushButton.setEnabled(False)
            self.Play_pushButton.setEnabled(True)
            self.Attach_pushButton.setEnabled(True)
            for i in range(int(device_info.nChanNum)):
                self.Channel_comboBox.addItem(str(i))
        else:
            QMessageBox.about(self, 'Thông báo', error_msg)

    # Đăng xuất thiết bị
    def logout_btn_onclick(self):
        """Đăng xuất thiết bị và giải phóng tài nguyên.

        :return: None
        """
        # Dừng phát video
        if self.playID:
            self.sdk.StopRealPlayEx(self.playID)
            self.playID = 0
            self.Video_label.repaint()
            self.sdk.SetDecCallBack(self.freePort, None)
            self.sdk.Stop(self.freePort)
            self.sdk.CloseStream(self.freePort)
            self.sdk.ReleasePort(self.freePort)
        # Dừng đăng ký
        if self.attachID:
            self.sdk.StopLoadPic(self.attachID)
            self.attachID = 0
        # Thoát
        result = self.sdk.Logout(self.loginID)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Play_pushButton.setEnabled(False)
        self.StopPlay_pushButton.setEnabled(False)
        self.Attach_pushButton.setEnabled(False)
        self.Detach_pushButton.setEnabled(False)
        self.setWindowTitle('Giao thông thông minh - Ngoại tuyến')
        self.loginID = C_LLONG(0)
        self.Channel_comboBox.clear()
        self.Attach_tableWidget.clear()
        self.Attach_tableWidget.setRowCount(0)
        self.Video_label.clear()
        self.GlobalScene_label.clear()
        self.SmallScene_label.clear()
        self.row = 0
        self.column = 0
        self.Attach_tableWidget.setHorizontalHeaderLabels([
            'Thời gian', 'Sự kiện', 'Biển số', 'Màu biển số', 'Loại xe', 'Màu xe', 'Quốc gia'
        ])

    # Bắt đầu xem trực tiếp
    def play_btn_onclick(self):
        """Bắt đầu xem trực tiếp kênh được chọn.

        :return: None
        """
        result, self.freePort = self.sdk.GetFreePort()
        if not result:
            pass
        self.sdk.OpenStream(self.freePort)
        self.sdk.Play(self.freePort, self.Video_label.winId())

        channel = self.Channel_comboBox.currentIndex()
        self.playID = self.sdk.RealPlayEx(self.loginID, channel, 0)
        if self.playID:
            self.Play_pushButton.setEnabled(False)
            self.StopPlay_pushButton.setEnabled(True)
            self.sdk.SetRealDataCallBackEx2(self.playID, self.m_RealDataCallBack, None, EM_REALDATA_FLAG.RAW_DATA)
            self.sdk.SetDecCallBack(self.freePort, self.m_DecodingCallBack)
        else:
            QMessageBox.about(self, 'Thông báo', 'error:' + str(self.sdk.GetLastError()))

    # Dừng phát video
    def stop_play_btn_onclick(self):
        """Dừng xem trực tiếp.

        :return: None
        """
        if self.playID:
            self.sdk.StopRealPlayEx(self.playID)
        self.Play_pushButton.setEnabled(True)
        self.StopPlay_pushButton.setEnabled(False)
        self.playID = 0
        self.Video_label.repaint()
        self.sdk.SetDecCallBack(self.freePort, None)
        self.sdk.Stop(self.freePort)
        self.sdk.CloseStream(self.freePort)
        self.sdk.ReleasePort(self.freePort)

    # Đăng ký sự kiện giao thông
    def attach_btn_onclick(self):
        """Đăng ký nhận sự kiện giao thông.

        :return: None
        """
        self.GlobalScene_label.clear()
        self.SmallScene_label.clear()
        self.Attach_tableWidget.setHorizontalHeaderLabels([
            'Thời gian', 'Sự kiện', 'Biển số', 'Màu biển số', 'Loại xe', 'Màu xe'
        ])
        channel = self.Channel_comboBox.currentIndex()
        bNeedPicFile = 1
        dwUser = 0
        self.attachID = self.sdk.RealLoadPictureEx(self.loginID, channel, EM_EVENT_IVS_TYPE.TRAFFICJUNCTION, bNeedPicFile, AnalyzerDataCallBack, dwUser, None)
        if not self.attachID:
            QMessageBox.about(self, 'Thông báo', 'error:' + str(self.sdk.GetLastError()))
        else:
            self.Attach_pushButton.setEnabled(False)
            self.Detach_pushButton.setEnabled(True)
            QMessageBox.about(self, 'Thông báo', 'Đăng ký thành công')

    # Hủy đăng ký
    def detach_btn_onclick(self):
        """Hủy đăng ký sự kiện giao thông.

        :return: None
        """
        if (self.attachID == 0):
            return
        self.sdk.StopLoadPic(self.attachID)
        self.GlobalScene_label.clear()
        self.SmallScene_label.clear()
        self.attachID = 0
        self.Attach_pushButton.setEnabled(True)
        self.Detach_pushButton.setEnabled(False)
        self.Attach_tableWidget.setHorizontalHeaderLabels([
            'Thời gian', 'Sự kiện', 'Biển số', 'Màu biển số', 'Loại xe', 'Màu xe'
        ])


    def update_UItable(self, dwAlarmType, show_info,detect_object_id, is_global, is_small):
        """Cập nhật bảng sự kiện và hiển thị hình ảnh.

        :param dwAlarmType: loại sự kiện
        :param show_info: thông tin hiển thị
        :param detect_object_id: id ảnh
        :param is_global: có ảnh toàn cảnh hay không
        :param is_small: có ảnh xe hay không
        :return: None
        """
        self.GlobalScene_label.clear()
        self.SmallScene_label.clear()
        if(dwAlarmType == EM_EVENT_IVS_TYPE.TRAFFICJUNCTION):
            if(self.row > 499):
                self.Attach_tableWidget.clear()
                self.Attach_tableWidget.setRowCount(0)
                self.Attach_tableWidget.setHorizontalHeaderLabels(
                    ['Thời gian', 'Sự kiện', 'Biển số', 'Màu biển số', 'Loại xe',
                    'Màu xe'])
                self.row = 0
                # Cập nhật giao diện
                self.Attach_tableWidget.viewport().update()
            self.Attach_tableWidget.setRowCount(self.row + 1)
            item1 = QTableWidgetItem(show_info.time_str)
            self.Attach_tableWidget.setItem(self.row, self.column, item1)
            item2 = QTableWidgetItem('Sự kiện nút giao thông')
            self.Attach_tableWidget.setItem(self.row, self.column + 1, item2)
            item3 = QTableWidgetItem(show_info.plate_number_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 2, item3)
            item4 = QTableWidgetItem(show_info.plate_color_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 3, item4)
            item5 = QTableWidgetItem(show_info.object_subType_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 4, item5)
            item6 = QTableWidgetItem(show_info.vehicle_color_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 5, item6)
            item7 = QTableWidgetItem(show_info.country_str)
            self.Attach_tableWidget.setItem(self.row, self.column + 6, item7)
            if (self.attachID != 0):
                if is_global:
                    image = QPixmap('./Global/Global_Img' + str(detect_object_id) + '.jpg').scaled(self.GlobalScene_label.width(),
                                                                                      self.GlobalScene_label.height())
                    self.GlobalScene_label.setPixmap(image)
                if is_small:
                    image = QPixmap('./Small/Small_Img' + str(detect_object_id) + '.jpg').scaled(self.SmallScene_label.width(),
                                                                                  self.SmallScene_label.height())
                    self.SmallScene_label.setPixmap(image)
            self.row += 1
            self.Attach_tableWidget.viewport().update()


    # Callback khi mất kết nối
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        """Callback khi mất kết nối thiết bị.

        :param lLoginID: handle đăng nhập
        :param pchDVRIP: địa chỉ IP
        :param nDVRPort: cổng
        :param dwUser: tham số người dùng
        :return: None
        """
        self.setWindowTitle('Giao thông thông minh - Ngoại tuyến')

    # Callback khi kết nối lại
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        """Callback khi kết nối lại thành công.

        :param lLoginID: handle đăng nhập
        :param pchDVRIP: địa chỉ IP
        :param nDVRPort: cổng
        :param dwUser: tham số người dùng
        :return: None
        """
        self.setWindowTitle('Giao thông thông minh - Trực tuyến')

    # Callback dữ liệu luồng
    def RealDataCallBack(self, lRealHandle, dwDataType, pBuffer, dwBufSize, param, dwUser):
        """Nhận dữ liệu video thời gian thực từ thiết bị.

        :param lRealHandle: handle xem trực tiếp
        :param dwDataType: loại dữ liệu
        :param pBuffer: buffer dữ liệu
        :param dwBufSize: kích thước buffer
        :param param: tham số mở rộng
        :param dwUser: tham số người dùng
        :return: None
        """
        if lRealHandle == self.playID:
            data_buffer = cast(pBuffer, POINTER(c_ubyte * dwBufSize)).contents
            with open('./data.dav', 'ab+') as data_file:
                data_file.write(data_buffer)
            self.sdk.InputData(self.freePort, pBuffer, dwBufSize)

    # Callback giải mã PLAYSDK
    def DecodingCallBack(self, nPort, pBuf, nSize, pFrameInfo, pUserData, nReserved2):
        """Nhận khung dữ liệu đã giải mã từ PLAYSDK.

        :param nPort: cổng phát
        :param pBuf: buffer dữ liệu YUV
        :param nSize: kích thước dữ liệu
        :param pFrameInfo: thông tin khung
        :param pUserData: dữ liệu người dùng
        :param nReserved2: dự phòng
        :return: None
        """
        # here get YUV data, pBuf is YUV data IYUV/YUV420 ,size is nSize, pFrameInfo is frame info with height, width.
        data = cast(pBuf, POINTER(c_ubyte * nSize)).contents
        info = pFrameInfo.contents
        # info.nType == 3 is YUV data,others ard audio data.
        # you can parse YUV420 data to RGB
        if info.nType == 3:
            pass

    # Dọn dẹp khi đóng cửa sổ chính
    def closeEvent(self, event):
        """Dọn dẹp tài nguyên khi cửa sổ đóng.

        :param event: sự kiện đóng
        :return: None
        """
        event.accept()
        if self.attachID:
            self.sdk.StopLoadPic(self.attachID)
            self.attachID = 0
        if self.playID:
            self.sdk.StopRealPlayEx(self.playID)
            self.playID = 0
        if self.loginID:
            self.sdk.Logout(self.loginID)
            self.loginID = 0
        self.sdk.Cleanup()
        self.Video_label.repaint()
        self.Attach_tableWidget.clear()
        self.Attach_tableWidget.setRowCount(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_wnd = TrafficWnd()
    wnd = my_wnd
    my_wnd.log_open()
    my_wnd.show()
    sys.exit(app.exec_())