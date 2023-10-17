 /*  Battery and Charger tester Service on Arduino with Command Line Interface
        receive 'G' or push button to do test sequence
*/

//#include <Servo.h>

//Servo myservo;  // create servo object to control a servo
// twelve servo objects can be created on most boards

int pos = 0;    // variable to store the servo position
const int LINK_STATUS_LED_11 = 11;
const int TEST_SWITCH1_PIN_10      = 10;
const int TEST_SWITCH2_PIN_4      = 4;
const int HC05_POWER_LOW_ON_8    = 8;
const int RELAY_7                = 7;
const int SWITCH_9               = 9;
const int RELAY_12               =12;

void setLEDon(void) { digitalWrite( LINK_STATUS_LED_11, LOW); }
void setLEDoff(void){ digitalWrite( LINK_STATUS_LED_11, HIGH); }
bool isLEDon(void){ digitalRead( LINK_STATUS_LED_11); }
void blink(void) {
  setLEDon();
  delay(500);
  setLEDoff();
}
void setDrainOn(void)   { digitalWrite(RELAY_12, LOW); digitalWrite(RELAY_7, HIGH);   } // discharge
void setChargeOn(void)   { digitalWrite(RELAY_7, LOW); digitalWrite(RELAY_12, HIGH);  } // charge
void setRelaysOff(void)  { digitalWrite(RELAY_12, LOW); digitalWrite(RELAY_7, LOW); } // idle

void buzzerOff(void)  { digitalWrite( HC05_POWER_LOW_ON_8, HIGH); } // make sure the buzzer starts out off 
void buzzerOn(void)   { digitalWrite( HC05_POWER_LOW_ON_8, LOW);  }

// power on
bool buzzed;
void buzz(){
  buzzerOn();
  delay(200);
  buzzerOff();
  buzzed = true;
}

/////////////////////////////////////////////////////////////////////////////////////
unsigned long nexttick;
void setup() {
  // initialize serial communications at 9600 bps:
  Serial.begin(9600);
      
  //myservo.attach(3);  // attaches the servo on pin 9 to the servo object
  pinMode(LINK_STATUS_LED_11, OUTPUT); 
  digitalWrite( LINK_STATUS_LED_11, HIGH);  
  pinMode( TEST_SWITCH1_PIN_10, INPUT_PULLUP);
  pinMode( TEST_SWITCH2_PIN_4, INPUT_PULLUP);
  digitalWrite( HC05_POWER_LOW_ON_8, HIGH);  // make sure the buzzer starts out off 
  pinMode(HC05_POWER_LOW_ON_8, OUTPUT);  //  pin 8 used to buzzer
  pinMode( SWITCH_9, INPUT_PULLUP);
  setRelaysOff();                       // 7 , 12 off before configuring
  pinMode(RELAY_7, OUTPUT);
  pinMode(RELAY_12, OUTPUT); 
  pinMode(RELAY_12, OUTPUT); 
  pinMode(RELAY_12, OUTPUT); 
  nexttick = millis();
  Serial.println("--------------------");
  setLEDon();
  buzz();
  }   

//int index, battvolt, battaccum, lowvoltlimit;
int currentnow;   //, currentdifVolt, currentdifV, current, curaccumraw, currentprev;
long currentaccumleft,currentaccumright; //,currentfilt;
const long dacscale = 1606;
const int currentrawoffset = 1068;
const long curdacscale = 6239;

int index, battvolt, battaccum, lowvoltlimit, currentdifVolt, currentdifV, current, curaccumraw, currentprev;
// currentvolt, 
char state[9];
//int dacscale = 1651;
//int testlength; // in intervals
void showBATTvolt()
{
  long int accum = 0;
  int max = 0;
  int min = 1024;

  // Batt volts
  analogRead(A1); // throw away first one
  for (int i=0;i<10;i++) {
    delay(5);
    int raw = analogRead(A1);
    accum += raw;
    if (raw>max)
      max = raw;
    if(raw<min)
      min = raw;
  }
  accum -= max;  //ignore largest one
  accum -= min;  //ignore smallest one
  battvolt = (accum*dacscale)/(1024*8);
  battaccum = accum;

  // Batt left current volts
  accum = 0;
  max = 0;
  min = 1024;
  analogRead(A2); // throw away first one
  for (int i=0;i<10;i++) {
    delay(5);
    int raw = analogRead(A2);
    accum += raw;
    if (raw>max)
      max = raw;
    if(raw<min)
      min = raw;
  }
  accum -= max;  //ignore largest one
  accum -= min;  //ignore smallest one
  currentaccumleft = accum; // temp store left accum

  // Batt right current volts
  accum = 0;
  max = 0;
  min = 1024;
  analogRead(A3); // throw away first one
  for (int i=0;i<10;i++) {
    delay(5);
    int raw = analogRead(A3);
    accum += raw;
    if (raw>max)
      max = raw;
    if(raw<min)
      min = raw;
  }
  accum -= max;  //ignore largest one
  accum -= min;  //ignore smallest one
  currentaccumright = accum;
  curaccumraw = (currentaccumleft - currentaccumright) + currentrawoffset;
  curaccumraw = ((curaccumraw*curdacscale)/(1024*8)); //
  //currentfilt = (currentfilt-(currentfilt/8))+curaccumraw;
  currentnow = -curaccumraw; //currentfilt/8;

  int temp = currentnow-currentprev;
  if ( abs(temp)>2 )     // filter out 1 bit changes
    {
    current = currentnow;
    //currentfilt = curaccumraw*8;
    }
  else if ( temp == 2)
    current = currentnow - 1;
  else if ( temp == -2)
    current = currentnow + 1;
  else
    current = currentprev;
  currentprev = current;  


  // curaccumraw = (((abs(accum-battaccum+2))*214)/1024)-2;   // in tenths of an amp
  // if ( abs(currentprev-curaccumraw)>1 )     // filter out 1 bit changes
  //   current = curaccumraw;
  // else
  //   current = currentprev;
  // if (current < 0)
  //   current = 0;
  // currentprev = current;  
  
  state[0] = (index==0)?'I':'R';
  state[1] = (digitalRead(LINK_STATUS_LED_11))?'l':'L';
  state[2] = (digitalRead(TEST_SWITCH1_PIN_10))?'0':'1';
  state[3] = (digitalRead(TEST_SWITCH2_PIN_4))?'0':'2';
  state[4] = (buzzed)?'B':'-';  buzzed = false;
  state[5] = (digitalRead(SWITCH_9))?'-':'M';
  state[6] = (digitalRead(RELAY_7 ))?'D':'-';
  state[7] = (digitalRead(RELAY_12))?'C':'-';
  state[8] = 0;

  Serial.print(state);
  Serial.print(",");
  Serial.print(index);
  Serial.print(",");
  Serial.print(battvolt);
  Serial.print(",");
  Serial.print(current);
  Serial.print(",");
  Serial.print(currentnow);
  Serial.print(",");
  Serial.print(accum);
  Serial.print(",");
  Serial.print(battaccum);
  Serial.println("");
  if (index) index += 1;
  // 
}

void doReset(void) {
  setLEDoff();
  setRelaysOff();
  buzzerOff();
  index = 0;
}
/////////////////////////////////////////////////////////////////////
//#define wait(A) {int i=0; while(i<A){delay(100);i+=100;if ( !digitalRead( SWITCH_9)){Serial.println("");return;}}}

void loop() {
  if(millis() >= nexttick) {
    nexttick = millis() + 1000;  
    showBATTvolt();    
  }  
  if ( !digitalRead( SWITCH_9) ) {
    doReset();
  }
  while( Serial.available())
    switch( toupper(Serial.read()) ) {
      case 'I': doReset();
        break;
      case 'G': index = 1;
        break;
      case 'L': setLEDon();
        break;
      case 'K': setLEDoff();
        break;
      case 'D': setDrainOn();
        break;
      case 'C': setChargeOn();
        break;
      case '-': setRelaysOff();
        break;
      case 'B': buzz();
        break;
      case 'H': buzz();
      case '?': buzz();
        Serial.println("CMDs:Go,Interrupt,L/K LED on/off,Drain,Charge,-Drain&Charge off,Buzz");
        Serial.println("Stat:Idle/Running,L/l led on/off,DIP 1/2,Buzzed,Microswitch,Drain,Charge");
    }
  }
