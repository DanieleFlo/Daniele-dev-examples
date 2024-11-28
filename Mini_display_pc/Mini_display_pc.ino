#include <SPI.h>
#include "Ucglib.h"

Ucglib_ST7735_18x128x160_HWSPI ucg(/*cd=*/9, /*cs=*/10, /*reset=*/8);

#define margin_H 2
#define margin_V 4

void setup(void) {
  delay(1000);
  // ucg.begin(UCG_FONT_MODE_TRANSPARENT);
  ucg.begin(UCG_FONT_MODE_SOLID);
  ucg.clearScreen();
  ucg.setRotate90();
}

void orario(String ora, bool clear) {
  int numChars = ora.length();
  int char_w = 6;
  int x1 = 160 - numChars * char_w - margin_H;
  int y1 = 8 + margin_V;

  ucg.setFont(ucg_font_helvB08_tr);
  ucg.setColor(1, 0, 0, 0);
  ucg.setPrintPos(x1, y1);
  // ucg.setColor(0, 0, 0);
  // ucg.drawBox(x1, margin_V, char_w*numChars, y1);
  if(clear == 0) ucg.setColor(127, 127, 127);
  else ucg.setColor(0, 0, 0);
  ucg.print(ora);
}


void CPU(int temp, int usage) {
  int pos_h = 25;
  ucg.setFont(ucg_font_helvB12_tr);
  ucg.setColor(1, 255, 0, 0);
  ucg.setPrintPos(margin_V, pos_h + margin_V * 2);
  ucg.setColor(255, 255, 255);
  ucg.print(temp);
  ucg.setFont(ucg_font_9x15_tf);
  ucg.print("\260");

  ucg.drawFrame(50, 30, 45, 20);
}

void loop(void) {
  orario("11:55", 0);
  delay(1000);
  orario("11:55", 1);
  orario("5:25", 0);
  delay(1000);
  orario("5:25", 1);
  orario("05:05" , 0);
  delay(1000);
  orario("05:05" , 1);
}
