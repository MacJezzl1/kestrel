//+------------------------------------------------------------------+
//|                                                   KestrelEA.mq5  |
//|                                               CapeChain Labs     |
//|                           Kestrel AI Trading Intelligence System  |
//|                                                                  |
//|  THIN ADAPTER — No trading logic lives here.                     |
//|  This EA only: reads market data, calls Kestrel Core via HTTPS,  |
//|  executes the returned signal, and reports results back.          |
//+------------------------------------------------------------------+
#property copyright "CapeChain Labs"
#property link      "https://kestrel.capechainlabs.com"
#property version   "1.00"
#property description "Kestrel Bridge — MT5 Adapter"
#property description "See every market. Miss nothing."

//--- Input parameters
input string   KestrelAPIUrl     = "https://api.kestrel.local:8000";  // Kestrel Core API URL
input string   KestrelAPIToken   = "";                                 // JWT Access Token
input string   AdapterSecret     = "";                                 // Bridge Adapter Secret
input string   Instrument        = "";                                 // Override instrument (blank = chart symbol)
input string   Timeframe         = "";                                 // Override timeframe (blank = chart TF)
input double   MinConfidence     = 0.65;                               // Minimum confidence to execute
input double   LotSize           = 0.01;                               // Default lot size
input int      MaxSpread         = 30;                                 // Max spread in points
input int      Slippage          = 10;                                 // Max slippage in points
input int      PollIntervalSec   = 60;                                 // Signal poll interval (seconds)
input bool     AutoTrade         = false;                              // Enable auto-execution
input int      MagicNumber       = 773571;                             // EA magic number

//--- Global variables
datetime       g_lastPollTime    = 0;
int            g_totalSignals    = 0;
int            g_totalTrades     = 0;
string         g_lastDirection   = "none";
double         g_lastConfidence  = 0.0;
string         g_lastRegime      = "unknown";
string         g_connectionStatus = "disconnected";


//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Validate required inputs
   if(StringLen(KestrelAPIToken) == 0)
   {
      Print("❌ Kestrel: API Token is required. Set it in EA inputs.");
      return INIT_PARAMETERS_INCORRECT;
   }
   
   // Set timer for polling
   EventSetTimer(PollIntervalSec);
   
   Print("🦅 Kestrel Bridge MT5 — Initialized");
   Print("   API: ", KestrelAPIUrl);
   Print("   Symbol: ", GetInstrument());
   Print("   Timeframe: ", GetTimeframe());
   Print("   Min Confidence: ", MinConfidence);
   Print("   Auto-Trade: ", AutoTrade ? "ON" : "OFF");
   
   // Initial connection test
   TestConnection();
   
   return INIT_SUCCEEDED;
}


//+------------------------------------------------------------------+
//| Expert deinitialization function                                    |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("🦅 Kestrel Bridge MT5 — Disconnected (reason: ", reason, ")");
}


//+------------------------------------------------------------------+
//| Timer function — polls Kestrel Core for signals                    |
//+------------------------------------------------------------------+
void OnTimer()
{
   RequestSignal();
}


//+------------------------------------------------------------------+
//| Tick function                                                       |
//+------------------------------------------------------------------+
void OnTick()
{
   // Update the comment display on every tick
   UpdateDisplay();
}


//+------------------------------------------------------------------+
//| Get the trading instrument                                         |
//+------------------------------------------------------------------+
string GetInstrument()
{
   if(StringLen(Instrument) > 0)
      return Instrument;
   return Symbol();
}


//+------------------------------------------------------------------+
//| Get the timeframe string                                           |
//+------------------------------------------------------------------+
string GetTimeframe()
{
   if(StringLen(Timeframe) > 0)
      return Timeframe;
   
   ENUM_TIMEFRAMES tf = Period();
   switch(tf)
   {
      case PERIOD_M1:  return "M1";
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
      case PERIOD_W1:  return "W1";
      case PERIOD_MN1: return "MN";
      default:         return "H1";
   }
}


//+------------------------------------------------------------------+
//| Test connection to Kestrel Core                                    |
//+------------------------------------------------------------------+
void TestConnection()
{
   string url = KestrelAPIUrl + "/api/status";
   string headers = "Authorization: Bearer " + KestrelAPIToken + "\r\n"
                   + "Content-Type: application/json\r\n";
   
   char post_data[];
   char result[];
   string result_headers;
   
   ResetLastError();
   int res = WebRequest("GET", url, headers, NULL, 5000, post_data, 0, result, result_headers);
   
   if(res == 200)
   {
      g_connectionStatus = "online";
      Print("✅ Kestrel Core connection OK");
   }
   else
   {
      g_connectionStatus = "offline";
      Print("❌ Kestrel Core connection failed. Code: ", res, " Error: ", GetLastError());
      Print("   Ensure ", KestrelAPIUrl, " is in Tools → Options → Expert Advisors → Allowed URLs");
   }
}


//+------------------------------------------------------------------+
//| Request a signal from Kestrel Core                                 |
//+------------------------------------------------------------------+
void RequestSignal()
{
   string url = KestrelAPIUrl + "/api/signals/generate";
   string headers = "Authorization: Bearer " + KestrelAPIToken + "\r\n"
                   + "Content-Type: application/json\r\n"
                   + "X-Adapter-Secret: " + AdapterSecret + "\r\n";
   
   // Build JSON payload
   string json = "{\"instrument\":\"" + GetInstrument() + "\","
                + "\"timeframe\":\"" + GetTimeframe() + "\"}";
   
   char post_data[];
   StringToCharArray(json, post_data, 0, StringLen(json));
   
   char result[];
   string result_headers;
   
   ResetLastError();
   int res = WebRequest("POST", url, headers, NULL, 10000, post_data, ArraySize(post_data), result, result_headers);
   
   if(res == 200)
   {
      g_connectionStatus = "online";
      string response = CharArrayToString(result);
      ProcessSignalResponse(response);
      g_totalSignals++;
      g_lastPollTime = TimeCurrent();
   }
   else if(res == 403)
   {
      Print("⚠️ Kestrel: License limit reached or invalid token");
      g_connectionStatus = "license_error";
   }
   else
   {
      Print("❌ Kestrel signal request failed. Code: ", res, " Error: ", GetLastError());
      g_connectionStatus = "error";
   }
}


//+------------------------------------------------------------------+
//| Process the signal response from Kestrel Core                      |
//+------------------------------------------------------------------+
void ProcessSignalResponse(string &json)
{
   // Basic JSON parsing (production would use a proper JSON library)
   // Extract direction
   string direction = ExtractJsonString(json, "direction");
   double confidence = ExtractJsonDouble(json, "confidence");
   string regime = ExtractJsonString(json, "regime");
   double sl = ExtractJsonDouble(json, "stop_loss");
   double tp = ExtractJsonDouble(json, "take_profit");
   
   g_lastDirection = direction;
   g_lastConfidence = confidence;
   g_lastRegime = regime;
   
   Print("🦅 Signal: ", direction, " | Confidence: ", DoubleToString(confidence, 3),
         " | Regime: ", regime);
   
   // Execute trade if auto-trade is enabled and confidence meets threshold
   if(AutoTrade && confidence >= MinConfidence && direction != "hold")
   {
      ExecuteTrade(direction, sl, tp);
   }
}


//+------------------------------------------------------------------+
//| Execute a trade based on the signal                                |
//+------------------------------------------------------------------+
void ExecuteTrade(string direction, double sl, double tp)
{
   // Check spread
   double spread = SymbolInfoInteger(Symbol(), SYMBOL_SPREAD);
   if(spread > MaxSpread)
   {
      Print("⚠️ Spread too high (", spread, " > ", MaxSpread, "). Skipping trade.");
      return;
   }
   
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = Symbol();
   request.volume    = LotSize;
   request.deviation = Slippage;
   request.magic     = MagicNumber;
   request.comment   = "Kestrel AI Signal";
   
   if(direction == "buy")
   {
      request.type  = ORDER_TYPE_BUY;
      request.price = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
      if(sl > 0) request.sl = sl;
      if(tp > 0) request.tp = tp;
   }
   else if(direction == "sell")
   {
      request.type  = ORDER_TYPE_SELL;
      request.price = SymbolInfoDouble(Symbol(), SYMBOL_BID);
      if(sl > 0) request.sl = sl;
      if(tp > 0) request.tp = tp;
   }
   else
   {
      return;
   }
   
   if(OrderSend(request, result))
   {
      g_totalTrades++;
      Print("✅ Trade executed: ", direction, " ", LotSize, " lots @ ",
            DoubleToString(request.price, 5));
      
      // Report execution back to Kestrel Core
      ReportExecution(direction, request.price, sl, tp);
   }
   else
   {
      Print("❌ Trade execution failed. Error: ", GetLastError(),
            " Retcode: ", result.retcode);
   }
}


//+------------------------------------------------------------------+
//| Report trade execution back to Kestrel Core (audit trail)          |
//+------------------------------------------------------------------+
void ReportExecution(string direction, double price, double sl, double tp)
{
   string url = KestrelAPIUrl + "/api/trades";
   string headers = "Authorization: Bearer " + KestrelAPIToken + "\r\n"
                   + "Content-Type: application/json\r\n";
   
   string json = "{\"instrument\":\"" + GetInstrument() + "\","
                + "\"direction\":\"" + direction + "\","
                + "\"entry_price\":" + DoubleToString(price, 5) + ","
                + "\"lot_size\":" + DoubleToString(LotSize, 2) + ","
                + "\"confidence_at_entry\":" + DoubleToString(g_lastConfidence, 3) + "}";
   
   char post_data[];
   StringToCharArray(json, post_data, 0, StringLen(json));
   
   char result[];
   string result_headers;
   
   int res = WebRequest("POST", url, headers, NULL, 5000, post_data, ArraySize(post_data), result, result_headers);
   
   if(res == 201)
      Print("✅ Trade reported to Kestrel Core");
   else
      Print("⚠️ Failed to report trade to Core. Code: ", res);
}


//+------------------------------------------------------------------+
//| Update the on-chart display                                        |
//+------------------------------------------------------------------+
void UpdateDisplay()
{
   string display = "";
   display += "╔══════════════════════════════════╗\n";
   display += "║     🦅 KESTREL AI BRIDGE         ║\n";
   display += "║     CapeChain Labs               ║\n";
   display += "╠══════════════════════════════════╣\n";
   display += "║ Status:     " + PadRight(g_connectionStatus, 20) + "║\n";
   display += "║ Symbol:     " + PadRight(GetInstrument(), 20) + "║\n";
   display += "║ Timeframe:  " + PadRight(GetTimeframe(), 20) + "║\n";
   display += "║ Auto-Trade: " + PadRight(AutoTrade ? "ENABLED" : "DISABLED", 20) + "║\n";
   display += "╠══════════════════════════════════╣\n";
   display += "║ Last Signal: " + PadRight(StringToUpper(g_lastDirection), 19) + "║\n";
   display += "║ Confidence:  " + PadRight(DoubleToString(g_lastConfidence * 100, 1) + "%", 19) + "║\n";
   display += "║ Regime:      " + PadRight(g_lastRegime, 19) + "║\n";
   display += "╠══════════════════════════════════╣\n";
   display += "║ Signals:     " + PadRight(IntegerToString(g_totalSignals), 19) + "║\n";
   display += "║ Trades:      " + PadRight(IntegerToString(g_totalTrades), 19) + "║\n";
   display += "╚══════════════════════════════════╝\n";
   
   Comment(display);
}


//+------------------------------------------------------------------+
//| Utility: Pad string to the right                                   |
//+------------------------------------------------------------------+
string PadRight(string text, int width)
{
   while(StringLen(text) < width)
      text += " ";
   return text;
}


//+------------------------------------------------------------------+
//| Utility: Extract a string value from JSON                          |
//+------------------------------------------------------------------+
string ExtractJsonString(string &json, string key)
{
   string search = "\"" + key + "\":\"";
   int start = StringFind(json, search);
   if(start < 0) return "";
   
   start += StringLen(search);
   int end = StringFind(json, "\"", start);
   if(end < 0) return "";
   
   return StringSubstr(json, start, end - start);
}


//+------------------------------------------------------------------+
//| Utility: Extract a double value from JSON                          |
//+------------------------------------------------------------------+
double ExtractJsonDouble(string &json, string key)
{
   string search = "\"" + key + "\":";
   int start = StringFind(json, search);
   if(start < 0) return 0.0;
   
   start += StringLen(search);
   
   // Find end of number (comma, brace, or bracket)
   string num = "";
   for(int i = start; i < StringLen(json); i++)
   {
      ushort ch = StringGetCharacter(json, i);
      if(ch == ',' || ch == '}' || ch == ']' || ch == ' ')
         break;
      num += ShortToString(ch);
   }
   
   if(num == "null") return 0.0;
   return StringToDouble(num);
}
//+------------------------------------------------------------------+
