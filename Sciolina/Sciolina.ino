#include <PID_v1.h>
#define RS A0
#define LED D0

int tiBlink = 0;
bool ledS = false;
#define Rmax 200000 /* Resistenza massima oltre il quale da errore (se il filo si stacca) */
#define R100grad 9000 /* Resistenza a cui deve arrivare per essere a 100°C */

#define PIN_OUTPUT1 D5
#define PIN_OUTPUT2 D6
#define PIN_OUTPUT3 D7

//Define Variables we'll be connecting to
double Setpoint, Input, Output;

//Specify the links and initial tuning parameters
double Kp = 2, Ki = 5, Kd = 1;
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);


/*  */
void blink(int deltaTime) {
  int tfBlink = millis();
  if (tfBlink - tiBlink >= deltaTime) {
    if (ledS == true) digitalWrite(D0, HIGH);
    else digitalWrite(D0, LOW);
    tiBlink = millis();
    ledS = !ledS;
  }
}

float readAnalogRS(int N) {
  float val = 0;
  for (int i = 0; i < N; i++) {
    val += analogRead(RS);
    delay(2);
  }
  return val / N;
}

float readRS() {
  float V1 = 3.3;
  float R1 = 29000;
  float Cv = 0.15;

  float V0 = (readAnalogRS(5) / 1023 * V1) - Cv;
  float R2 = (R1 * V0) / (V1 - V0);
  Serial.print("V= ");
  Serial.println(V0);
  Serial.print("R= ");
  Serial.print(R2 / 1000);
  Serial.println("Kohm");
  return R2;
}

void setup() {
  pinMode(LED, OUTPUT);
  Serial.begin(115200);
  Serial.println("Hello!");
  digitalWrite(LED, LOW);

  //initialize the variables we're linked to
  Input = readRS();
  Setpoint = R100grad;

  //turn the PID on
  myPID.SetMode(AUTOMATIC);
}

void loop() {
  delay(20);

  Input = readRS();
  if (Input < Rmax) {
    myPID.Compute();
    int PWM = map(int(255 - Output), 0, 255, 0, 1023);

    Serial.print("PWM output: ");
    Serial.println(PWM);

    analogWrite(PIN_OUTPUT1, PWM);
    analogWrite(PIN_OUTPUT2, PWM);
    analogWrite(PIN_OUTPUT3, PWM);
    analogWrite(LED, map(Output, 0, 255, 0, 1023));
  } else {
    blink(1000);
    analogWrite(PIN_OUTPUT1, 0);
    analogWrite(PIN_OUTPUT2, 0);
    analogWrite(PIN_OUTPUT3, 0);
    Serial.println("Errore");
  }
}