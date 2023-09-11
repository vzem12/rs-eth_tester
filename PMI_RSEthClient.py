import PySimpleGUI as sg
import os, sys
import serial
import serial.tools.list_ports
import random
from threading import Thread
from time import sleep
from datetime import datetime

CRC16_X25_TABLE = [
        0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
        0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
        0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
        0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
        0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
        0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
        0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
        0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
        0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
        0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
        0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
        0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
        0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
        0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
        0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
        0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
        0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
        0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
        0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
        0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
        0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
        0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
        0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
        0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
        0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
        0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
        0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
        0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
        0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
        0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
        0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
        0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78,
        ]    
    
parity = {
    "NONE": "N",
    "EVEN": "E",
    "ODD": "O",
    "MARK": "M",
    "SPACE": "S",
}
brList = [2400,9600,19200,115200]
parList = ["NONE", "EVEN", "ODD", "MARK", "SPACE"]
dataBitList = [8,7,6,5]
stopBitList = [1,1.5,2]

logfile = "RSPMIlog_client.csv"

coms = []
comlist = serial.tools.list_ports.comports()
for com in comlist:
    coms.append(com.device)
    
random.seed()
DEBUG = True

def crc16x25(data, crc=0xFFFF):
    data = bytes.fromhex(data)
    for byte in data:
        crc = (crc >> 8) ^ CRC16_X25_TABLE[(crc ^ byte) & 0x00ff]
        crc = crc ^ 0xffff
        crc_s = hex(crc)[2:]
        if len(crc_s) < 4:
            crc_s = "0" + crc_s
        crc_s = crc_s[-2:]+crc_s[:2]
        crc_b = bytes.fromhex(crc_s)
    return crc_b.hex()
    
    
def COMMAND_GEN(length):
    SYMBOLS = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
    COMMAND = ''
    for i in range (length*2):
        n = random.randint(0,len(SYMBOLS)-1)
        COMMAND+=SYMBOLS[n]
    return COMMAND
    

s_column = (290, 450)
s_text = (15, 1)
s_radio_top = (14, 1)
s_indicator = (13, 1)
backColorMain = "#2A303C"
buttonColor = ("#FFFFFF", "#041B47")

col_send_mode = [
    [
        sg.Radio("Отправка", "TestMode", background_color=backColorMain, size=s_radio_top, key="SEND_MODE"), sg.Text("", size=s_indicator, background_color='red', key="SEND_INDICATOR"),
    ],
    [
        sg.Text("Размер сообщения:", background_color=backColorMain, size=s_text), sg.Input(size=(5, 1), default_text='150', key="SEND_LEN"),
    ],
    [
        sg.Text("Кол-во сообщений:", background_color=backColorMain, size=s_text), sg.Input(size=(5, 1), default_text='60', key="SEND_NUM"),
    ],
    [
        sg.Text("Интервал отправки:", background_color=backColorMain, size=s_text), sg.Input(size=(5, 1), default_text='2', key="SEND_INTER"),
    ],
    [
        sg.Text("Скорость: ", background_color=backColorMain, size=s_text), sg.Combo(values=brList, default_value=brList[0], size=s_text, key="SEND_BR"),
    ],
    [
        sg.Text("Четность:", background_color=backColorMain, size=s_text), sg.Combo(values=parList, default_value=parList[0], size=s_text, key="SEND_PAR"),
    ],
    [
        sg.Text("Бит данных:", background_color=backColorMain, size=s_text), sg.Combo(values=dataBitList, default_value=dataBitList[0], size=s_text, key="SEND_DATABIT"),
    ],
    [
        sg.Text("Стоп Бит:", background_color=backColorMain, size=s_text), sg.Combo(values=stopBitList, default_value=stopBitList[0], size=s_text, key="SEND_STOPBIT"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Button("Отправить", button_color=buttonColor, size=s_text, key="SEND_SEND"), sg.Button("Остановить", button_color=buttonColor, size=s_text, key="SEND_STOP"),
    ],
    [
        sg.Multiline(size=(35,7), key="SEND_OUTPUT"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Button("Сбросить", button_color=buttonColor, size=s_text, key="SEND_CLEAR"), 
    ],
]

col_recv_mode = [
    [
        sg.Radio("Прием", "TestMode", background_color=backColorMain, size=s_radio_top, key="RECV_MODE"), sg.Text("", size=s_indicator, background_color='red', key="RECV_INDICATOR"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Text("Скорость: ", background_color=backColorMain, size=s_text), sg.Combo(values=brList, default_value=brList[0], size=s_text, key="RECV_BR"),
    ],
    [
        sg.Text("Четность:", background_color=backColorMain, size=s_text), sg.Combo(values=parList, default_value=parList[0], size=s_text, key="RECV_PAR"),
    ],
    [
        sg.Text("Бит данных:", background_color=backColorMain, size=s_text), sg.Combo(values=dataBitList, default_value=dataBitList[0], size=s_text, key="RECV_DATABIT"),
    ],
    [
        sg.Text("Стоп Бит:", background_color=backColorMain, size=s_text), sg.Combo(values=stopBitList, default_value=stopBitList[0], size=s_text, key="RECV_STOPBIT"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Button("Запустить", button_color=buttonColor, size=s_text, key="RECV_START"), sg.Button("Остановить", button_color=buttonColor, size=s_text, key="RECV_STOP"),
    ],
    [
        sg.Multiline(size=(35,7), key="RECV_OUTPUT"),
    ],
    [
        sg.Text("Ошибок: ", background_color=backColorMain, size=s_text), sg.Text("0", background_color=backColorMain, size=(10, 1), key="RECV_ERRORS"),
    ],
    [
        sg.Button("Сбросить", button_color=buttonColor, size=s_text, key="RECV_CLEAR"), 
    ]
]

col_srev_mode = [
    [
        sg.Radio("Обмен", "TestMode", background_color=backColorMain, size=s_radio_top, key="SREV_MODE"), sg.Text("", size=s_indicator, background_color='red', key="SREV_INDICATOR"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text("Размер ответа:", background_color=backColorMain, size=s_text), sg.Input(size=(5, 1), default_text='15', key="SREV_LEN_MIN"), sg.Text("-",background_color=backColorMain), 
    sg.Input(size=(5, 1), default_text='150', key="SREV_LEN_MAX"),],
    [
        sg.Text("Скорость: ", background_color=backColorMain, size=s_text), sg.Combo(values=brList, default_value=brList[0], size=s_text, key="SREV_BR"),
    ],
    [
        sg.Text("Четность:", background_color=backColorMain, size=s_text), sg.Combo(values=parList, default_value=parList[0], size=s_text, key="SREV_PAR"),
    ],
    [
        sg.Text("Бит данных:", background_color=backColorMain, size=s_text), sg.Combo(values=dataBitList, default_value=dataBitList[0], size=s_text, key="SREV_DATABIT"),
    ],
    [
        sg.Text("Стоп Бит:", background_color=backColorMain, size=s_text), sg.Combo(values=stopBitList, default_value=stopBitList[0], size=s_text, key="SREV_STOPBIT"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Button("Запустить", button_color=buttonColor, size=s_text, key="SREV_START"), sg.Button("Остановить", button_color=buttonColor, size=s_text, key="SREV_STOP"),
    ],
    [
        sg.Multiline(size=(35,7), key="SREV_OUTPUT"),
    ],
    [
        sg.Text("Ошибок: ", background_color=backColorMain, size=s_text), sg.Text("0", background_color=backColorMain, size=(10, 1), key="SREV_ERRORS"),
    ],
    [
        sg.Button("Сбросить", button_color=buttonColor, size=s_text, key="SREV_CLEAR"), 
    ]
]

layout = [
    [
        sg.Text("COM порт: ", background_color=backColorMain, size=(10, 1)),
        sg.Combo(values=coms, default_value=coms[0] if len(coms)!=0 else '', size=(10, 1), key="COMSET"),
        sg.Button("ОБНОВИТЬ", button_color=buttonColor, size=(10, 1), key="REFRESH_COM"),
    ],
    [
        sg.Text('_'*200, background_color=backColorMain, size=(110, 1))
    ],
    [
        sg.Column(col_send_mode, element_justification='l', background_color=backColorMain, size=s_column), 
        sg.Column(col_recv_mode, element_justification='l', background_color=backColorMain, size=s_column),
        sg.Column(col_srev_mode, element_justification='l', background_color=backColorMain, size=s_column),
    ],
]
sendMode = False
recvMode = False
srevMode = False
crcRecvCounter = 0
crcSrevCounter = 0

def send():
    global window
    global sendMode
    global port
    startTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    file = open(logfile, 'a+', encoding='utf-8')
    file.write(f"{startTime};Отправка {sendNUM} сообщений по {sendLEN} байт с интервалом {sendINTER}\n")
    port = serial.Serial(COM, sendBR, bytesize=sendDB, parity=sendPAR, stopbits=sendSB, timeout=1)
    port.set_buffer_size(rx_size = 4000, tx_size = 4000)
    for i in range(sendNUM):
        if not sendMode: break
        command = COMMAND_GEN(sendLEN-2)
        crc = crc16x25(command)
        command = command+crc
        command = bytes.fromhex(command)
        if DEBUG: print(command)
        port.write(command)
        window["SEND_OUTPUT"].print(f"{i+1} Сообщение {sendBR},{sendDB}{sendPAR}{sendSB} - {sendLEN} Байт")
        file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Отправлено {i+1} сообщение {sendBR},{sendDB}{sendPAR}{sendSB};{command}\n")
        sleep(sendINTER)
    try:
        port.close()
    except:
        pass
    port = None
    sendMode = False
    file.close()
    window.Element("SEND_INDICATOR").update(background_color = "red")
    
    
def recv():
    global window
    global recvMode
    global port
    global crcRecvCounter
    counter = 0
    startTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    file = open(logfile, 'a+', encoding='utf-8')
    file.write(f"{startTime};Старт приема сообщений {recvBR},{recvDB}{recvPAR}{recvSB}\n")
    window["RECV_OUTPUT"].print(f"Время начала: {startTime}")
    port = serial.Serial(COM, recvBR, bytesize=recvDB, parity=recvPAR, stopbits=recvSB, timeout=3)
    port.set_buffer_size(rx_size = 4000, tx_size = 4000)
    while recvMode:
        if (port.inWaiting() > 0):
            msg = b""
            while port.inWaiting() > 0 and recvMode:
                msg += port.read(port.inWaiting())
                sleep(0.11)
            counter += 1
            recvLEN = len(msg)
            if recvLEN > 4:
                statCRC = "OK" if msg.hex()[-4:] == crc16x25(msg.hex()[:-4]) else "NOTOK"
            else:
                statCRC = "NOTOK"
            if statCRC == "NOTOK":
                crcRecvCounter += 1
                window["RECV_ERRORS"].update(crcRecvCounter)
                window["RECV_ERRORS"].update(background_color = "red")
            window["RECV_OUTPUT"].print(f"#{counter} {recvBR},{recvDB}{recvPAR}{recvSB} - {recvLEN} Байт CRC:{statCRC}")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Принято сообщение {counter} длина: {recvLEN} байт CRC: {statCRC};{msg.hex()}\n")
    stopTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    window["RECV_OUTPUT"].print(f"Время окончания: {stopTime}")
    file.write(f"{stopTime};Окончание приема сообщений {recvBR},{recvDB}{recvPAR}{recvSB}\n")
    try:
        port.close()
    except:
        pass
    file.close()
    port = None


def srev():
    global window
    global srevMode
    global port
    global crcSrevCounter
    counterIN = 0
    counterOUT = 0
    startTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    file = open(logfile, 'a+', encoding='utf-8')
    file.write(f"{startTime};Старт обмена сообщениями {srevBR},{srevDB}{srevPAR}{srevSB}\n")
    window["SREV_OUTPUT"].print(f"Время начала: {startTime}")
    port = serial.Serial(COM, srevBR, bytesize=srevDB, parity=srevPAR, stopbits=srevSB, timeout=3)
    port.set_buffer_size(rx_size = 4000, tx_size = 4000)
    while srevMode:
        if (port.inWaiting() > 0):
            msg = b""
            while port.inWaiting() > 0 and srevMode:
                msg += port.read(port.inWaiting())
                sleep(0.11)
            counterIN += 1
            srevLEN = len(msg)
            if srevLEN > 4:
                statCRC = "OK" if msg.hex()[-4:] == crc16x25(msg.hex()[:-4]) else "NOTOK"
            else:
                statCRC = "NOTOK"
            if statCRC == "NOTOK":
                crcSrevCounter += 1
                window["SREV_ERRORS"].update(crcSrevCounter)
                window["SREV_ERRORS"].update(background_color = "red")
            window["SREV_OUTPUT"].print(f"IN #{counterIN} {srevBR},{srevDB}{srevPAR}{srevSB} - {srevLEN} Байт CRC:{statCRC}")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Принято сообщение {counterIN} длина: {srevLEN} байт CRC: {statCRC};{msg.hex()}\n")
            if statCRC == "OK":
                counterOUT += 1
                length = random.randint(srevLenMin,srevLenMax)
                command = COMMAND_GEN(length-2)
                csum = crc16x25(command)
                command += csum
                port.write(bytes.fromhex(command))
                window["SREV_OUTPUT"].print(f"OUT #{counterOUT} {srevBR},{srevDB}{srevPAR}{srevSB} - {length} Байт")
                file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Отправлено сообщение {counterOUT} длина: {length} байт;{command}\n")
    stopTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    window["SREV_OUTPUT"].print(f"Время окончания: {stopTime}")
    file.write(f"{stopTime};Окончание обмена сообщениями {srevBR},{srevDB}{srevPAR}{srevSB}\n")
    try:
        port.close()
    except:
        pass
    file.close()
    port = None
    
    
port = None
window = sg.Window('RS Ethernet Test Tool by ZemtsovVA (Client part)', background_color=backColorMain, layout=layout, icon="icon_c.ico")


while True:  # The Event Loop
    event, values = window.read()
    # print(event)
    if event in (None, 'Exit', 'Cancel'):
        sendMode = False
        recvMode = False
        srevMode = False
        try:
            tr.join()
        except:
            pass
        break
    COM = values["COMSET"]
    if event == "SEND_SEND" and values["SEND_MODE"] and not sendMode and not recvMode and not srevMode:
        sendMode = True
        sendBR = values["SEND_BR"]
        sendPAR = parity[values["SEND_PAR"]]
        sendDB = values["SEND_DATABIT"]
        sendSB = values["SEND_STOPBIT"]
        sendLEN = int(values["SEND_LEN"])
        sendNUM = int(values["SEND_NUM"])
        sendINTER = float(values["SEND_INTER"])
        tr = Thread(target=send)
        window.Element("SEND_INDICATOR").update(background_color = "green")
        tr.start()
    if event == "SEND_STOP" and sendMode:
        sendMode = False
        sleep(0.5)
        try:
            port.close()
        except:
            pass
        port = None
        window.Element("SEND_INDICATOR").update(background_color = "red")
    if event == "SEND_CLEAR":
        window["SEND_OUTPUT"].update("")
        
    if event == "RECV_START" and values["RECV_MODE"] and not recvMode and not srevMode and not sendMode:
        recvMode = True
        recvBR = values["RECV_BR"]
        recvPAR = parity[values["RECV_PAR"]]
        recvDB = values["RECV_DATABIT"]
        recvSB = values["RECV_STOPBIT"]
        window.Element("RECV_INDICATOR").update(background_color = "green")
        tr = Thread(target=recv)
        tr.start()
    if event == "RECV_STOP" and recvMode:
        recvMode = False
        sleep(0.5)
        try:
            port.close()
        except:
            pass
        port = None
        window.Element("RECV_INDICATOR").update(background_color = "red")
    if event == "RECV_CLEAR":
        window["RECV_OUTPUT"].update("")
        crcRecvCounter = 0
        window["RECV_ERRORS"].update(crcRecvCounter)
        window["RECV_ERRORS"].update(background_color = backColorMain)
        
    if event == "SREV_START" and values["SREV_MODE"] and not srevMode and not recvMode and not sendMode:
        srevMode = True
        srevBR = values["SREV_BR"]
        srevPAR = parity[values["SREV_PAR"]]
        srevDB = values["SREV_DATABIT"]
        srevSB = values["SREV_STOPBIT"]
        srevLenMin = int(values["SREV_LEN_MIN"])
        srevLenMax = int(values["SREV_LEN_MAX"])
        window.Element("SREV_INDICATOR").update(background_color = "green")
        tr = Thread(target=srev)
        tr.start()
    if event == "SREV_STOP" and srevMode:
        srevMode = False
        sleep(0.5)
        try:
            port.close()
        except:
            pass
        port = None
        window.Element("SREV_INDICATOR").update(background_color = "red")
    if event == "SREV_CLEAR":
        window["SREV_OUTPUT"].update("")
        crcSrevCounter = 0
        window["SREV_ERRORS"].update(crcSrevCounter)
        window["SREV_ERRORS"].update(background_color = backColorMain)
        
    if event == "REFRESH_COM":
        coms = []
        comlist = serial.tools.list_ports.comports()
        for com in comlist:
            coms.append(com.device)
        window.Element("COMSET").update(values=coms)
            
