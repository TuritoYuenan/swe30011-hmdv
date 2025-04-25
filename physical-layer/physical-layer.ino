// Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

#define ACT_BZR 5
#define ACT_LED 6
#define ACT_FAN 12

#define SEN_TMP 7
#define SEN_MQ2 A0
#define SEN_MQ4 A1
#define SEN_MQ7 A2

#include <OneWire.h>
#include <TimerOne.h>

OneWire sensor(SEN_TMP);

struct {
  float lpg;
  float ch4;
  float co;
  float temp;
} readings;

void setup() {
  Serial.begin(9600);

  pinMode(ACT_LED, OUTPUT);
  pinMode(ACT_BZR, OUTPUT);
  pinMode(ACT_FAN, OUTPUT);

  pinMode(SEN_MQ2, INPUT);
  pinMode(SEN_MQ4, INPUT);
  pinMode(SEN_MQ7, INPUT);
  pinMode(SEN_TMP, INPUT);

  // disable buzzer
  digitalWrite(ACT_BZR, HIGH);

  Timer1.initialize(2000000);
  Timer1.attachInterrupt(routine);
}

void loop() {
  delay(100);
}

void routine() {
  readSensors();
  sendReadings();
}

void readSensors() {
  // Gas sensor readings
  readings.lpg = analogRead(SEN_MQ2);
  readings.ch4 = analogRead(SEN_MQ4);
  readings.co = analogRead(SEN_MQ7);

  // Temperature sensor readings
  readings.temp = readTemperature();
}

void sendReadings() {
  Serial.print("LPG:");
  Serial.print(readings.lpg);
  Serial.print(",CH4:");
  Serial.print(readings.ch4);
  Serial.print(",CO:");
  Serial.print(readings.co);
  Serial.print(",Temperature:");
  Serial.println(readings.temp);
}

void engageResponseSystem() {
  digitalWrite(ACT_BZR, LOW);
  digitalWrite(ACT_LED, HIGH);
  digitalWrite(ACT_FAN, HIGH);
}

float readTemperature() {
  byte data[12];
  byte addr[8];

  if (!sensor.search(addr)) {
    sensor.reset_search();
    return -1000;
  }

  if (OneWire::crc8(addr, 7) != addr[7]) {
    Serial.println("CRC is not valid!");
    return -1000;
  }

  if (addr[0] != 0x10 && addr[0] != 0x28) {
    Serial.print("Device is not recognized");
    return -1000;
  }

  sensor.reset();
  sensor.select(addr);
  sensor.write(0x44, 1);

  byte present = sensor.reset();
  sensor.select(addr);
  sensor.write(0xBE);

  for (int i = 0; i < 9; i++) { data[i] = sensor.read(); }
  sensor.reset_search();

  byte MSB = data[1];
  byte LSB = data[0];

  float tempRead = ((MSB << 8) | LSB);
  float TemperatureSum = tempRead / 16;
  return TemperatureSum;
}
