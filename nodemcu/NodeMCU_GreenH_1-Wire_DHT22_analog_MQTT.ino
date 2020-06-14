// DHT22 device
DHTesp dht;

// WiFi configuration
const char* ssid = "<your SSID>";
const char* password = "<your password>";
int wifitries = 0;
int connstatus;

IPAddress staticIP(192,168,42,80);
IPAddress gateway(192,168,42,1);
IPAddress subnet(255,255,255,0);

// MQTT configuration and buffer
const char* mqtt_server = "192.168.42.57";
const char* mqtt_username = "";
const char* mqtt_password = "";
const char* mqtt_topic = "domoticz/in";
char mqttbuffer[60];

WiFiClient espClient;
PubSubClient client(espClient);

// LED definitions
//const int led = 2; // ESP12 builtin LED
const int led =16; // External LED connected to D0
//const int led_on = LOW; // ESP12 builtin LED
//const int led_off = HIGH; // ESP12 builtin LED
const int led_on = HIGH; // External LED
const int led_off = LOW; // External LED

// Temperature Domoticz idx and constants/variables
const int idx_temp = 10; /* same as virual sensor idx in Domotocz */
float temperature = 0.0;

// Temperature and humidity Domoticz idx and constants/variables
const int idxdht = 11; /* same as virual sensor idx in Domotocz */
float airtemperature = 0.0;
float airhumidity = 0.0;

// Soil humidity Domoticz idx and constants/variables
const int idx_shum = 12; /* same as virual sensor idx in Domotocz */
int inputVal = 0; //Variable to store analog input 
int moisture = 0; // calculated moisture value
// Measured min and max values from soil moisture sensor
const int inputValMin = 282;
const int inputValMax = 562;
// Moisture range expected by Domoticz virtual device, in centibars (cb)
const int moistureRange = 200;

// Handle recieved MQTT message, just print it
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

// Reconnect to MQTT broker
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("NodeMCUClient")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup(void){
  pinMode(led, OUTPUT);
  digitalWrite(led, led_off);
  Serial.begin(115200);

  // Start up the 1-Wire library
  sensors.begin();
  Serial.println("");
  Serial.println("Starting: NodeMCU_GreenH_1-Wire_DHT22_analog_MQTT.ino");
  Serial.println("1-Wire library started");

  // Setup DHT library
  dht.setup(DHT22_BUS, DHTesp::DHT22); // Connect DHT sensor to GPIO 04
  Serial.println("DHT library started");

  // Set WiFi to station mode and disconnect from an AP if it was previously connected
  WiFi.mode(WIFI_STA);
  WiFi.hostname("greenhouse-nodemcu");
  //WiFi.disconnect();
  Serial.println("Connect to network");
  Serial.printf("MAC address: %s\n", WiFi.macAddress().c_str());
  //delay(100);
  WiFi.config(staticIP, gateway, subnet);
  WiFi.begin(ssid, password);
  wifitries = 0;

  // Wait for WiFi connection
  Serial.println("Wait for WiFi connection");
  while ((connstatus = WiFi.status()) != WL_CONNECTED) {
    delay(600);
    digitalWrite(led, led_on);
    delay(400);
    Serial.printf(".");
    //Serial.printf("%d", connstatus);
    wifitries++;
    if (wifitries > 40) {
      Serial.println("");
      wifitries = 0;
    }
    digitalWrite(led, led_off);
  }
  Serial.println("");
  Serial.print("Connected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Setup MQTT
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

}

void loop(void)
{
  // Wait between measurements
  delay(10 * dht.getMinimumSamplingPeriod());

  // Reconnect to MQTT broker if needed
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  // Read and publish temperature
  digitalWrite(led, led_on);
  sensors.requestTemperatures(); // Send the command to get temperatures
  temperature = sensors.getTempCByIndex(0);
  sprintf(mqttbuffer, "{ \"idx\" : %d, \"nvalue\" : 0, \"svalue\" : \"%3.1f\" }", idx_temp, temperature);
  // send temperature to the MQTT topic
  client.publish(mqtt_topic, mqttbuffer);
  // Debug MQTT message
  Serial.println(mqttbuffer);
  delay(200);
  // Read and publish temperature and humitity
  float airhumidity = dht.getHumidity();
  float airtemperature = dht.getTemperature();
  sprintf(mqttbuffer, "{ \"idx\" : %d, \"nvalue\" : 0, \"svalue\" : \"%3.1f;%3.1f;0\" }",
    idxdht, airtemperature, airhumidity);
  // send temperature and humidity to the MQTT topic
  client.publish(mqtt_topic, mqttbuffer);
  // Debug MQTT message
  Serial.println(mqttbuffer);
  delay(200);
  // Read and publish analog input from moisture sensor
  inputVal = analogRead (A0); // Analog Values 0 to 1023
  Serial.print("Analog input: ");
  Serial.println (inputVal);
  if (inputVal < inputValMin)
    inputVal = inputValMin;
  if (inputVal > inputValMax)
    inputVal = inputValMax;
  Serial.print("Adjusted analog input: ");
  Serial.println (inputVal);
  moisture = inputVal - inputValMin;
  moisture = (moisture * moistureRange)/(inputValMax - inputValMin);
  Serial.print("Moisture: ");
  Serial.println (moisture);
  sprintf(mqttbuffer, "{ \"idx\" : %d, \"nvalue\" : %d, \"svalue\" : \"0.0\" }",
  idx_shum, moisture);
  client.publish(mqtt_topic, mqttbuffer);
  // Debug MQTT message
  Serial.println(mqttbuffer);
  digitalWrite(led, led_off);
}
