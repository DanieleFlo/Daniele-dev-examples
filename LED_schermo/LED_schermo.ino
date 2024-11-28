#include <FastLED.h>
#include <stdio.h>
#include <stdlib.h>

// How many leds in your strip?
#define NUM_LEDS 60
#define DATA_PIN 3
#define time_spleep 1000

// Define the array of leds
CRGB leds[NUM_LEDS];

int led = 0;
int r, g, b;

bool status_led = false;
unsigned long time_s = 0;

void led_low() {
  if (status_led == true) {
    for (int i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(0, 0, 0);
    }
    FastLED.show();
    status_led = false;
  }
}

void setup() {
  Serial.begin(115200);
  FastLED.addLeds<WS2813, DATA_PIN, RGB>(leds, NUM_LEDS);
  led_low();
  Serial.setTimeout(10);
}


void loop() {

  while (!Serial.available()) {
    if (millis() - time_s > time_spleep && status_led == true) {
      led_low();
      time_s = millis();
    }
  };
  String line = Serial.readStringUntil('\n');
  if (line.length() > 0) {
    status_led = true;
    time_s = millis();
    int m = 0;
    int n = line.indexOf(";");
    int indice = 0;
    while (n > 0) {
      String token = line.substring(n, m);
      m = n + 1;
      n = line.indexOf(";", n + 1);

      //elaboro il token:
      if (indice % 3 == 0) {
        led++;
        r = token.toInt();
      } else {
        if (indice % 3 == 1) { g = token.toInt(); }
        if (indice % 3 == 2) { b = token.toInt(); }
      }
      leds[led - 1] = CRGB(r, g, b);
      indice++;
    }
    led = 0;
    FastLED.show();
  }
}
