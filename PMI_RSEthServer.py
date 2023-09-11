#!/usr/bin/env python3


from socket import *
import random
from netifaces import interfaces, ifaddresses, AF_INET
from time import sleep
import time
from datetime import datetime
import PySimpleGUI as sg
import os, sys
from threading import Thread
import select

random.seed()
DEBUG = True

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
    return crc_b.hex().upper()
    

def COMMAND_GEN(length):
    SYMBOLS = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
    COMMAND = ''
    for i in range (length*2):
        n = random.randint(0,len(SYMBOLS)-1)
        COMMAND+=SYMBOLS[n]
    return COMMAND.upper()

SOCKET = None

def recvM():
    global SOCKET
    global recvMode
    global crcRecvCounter
    window.Element("RECV_INDICATOR").update(background_color = "green")
    startTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    file = open(logfile, 'a+', encoding='utf-8')
    if recvTCPMode == "TCP Client":
        file.write(f"{startTime};Старт приема сообщений {recvTCPMode} {recvRemIP}:{recvPort}\n")
        window["RECV_OUTPUT"].print(f"Время начала: {startTime}")
        SOCKET = socket(AF_INET, SOCK_STREAM)
        SOCKET.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000)
        SOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
#        SOCKET.setblocking(0)
        try:
            SOCKET.connect((recvRemIP, int(recvPort)))
            connected = True
            window["RECV_OUTPUT"].print(f"Соединение с {recvRemIP}:{recvPort} установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {recvRemIP}:{recvPort} установлено\n")
        except:
            connected = False
            window["RECV_OUTPUT"].print(f"Соединение с {recvRemIP}:{recvPort} не установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {recvRemIP}:{recvPort} не установлено\n")
        counter = 0
        if connected:
            while recvMode:
                ready = select.select([SOCKET],[],[],1)
                if ready[0]:
                    try:
                        msg = SOCKET.recv(6000).hex().upper()
                    except OSError:
                        break
                    counter += 1
                    length = int(len(msg)/2)
                    csum = msg[-4:]
                    if len(msg) > 4:
                        statCRC = "OK" if crc16x25(msg[:-4]) == csum else "NOTOK"
                    else:
                        statCRC = "NOTOK"
                    if statCRC == "NOTOK":
                        crcRecvCounter += 1
                        window["RECV_ERRORS"].update(crcRecvCounter)
                        window["RECV_ERRORS"].update(background_color = "red")
                    window["RECV_OUTPUT"].print(f"#{counter} от {recvRemIP}:{recvPort} - {length} Байт CRC:{statCRC}")
                    file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Принято сообщение {counter} от {recvRemIP}:{recvPort} длина: {length} байт CRC: {statCRC};{msg}\n")
            stopTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            window["RECV_OUTPUT"].print(f"Время окончания: {stopTime}")
            file.write(f"{stopTime};Окончание приема сообщений {recvTCPMode} {recvRemIP}:{recvPort}\n")
    if recvTCPMode == "TCP Server":
        file.write(f"{startTime};Старт приема сообщений {recvTCPMode} {recvLocalIP}:{recvPort}\n")
        window["RECV_OUTPUT"].print(f"Время начала: {startTime}")
        SOCKET = socket(AF_INET, SOCK_STREAM)
        SOCKET.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000)
        SOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
#        SOCKET.setblocking(0)
        SOCKET.bind((recvLocalIP, int(recvPort)))
        SOCKET.listen(50)
        try:
            CONN, ADDR = SOCKET.accept()
            connected = True
            window["RECV_OUTPUT"].print(f"Соединение с {ADDR[0]}:{ADDR[1]} установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {ADDR[0]}:{ADDR[1]} установлено\n")
        except:
            connected = False
            window["RECV_OUTPUT"].print(f"Соединение не установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение не установлено\n")
        counter = 0
        if connected:
            while recvMode:
                ready = select.select([CONN],[],[],1)
                if ready[0]:
                    try:
                        msg = CONN.recv(6000).hex().upper()
                    except OSError:
                        break
                    counter += 1
                    length = int(len(msg)/2)
                    csum = msg[-4:]
                    if len(msg) > 4:
                        statCRC = "OK" if crc16x25(msg[:-4]) == csum else "NOTOK"
                    else:
                        statCRC = "NOTOK"
                    if statCRC == "NOTOK":
                        crcRecvCounter += 1
                        window["RECV_ERRORS"].update(crcRecvCounter)
                        window["RECV_ERRORS"].update(background_color = "red")
                    window["RECV_OUTPUT"].print(f"#{counter} от {ADDR[0]}:{ADDR[1]} - {length} Байт CRC:{statCRC}")
                    file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Принято сообщение {counter} от {ADDR[0]}:{ADDR[1]} длина: {length} байт CRC: {statCRC};{msg}\n")
            stopTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            window["RECV_OUTPUT"].print(f"Время окончания: {stopTime}")
            file.write(f"{stopTime};Окончание приема сообщений {recvTCPMode} {ADDR[0]}:{ADDR[1]}\n")
    try:
        SOCKET.close()
    except:
        pass
    file.close()
    SOCKET = None
    window.Element("RECV_INDICATOR").update(background_color = "red")
    recvMode = False
    

def sendM():
    global SOCKET
    global sendMode
    window.Element("SEND_INDICATOR").update(background_color = "green")
    startTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    file = open(logfile, 'a+', encoding='utf-8')
    if sendTCPMode == "TCP Client":
        file.write(f"{startTime};Отправка {sendNUM} сообщений по {sendLEN} байт с интервалом {sendINTER} секунд {sendTCPMode} {sendRemIP}:{sendPort}\n")
        SOCKET = socket(AF_INET, SOCK_STREAM)
        SOCKET.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000)
        SOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            SOCKET.connect((sendRemIP, int(sendPort)))
            connected = True
            window["SEND_OUTPUT"].print(f"Соединение с {sendRemIP}:{sendPort} установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {sendRemIP}:{sendPort} установлено\n")
        except:
            connected = False
            window["SEND_OUTPUT"].print(f"Соединение с {sendRemIP}:{sendPort} не установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {sendRemIP}:{sendPort} не установлено\n")
        if connected:
            for i in range(sendNUM):
                if not sendMode: break
                command = COMMAND_GEN(sendLEN-2)
                csum = crc16x25(command)
                command += csum
                SOCKET.sendall(bytes.fromhex(command))
                window["SEND_OUTPUT"].print(f"{i+1} Сообщение к {sendRemIP}:{sendPort} - {sendLEN} Байт")
                file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Отправлено {i+1}-е сообщение к {sendRemIP}:{sendPort} {sendTCPMode};{command}\n")
                sleep(sendINTER)
    if sendTCPMode == "TCP Server":
        file.write(f"{startTime};Отправка {sendNUM} сообщений по {sendLEN} байт с интервалом {sendINTER} секунд {sendTCPMode} {sendLocalIP}:{sendPort}\n")
        SOCKET = socket(AF_INET, SOCK_STREAM)
        SOCKET.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000)
        SOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        SOCKET.bind((sendLocalIP, int(sendPort)))
        SOCKET.listen(50)
        try:
            CONN, ADDR = SOCKET.accept()
            connected = True
            window["SEND_OUTPUT"].print(f"Соединение с {ADDR[0]}:{ADDR[1]} установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {ADDR[0]}:{ADDR[1]} установлено\n")
        except:
            connected = False
            window["SEND_OUTPUT"].print(f"Соединение не установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение не установлено\n")
        if connected:
            for i in range(sendNUM):
                if not sendMode: break
                command = COMMAND_GEN(sendLEN-2)
                csum = crc16x25(command)
                command += csum
                CONN.send(bytes.fromhex(command))
                window["SEND_OUTPUT"].print(f"{i+1} Сообщение к {ADDR[0]}:{ADDR[1]} - {sendLEN} Байт")
                file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Отправлено {i+1}-е сообщение к {ADDR[0]}:{ADDR[1]} {sendTCPMode};{command}\n")
                sleep(sendINTER)
    try:
        SOCKET.close()
    except:
        pass
    file.close()
    SOCKET = None
    window.Element("SEND_INDICATOR").update(background_color = "red")
    sendMode = False
    
    
def srevM():
    global SOCKET
    global srevMode
    global crcRecvCounter
    window.Element("SREV_INDICATOR").update(background_color = "green")
    startTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    file = open(logfile, 'a+', encoding='utf-8')
    if srevTCPMode == "TCP Client":
        file.write(f"{startTime};Старт обмена сообщениями по {srevLENMin}-{srevLENMax} байт с интервалом {srevINTER} секунд {srevTCPMode} {srevRemIP}:{srevPort}\n")
        window["SREV_OUTPUT"].print(f"Время начала: {startTime}")
        SOCKET = socket(AF_INET, SOCK_STREAM)
        SOCKET.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000)
        SOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            SOCKET.connect((srevRemIP, int(srevPort)))
            connected = True
            window["SREV_OUTPUT"].print(f"Соединение с {srevRemIP}:{srevPort} установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {srevRemIP}:{srevPort} установлено\n")
        except:
            connected = False
            window["SREV_OUTPUT"].print(f"Соединение с {srevRemIP}:{srevPort} не установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {srevRemIP}:{srevPort} не установлено\n")
        counterIN = 0
        counterOUT = 0
        timeRecv = time.time()
        begin = True
        if connected:
            while srevMode:
                if (time.time() - timeRecv) >= srevINTER or begin:
                    begin = False
                    length = random.randint(srevLENMin, srevLENMax)
                    command = COMMAND_GEN(length-2)
                    csum = crc16x25(command)
                    command += csum
                    SOCKET.sendall(bytes.fromhex(command))
                    counterOUT += 1
                    window["SREV_OUTPUT"].print(f"OUT #{counterOUT} Сообщение к {srevRemIP}:{srevPort} - {length} Байт")
                    file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Отправлено {counterOUT}-е сообщение к {srevRemIP}:{srevPort} {srevTCPMode};{command}\n")
                    recvOK = False
                    timeRecv = time.time()
                    while not recvOK and srevMode:
                        ready = select.select([SOCKET],[],[],1)
                        if (time.time() - timeRecv) >= 6: 
                            window["SREV_OUTPUT"].print(f"ERROR Ответ от {srevRemIP}:{srevPort} не получен")
                            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Ответ от {srevRemIP}:{srevPort} не получен\n")
                            break
                        if ready[0]:
                            try:
                                msg = SOCKET.recv(6000).hex().upper()
                            except OSError:
                                break
                            recvOK = True
                            counterIN += 1
                            length = int(len(msg)/2)
                            csum = msg[-4:]
                            if len(msg) > 4:
                                statCRC = "OK" if crc16x25(msg[:-4]) == csum else "NOTOK"
                            else:
                                statCRC = "NOTOK"
                            if statCRC == "NOTOK":
                                crcRecvCounter += 1
                                window["SREV_ERRORS"].update(crcRecvCounter)
                                window["SREV_ERRORS"].update(background_color = "red")
                            window["SREV_OUTPUT"].print(f"IN #{counterIN} от {srevRemIP}:{srevPort} - {length} Байт CRC:{statCRC}")
                            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Принято сообщение {counterIN} от {srevRemIP}:{srevPort} длина: {length} байт CRC: {statCRC};{msg}\n")
            stopTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            window["SREV_OUTPUT"].print(f"Время окончания: {stopTime}")
            file.write(f"{stopTime};Окончание обмена сообщениями {srevTCPMode} {srevRemIP}:{srevPort}\n")
            window.Element("SREV_INDICATOR").update(background_color = "red")
    if srevTCPMode == "TCP Server":
        file.write(f"{startTime};Старт обмена сообщениями по {srevLENMin}-{srevLENMax} байт с интервалом {srevINTER} секунд {srevTCPMode} {srevLocalIP}:{srevPort}\n")
        window["SREV_OUTPUT"].print(f"Время начала: {startTime}")
        SOCKET = socket(AF_INET, SOCK_STREAM)
        SOCKET.setsockopt(SOL_SOCKET, SO_RCVBUF, 10000)
        SOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        SOCKET.bind((srevLocalIP, int(srevPort)))
        SOCKET.listen(50)
        try:
            CONN, ADDR = SOCKET.accept()
            connected = True
            window["SREV_OUTPUT"].print(f"Соединение с {ADDR[0]}:{ADDR[1]} установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение с {ADDR[0]}:{ADDR[1]} установлено\n")
        except:
            connected = False
            window["SREV_OUTPUT"].print(f"Соединение не установлено")
            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Соединение не установлено\n")
        counterIN = 0
        counterOUT = 0
        timeRecv = time.time()
        begin = True
        if connected:
            while srevMode:
                if (time.time() - timeRecv) >= srevINTER or begin:
                    begin = False
                    length = random.randint(srevLENMin, srevLENMax)
                    command = COMMAND_GEN(length-2)
                    csum = crc16x25(command)
                    command += csum
                    CONN.send(bytes.fromhex(command))
                    counterOUT += 1
                    window["SREV_OUTPUT"].print(f"OUT #{counterOUT} Сообщение к {ADDR[0]}:{ADDR[1]} - {length} Байт")
                    file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Отправлено {counterOUT}-е сообщение к {ADDR[0]}:{ADDR[1]} {srevTCPMode};{command}\n")
                    recvOK = False
                    timeRecv = time.time()
                    while not recvOK and srevMode:
                        ready = select.select([CONN],[],[],1)
                        if (time.time() - timeRecv) >= 6: 
                            window["SREV_OUTPUT"].print(f"ERROR Ответ от {ADDR[0]}:{ADDR[1]} не получен")
                            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Ответ от {ADDR[0]}:{ADDR[1]} не получен\n")
                            break
                        if ready[0]:
                            try:
                                msg = CONN.recv(6000).hex().upper()
                            except OSError:
                                break
                            recvOK = True
                            counterIN += 1
                            length = int(len(msg)/2)
                            csum = msg[-4:]
                            if len(msg) > 4:
                                statCRC = "OK" if crc16x25(msg[:-4]) == csum else "NOTOK"
                            else:
                                statCRC = "NOTOK"
                            if statCRC == "NOTOK":
                                crcRecvCounter += 1
                                window["SREV_ERRORS"].update(crcRecvCounter)
                                window["SREV_ERRORS"].update(background_color = "red")
                            window["SREV_OUTPUT"].print(f"IN #{counterIN} от {ADDR[0]}:{ADDR[1]} - {length} Байт CRC:{statCRC}")
                            file.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')};Принято сообщение {counterIN} от {ADDR[0]}:{ADDR[1]} длина: {length} байт CRC: {statCRC};{msg}\n")
            stopTime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            window["SREV_OUTPUT"].print(f"Время окончания: {stopTime}")
            file.write(f"{stopTime};Окончание обмена сообщениями {srevTCPMode} {ADDR[0]}:{ADDR[1]}\n")
            window.Element("SREV_INDICATOR").update(background_color = "red")
    try:
        SOCKET.close()
    except:
        pass
    file.close()
    SOCKET = None
    window.Element("SREV_INDICATOR").update(background_color = "red")
    sendMode = False


def getIPAddresses():
    addresses = []
    for ifaceName in interfaces():
        address = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )][0]
        if address != "No IP addr": addresses.append(address)
    return addresses


modeList = ["TCP Client", "TCP Server"]
IPs = getIPAddresses()
logfile = "RSPMIlog_server.csv"

defRemIP = "192.168.222.77"
defPort = "40417"

s_column = (290, 490)
s_text = (17, 1)
s_radio_top = (14, 1)
s_indicator = (13, 1)
s_button = (15, 1)
s_output = (38,8)
backColorMain = "#2A303C"
buttonColor = ("#FFFFFF", "#041B47")

col_recv_mode = [
    [
        sg.Radio("Прием", "TestMode", background_color=backColorMain, size=s_radio_top, key="RECV_MODE"), sg.Text("", size=s_indicator, background_color='red', key="RECV_INDICATOR"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Text("Режим: ", background_color=backColorMain, size=s_text), sg.Combo(values=modeList, default_value=modeList[0], size=s_text, key="RECV_TCP_MODE"),
    ],
    [
        sg.Text("IP конвертора:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text=defRemIP, key="RECV_REMOTE_IP"),
    ],
    [
        sg.Text("TCP порт:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text=defPort, key="RECV_PORT"),
    ],
    [
        sg.Text("IP сервера(local):", background_color=backColorMain, size=s_text), sg.Combo(values=IPs, default_value=IPs[0], size=s_text, key="RECV_LOCAL_IP"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Button("Запустить", button_color=buttonColor, size=s_button, key="RECV_START"), sg.Button("Остановить", button_color=buttonColor, size=s_button, key="RECV_STOP"),
    ],
    [
        sg.Multiline(size=s_output, key="RECV_OUTPUT"),
    ],
    [
        sg.Text("Ошибок: ", background_color=backColorMain, size=s_text), sg.Text("0", background_color=backColorMain, size=(10, 1), key="RECV_ERRORS"),
    ],
    [
        sg.Button("Сбросить", button_color=buttonColor, size=s_button, key="RECV_CLEAR"), 
    ],
]

col_send_mode = [
    [
        sg.Radio("Отправка", "TestMode", background_color=backColorMain, size=s_radio_top, key="SEND_MODE"), sg.Text("", size=s_indicator, background_color='red', key="SEND_INDICATOR"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Text("Размер сообщения:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text='150', key="SEND_SIZE"),
    ],
    [
        sg.Text("Кол-во сообщений:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text='60', key="SEND_NUM"),
    ],
    [
        sg.Text("Интервал отправки:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text='2', key="SEND_INTER"),
    ],
    [
        sg.Text("Режим: ", background_color=backColorMain, size=s_text), sg.Combo(values=modeList, default_value=modeList[0], size=s_text, key="SEND_TCP_MODE"),
    ],
    [
        sg.Text("IP конвертора:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text=defRemIP, key="SEND_REMOTE_IP"),
    ],
    [
        sg.Text("TCP порт:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text=defPort, key="SEND_PORT"),
    ],
    [
        sg.Text("IP сервера(local):", background_color=backColorMain, size=s_text), sg.Combo(values=IPs, default_value=IPs[0], size=s_text, key="SEND_LOCAL_IP"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Button("Запустить", button_color=buttonColor, size=s_button, key="SEND_START"), sg.Button("Остановить", button_color=buttonColor, size=s_button, key="SEND_STOP"),
    ],
    [
        sg.Multiline(size=s_output, key="SEND_OUTPUT"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Button("Сбросить", button_color=buttonColor, size=s_button, key="SEND_CLEAR"), 
    ]
]

col_srev_mode = [
    [
        sg.Radio("Обмен", "TestMode", background_color=backColorMain, size=s_radio_top, key="SREV_MODE"), sg.Text("", size=s_indicator, background_color='red', key="SREV_INDICATOR"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text('',background_color=backColorMain),],
    [sg.Text("Размер запроса:", background_color=backColorMain, size=s_text), sg.Input(size=(5, 1), default_text='15', key="SREV_LEN_MIN"), sg.Text("-",background_color=backColorMain), 
    sg.Input(size=(5, 1), default_text='150', key="SREV_LEN_MAX"),],
    [
        sg.Text("Интервал отправки:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text='2', key="SREV_INTER"),
    ],
    [
        sg.Text("Режим: ", background_color=backColorMain, size=s_text), sg.Combo(values=modeList, default_value=modeList[0], size=s_text, key="SREV_TCP_MODE"),
    ],
    [
        sg.Text("IP конвертора:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text=defRemIP, key="SREV_REMOTE_IP"),
    ],
    [
        sg.Text("TCP порт:", background_color=backColorMain, size=s_text), sg.Input(size=s_text, default_text=defPort, key="SREV_PORT"),
    ],
    [
        sg.Text("IP сервера(local):", background_color=backColorMain, size=s_text), sg.Combo(values=IPs, default_value=IPs[0], size=s_text, key="SREV_LOCAL_IP"),
    ],
    [sg.Text('',background_color=backColorMain),],
    [
        sg.Button("Запустить", button_color=buttonColor, size=s_button, key="SREV_START"), sg.Button("Остановить", button_color=buttonColor, size=s_button, key="SREV_STOP"),
    ],
    [
        sg.Multiline(size=s_output, key="SREV_OUTPUT"),
    ],
    [
        sg.Text("Ошибок: ", background_color=backColorMain, size=s_text), sg.Text("0", background_color=backColorMain, size=(10, 1), key="SREV_ERRORS"),
    ],
    [
        sg.Button("Сбросить", button_color=buttonColor, size=s_button, key="SREV_CLEAR"), 
    ]
]

layout = [
    [ 
        sg.Column(col_recv_mode, element_justification='l', background_color=backColorMain, size=s_column),
        sg.Column(col_send_mode, element_justification='l', background_color=backColorMain, size=s_column),
        sg.Column(col_srev_mode, element_justification='l', background_color=backColorMain, size=s_column),
    ],
]

recvMode = False
sendMode = False
srevMode = False
crcRecvCounter = 0
crcSrevCounter = 0

window = sg.Window('RS Ethernet Test Tool by ZemtsovVA (Server part)', background_color=backColorMain, layout=layout, icon="icon_s.ico", finalize=True)

while True:  # The Event Loop
    event, values = window.read()
    # print(event)
    if event in (None, 'Exit', 'Cancel'):
        recvMode = False
        sendMode = False
        srevMode = False
        sys.exit()
        break
    
    if event == "RECV_START" and values["RECV_MODE"] and not recvMode and not sendMode and not srevMode:
        recvMode = True
        recvRemIP = values["RECV_REMOTE_IP"]
        recvPort = values["RECV_PORT"]
        recvTCPMode = values["RECV_TCP_MODE"]
        recvLocalIP = values["RECV_LOCAL_IP"]
        tr = Thread(target = recvM)
        tr.start()
        
    if event == "RECV_STOP" and recvMode:
        recvMode = False
        try:    
            SOCKET.close()
        except:
            pass
        SOCKET = None
    if event == "RECV_CLEAR":
        crcRecvCounter = 0
        window["RECV_ERRORS"].update(crcRecvCounter)
        window["RECV_ERRORS"].update(background_color = backColorMain)
        window["RECV_OUTPUT"].update("")
        
    if event == "SEND_START" and values["SEND_MODE"] and not sendMode and not recvMode and not srevMode:
        sendMode = True
        sendRemIP = values["SEND_REMOTE_IP"]
        sendPort = values["SEND_PORT"]
        sendTCPMode = values["SEND_TCP_MODE"]
        sendLocalIP = values["SEND_LOCAL_IP"]
        sendLEN = int(values["SEND_SIZE"])
        sendNUM = int(values["SEND_NUM"])
        sendINTER = int(values["SEND_INTER"])
        tr = Thread(target = sendM)
        tr.start()
        
    if event == "SEND_STOP" and sendMode:
        sendMode = False
        try:    
            SOCKET.close()
        except:
            pass
        SOCKET = None
    if event == "SEND_CLEAR":
        window["SEND_OUTPUT"].update("")
        
    if event == "SREV_START" and values["SREV_MODE"] and not srevMode and not sendMode and not recvMode:
        srevMode = True
        srevRemIP = values["SREV_REMOTE_IP"]
        srevPort = values["SREV_PORT"]
        srevTCPMode = values["SREV_TCP_MODE"]
        srevLocalIP = values["SREV_LOCAL_IP"]
        srevLENMin = int(values["SREV_LEN_MIN"])
        srevLENMax = int(values["SREV_LEN_MAX"])
        srevINTER = int(values["SREV_INTER"])
        tr = Thread(target = srevM)
        tr.start()
        
    if event == "SREV_STOP" and srevMode:
        srevMode = False
        try:    
            SOCKET.close()
        except:
            pass
        SOCKET = None
    if event == "SREV_CLEAR":
        crcSrevCounter = 0
        window["SREV_ERRORS"].update(crcSrevCounter)
        window["SREV_ERRORS"].update(background_color = backColorMain)
        window["SREV_OUTPUT"].update("")

