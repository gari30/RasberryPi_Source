#!/usr/bin/env python3
# codeing: UTF-8

import os
import smbus
import time
import pathlib
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

now_month = datetime.datetime.now().strftime('%Y%m')
Path = './' + now_month + '_Temp_Humidi_Sensor_Data.json'
###ファイルがなかったら作成
if not os.path.exists(Path):
  print("True")
  with open(Path, 'w'):
      pass

i2c = smbus.SMBus(1)
i2c_addr = 0x45

i2c.write_byte_data( i2c_addr, 0x21, 0x30)
time.sleep(0.5)

i2c.write_byte_data( i2c_addr, 0xe0, 0x00 )
data = i2c.read_i2c_block_data( i2c_addr, 0x00, 6 )
temperature = tempChanger(data[0], data[1])
humidity = humidChanger(data[3], data[4])
temperature_str = str('{:.02f}'.format(temperature))
humidity_str = str('{:.02f}'.format(humidity))
with open(Path, 'a') as f:
  print(temperature_str + '℃')
  print(humidity_str + '%')
  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y/%m/%d %H:%M:%S")
  f.write('{"time"' + ': "' + time_str + '",')
  f.write('"temperature"' + ': "' + temperature_str + '",')
  f.write('"humidity"' + ': "' + humidity_str + '"}\n')
  pushDataFirestore(int(time_now.timestamp()), temperature, humidity, 0)
