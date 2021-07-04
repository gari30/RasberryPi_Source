#!/usr/bin/env python3
# codeing: UTF-8

import os
import sys
import smbus
import serial
import time
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# firestoreにデータを上げる
# param date: 日付データ(数値)
# param temperature: 温度データ(数値)
# param humidity: 湿度データ(数値)
# param co2_concentration: CO2濃度(数値)
def pushDataFirestore(date, temperature, humidity, co2_concentration):
  cred = credentials.Certificate('./kyokko-ob-team_firestore.json')
  firebase_admin.initialize_app(cred)
  db = firestore.client()

  store_document = db.collection('sensor-data_test-env').document(str(date))
  store_document.set({
    'temperature': temperature,
    'humidity': humidity,
    'co2-concentration': co2_concentration,
  })

# 温度データを数値変換
def tempChanger(msb, lsb):
  mlsb = ((msb << 8 ) | lsb)
  return (-45 + 175 * int( str( mlsb ), 10) / (pow( 2, 16 ) - 1 ))

# 湿度データを温度変換
def humidChanger( msb, lsb):
  mlsb = ((msb << 8) | lsb)
  return ( 100 * int( str( mlsb ), 10) / (pow( 2, 16 ) - 1 ))

# CO2センサキャリブレーション
def setCo2Calibration():
  # MH-Z14Bにキャリブレーションコマンドを送信
  co2_serial.write(bytes([0xFF, 0x01, 0x87, 0x00, 0x00, 0x00, 0x00, 0x00, 0x78]))
  print("co2 sensor calibration.")
  co2_serial.reset_input_buffer()
  return

# CO2濃度取得
def getCo2Concentration():
  # MH-Z14Bにコマンド送信、レスポンス受信
  co2_serial.write(bytes([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79]))
  co2_data = co2_serial.read(9)

  if len(co2_data) != 9:
    # 受信バイト数エラー
    co2_serial.reset_input_buffer()
    print("Response length error.")
    return -1

  if co2_data[0] != 0xFF or co2_data[1] != 0x86:
    # 受信データ異常エラー
    co2_serial.reset_input_buffer()
    print("Response Data error.")
    return -1

  co2_checksum = 0xFF - (sum(co2_data[1:7]) & 0xFF) + 1
  if co2_checksum != co2_data[8]:
    # チェックサムエラー
    co2_serial.reset_input_buffer()
    print("checksum error.")
    return -1

  return co2_data[2] * 256 + data[3]

# シリアルデバイスの設定
co2_serial = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=0.1)

if 1 < len(sys.argv):
  arg_data = sys.argv[1]
  if arg_data == 'co2_init':
    # co2濃度センサのキャリブレーション
    setCo2Calibration()
    sys.exit()

now_month = datetime.datetime.now().strftime('%Y%m')
Path = './' + now_month + '_Temp_Humidi_Sensor_Data.json'
# ファイルがなかったら作成
if not os.path.exists(Path):
  print("True")
  with open(Path, 'w'):
      pass

i2c = smbus.SMBus(1)
i2c_addr = 0x45

i2c.write_byte_data( i2c_addr, 0x21, 0x30)
time.sleep(0.5)

# 温湿度データの取得
i2c.write_byte_data( i2c_addr, 0xe0, 0x00 )
data = i2c.read_i2c_block_data( i2c_addr, 0x00, 6 )
temperature = tempChanger(data[0], data[1])
humidity = humidChanger(data[3], data[4])

# CO2濃度データの取得
co2_retry_count = 0
while co2_retry_count < 3:
  co2_conc = getCo2Concentration()
  if co2_conc != -1:
    break
  co2_retry_count += 1

# データの整形
temperature_str = str('{:.02f}'.format(temperature))
humidity_str = str('{:.02f}'.format(humidity))
co2_conc_str = str('{:.02f}'.format(co2_conc))
with open(Path, 'a') as f:
  print(temperature_str + '℃')
  print(humidity_str + '%')
  print(co2_conc_str + 'ppm')
  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y/%m/%d %H:%M:%S")
  f.write('{"time"' + ': "' + time_str + '",')
  f.write('"temperature"' + ': "' + temperature_str + '",')
  f.write('"humidity"' + ': "' + humidity_str + '",')
  f.write('"co2_concentration"' + ': "' + co2_conc_str + '"}\n')
  pushDataFirestore(int(time_now.timestamp()), temperature, humidity, co2_conc)
