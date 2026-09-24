//+------------------------------------------------------------------+
//|                                                   KestrelEA.mq5  |
//|                                               CapeChain Labs     |
//|           Kestrel Autonomous Smart Trading Engine v5.00           |
//|                                                                  |
//|  MULTI-DIMENSIONAL INTELLIGENCE PLATFORM:                        |
//|  - 8 Weighted Technical Indicators (EMA/RSI/MACD/BB/Stoch/ADX/   |
//|    Volume/H4 Trend) with Confluence Scoring                      |
//|  - Multi-Timeframe Confluence (M5/M15/H1/H4/D1)                 |
//|  - Model Consensus Breakdown (Trend/Momentum/Vol/Volume/Struct)  |
//|  - Liquidity/Stop-Cluster Heatmap on Chart                       |
//|  - News-Proximity Flag with Confidence Adjustment                |
//|  - Historical Pattern Matching (Pearson Correlation)             |
//|  - Risk-Adjusted Position Sizing (% of Balance)                  |
//|  - Volatility Forecast (ATR Slope + BB Width Projection)         |
//|  - Post-Signal Outcome Tracker (Predicted vs Actual)             |
//|  - Star-Rated Buy/Sell Markers with Bias Panel                   |
//|  - Fully Autonomous Auto-Execution                               |
//|  - ATR-Based Adaptive SL/TP with 3-Level Partial Take-Profit    |
//|  - Multi-Client PAMM Copy-Receiver                               |
//|  - Crash & Boom Spike Hunter with Directional Bias              |
//|  - Continuous Supabase Cloud PostgreSQL Sync                     |
//+------------------------------------------------------------------+
#property copyright "CapeChain Labs"
#property link      "https://kestrel.capechainlabs.com"
#property version   "5.10"
#property description "Kestrel Autonomous Smart Trading Engine v5.1 — Deep Candlestick & Multi-Dimensional Intelligence"
#property description "See every market. Miss nothing."

//--- Display & Analytical Enums
enum ENUM_HUD_MODE
{
   HUD_MODE_EXPANDED  = 0,   // Pro Full Intelligence Dashboard
   HUD_MODE_MINIMIZED = 1    // Executive Client Presentation Mode
};

enum ENUM_LIQ_STYLE
{
   LIQ_STYLE_CLEAN_LEVELS = 0, // Clean Institutional Key Lines & Price Badges (Recommended)
   LIQ_STYLE_SUBTLE_ZONES = 1, // Subtle Modern Outlines (No Solid Background Fill)
   LIQ_STYLE_OFF          = 2  // Off (Pure Price Action)
};

//--- Input parameters
input group "=== Kestrel Core & Cloud ==="
input string   KestrelAPIUrl     = "https://backend-macjezzl1s-projects.vercel.app";  // Kestrel Core API URL (Live Production)
input string   KestrelAPIToken   = "kestrel-enterprise-owner-vip";     // JWT License Token (Enterprise VIP)
input string   AdapterSecret     = "mt5-adapter-secret-change-me";     // Bridge Adapter Secret
input string   SupabaseUrl       = "https://fuzhwfvixsiyjwokigkp.supabase.co"; // Supabase Project URL
input string   SupabaseApiKey    = "sb_publishable_ud50Y_R0JCHKAg8Uo3KxqA_-InEzdlt"; // Supabase API Key

input group "=== Multi-Client PAMM Copy Trading ==="
input string   ClientAccountID   = "41230754";                         // This Terminal's Account ID
input bool     EnableCopyReceiver = true;                              // Enable Master-to-Client Web Broadcast Receiver
input double   ClientRiskMultiplier = 1.0;                             // Account Custom Risk Multiplier (0.5x - 2.0x)

input group "=== Autonomous Execution ==="
input bool     AutoTrade         = true;                               // Auto-Pilot Mode (True = Auto, False = Manual)
input double   MinConfidence     = 0.65;                               // Minimum Confluence Confidence (0.0-1.0)
input double   LotSize           = 0.20;                               // Base/Max Lot Size (Manual Override Cap)
input int      MaxSpreadPoints   = 120;                                // Max Spread in Points
input int      SlippagePoints    = 30;                                 // Max Slippage in Points
input int      PollIntervalSec   = 8;                                  // Analysis Poll Interval (Seconds)
input int      MagicNumber       = 773571;                             // EA Magic Number
input bool     EnableSpikeHunter = true;                               // Crash/Boom Directional Bias Filter

input group "=== Risk Management & SL/TP ==="
input double   RiskPercentPerTrade = 1.0;                              // Risk % Per Trade (0=use fixed LotSize)
input double   SL_ATR_Mult       = 1.5;                               // Stop Loss = ATR × This Multiplier
input double   TP1_ATR_Mult      = 2.0;                               // Take Profit Level 1 (close 40%)
input double   TP2_ATR_Mult      = 3.5;                               // Take Profit Level 2 (close 30%)
input double   TP3_ATR_Mult      = 5.0;                               // Take Profit Level 3 (trail remainder)
input int      ReEntryCooldownBars = 2;                                // Min Bars After Close Before Re-Entry
input bool     UseTrailingStop   = true;                               // Enable 3-Level Trailing Stop & Breakeven

input group "=== Candlestick & Price Action Engine ==="
input bool     EnableCandleAnalysis   = true;                          // Deep Candlestick Pattern Recognition
input bool     ShowCandleBadges       = true;                          // Draw Subtle Pattern Badges on Chart Candles
input int      MaxCandleBadges        = 5;                             // Maximum Badges on Chart (Keep Clean)
input bool     EnableFVGDetection     = true;                          // Smart Money Fair Value Gap (FVG) Detection

input group "=== Intelligence Modules ==="
input bool     EnableMTFPanel       = true;                            // Multi-Timeframe Confluence Panel
input bool     EnableNewsFilter     = true;                            // News-Proximity Confidence Filter
input bool     EnableLiquidityMap   = true;                            // On-Chart Liquidity/Stop Heatmap
input bool     EnablePatternMatch   = true;                            // Historical Pattern Matching
input bool     EnableVolForecast    = true;                            // Volatility Forecast
input bool     EnableOutcomeTracker = true;                            // Post-Signal Outcome Tracker
input int      PatternLookbackBars  = 500;                             // Pattern Match Lookback Depth (Bars)

input group "=== Client Presentation & Display ==="
input ENUM_HUD_MODE  HudMode          = HUD_MODE_EXPANDED;             // Initial HUD View (Expanded vs Minimized)
input ENUM_LIQ_STYLE LiquidityStyle   = LIQ_STYLE_CLEAN_LEVELS;        // Liquidity Style (Clean Key Levels vs Zones)
input bool     Apply3DCyberTheme    = true;                            // Apply Obsidian & Neon Candle Theme
input bool     DrawSignalArrows     = true;                            // Draw Signal Arrows on Chart
input bool     ShowAdvancedHUD      = true;                            // Render Analysis HUD Panel
input bool     EnableInteractiveButtons = true;                        // Enable On-Chart Trade Buttons

//--- Persistent Indicator Handles (created once in OnInit, reused every analysis cycle)
int g_hEma9, g_hEma21, g_hEma50, g_hEma200;
int g_hRsi14;
int g_hMacd;
int g_hBB20;
int g_hStoch;
int g_hAdx14;
int g_hAtr14;
int g_hH4Ema50;  // H4 timeframe EMA for higher-timeframe trend bias

//--- Multi-Timeframe Indicator Handles [0]=M5, [1]=M15, [2]=H1, [3]=H4, [4]=D1
int g_hMTF_Ema9[5], g_hMTF_Ema21[5];
int g_hMTF_Rsi14[5];
int g_hMTF_Macd[5];
ENUM_TIMEFRAMES g_mtfPeriods[5];

// ================================================================
// DATA STRUCTURES
// ================================================================

//--- Analysis Result Structure
struct ConfluenceAnalysis
{
   string   direction;        // "BUY", "SELL", "HOLD"
   double   score;            // -1.0 to +1.0 weighted confluence score
   double   confidence;       // 0.0 to 1.0 (absolute value of normalized score)
   double   atrValue;         // Current ATR for SL/TP calculation
   double   suggestedSL;      // ATR-based stop loss price
   double   suggestedTP1;     // Take profit level 1
   double   suggestedTP2;     // Take profit level 2
   double   suggestedTP3;     // Take profit level 3
   string   reasoning;        // Human-readable explanation
   // Individual indicator votes (-1, 0, +1)
   int      emaVote;
   int      rsiVote;
   int      macdVote;
   int      bbVote;
   int      stochVote;
   int      adxVote;
   int      volumeVote;
   int      h4TrendVote;
   int      candleVote;       // Candlestick Pattern Vote (-1, 0, +1)
   // Key indicator values for HUD display
   double   rsiValue;
   double   adxValue;
   double   macdMain;
   double   macdSignal;
   double   stochMain;
   double   bbUpper;
   double   bbLower;
   double   ema9Val;
   double   ema21Val;
   double   ema50Val;
   double   ema200Val;
   int      indicatorsAvailable;
   bool     isValid;
   datetime analysisTime;
};

//--- Candlestick Pattern Information
struct CandlePatternInfo
{
   string   patternName;      // e.g., "Bullish Engulfing", "Pin Bar / Hammer", "Morning Star", etc.
   string   direction;        // "BULLISH", "BEARISH", "NEUTRAL"
   double   confidence;       // 0.0 to 1.0
   string   category;         // "REVERSAL", "CONTINUATION", "COMPRESSION"
   int      barIndex;         // Bar index where pattern formed (1 for last closed candle)
   datetime barTime;
   double   patternPrice;
   string   description;
   int      vote;             // +1, -1, 0
};

//--- Candle Anatomy & Pressure Metrics
struct CandleAnatomy
{
   double   bodyPct;             // Body size as % of high-low range
   double   upperWickPct;        // Upper wick as % of high-low range
   double   lowerWickPct;        // Lower wick as % of high-low range
   double   buyingPressurePct;   // Estimated buying force %
   double   sellingPressurePct;  // Estimated selling force %
   bool     isExpansionBar;      // Range >= 1.4x ATR
   bool     isCompressionBar;    // Range <= 0.6x ATR (inside bar / squeeze)
   double   atrRatio;            // Current candle range / 20-bar avg
   int      secondsRemaining;    // Seconds until current candle closes
   string   timeRemainingText;   // Formatted "MM:SS"
   int      consecutiveDir;      // +1 for consecutive bull bars, -1 for bear bars
   int      consecutiveCount;    // Count of consecutive directional bars
};

//--- Fair Value Gap (FVG)
struct FairValueGap
{
   bool     active;
   string   direction;           // "BULLISH", "BEARISH"
   double   topPrice;
   double   bottomPrice;
   int      barIndex;
   datetime barTime;
   bool     mitigated;
};

//--- Multi-Timeframe Analysis
struct MTFSlot
{
   ENUM_TIMEFRAMES tf;
   string   label;          // "M5", "M15", etc.
   string   direction;      // "BUY", "SELL", "NEUTRAL"
   double   confidence;
   int      emaVote;
   double   rsiValue;
   int      macdVote;
   bool     isValid;
};

struct MTFAnalysis
{
   MTFSlot  slots[5];
   int      agreementCount;   // how many agree with primary signal
   int      bullishCount;
   int      bearishCount;
   int      neutralCount;
   string   consensus;        // "STRONGLY ALIGNED", "MOSTLY ALIGNED", "MIXED", "CONFLICTING"
};

//--- Model Consensus Breakdown
struct ConsensusCategory
{
   string   name;
   int      totalModels;
   int      buyVotes;
   int      sellVotes;
   int      neutralVotes;
   double   agreementPct;
   string   verdict;          // "BUY", "SELL", "MIXED"
};

struct ModelConsensus
{
   ConsensusCategory categories[5]; // Trend, Momentum, Volatility, Volume, Structure
   int      totalModels;
   int      totalAgreeing;
   double   overallConsensusPct;
};

//--- Liquidity Zone
struct LiquidityZone
{
   double   priceLevel;
   double   zoneTop;
   double   zoneBtm;
   int      strength;         // 1-5 (touches/factors)
   string   zoneType;         // "ROUND", "SWING_HI", "SWING_LO", "STOP_CLUSTER"
   color    zoneColor;
};

//--- News Event
struct NewsEvent
{
   datetime eventTime;
   string   currency;
   string   impact;           // "HIGH", "MEDIUM", "LOW"
   string   title;
   int      minutesUntil;
};

//--- Pattern Match
struct PatternMatch
{
   int      totalMatches;
   double   continuationPct;
   double   reversalPct;
   double   avgMatchCorrelation;
   string   summary;
};

//--- Volatility Forecast
struct VolatilityForecast
{
   string   forecast;         // "EXPANDING", "CONTRACTING", "STABLE"
   string   icon;             // arrow icon
   double   currentATR;
   double   projectedATR;
   double   atrChangePct;
   double   atrSlope;
   double   bbWidthCurrent;
   double   bbWidthAvg;
};

//--- Post-Signal Outcome Tracker
struct SignalOutcome
{
   bool     active;
   datetime signalTime;
   string   direction;
   double   entryPrice;
   double   confidenceAtEntry;
   double   predictedTP;
   double   predictedSL;
   double   currentPnLPips;
   double   maxFavorablePips;
   double   maxAdversePips;
   string   outcomeStatus;    // "TRACKING", "HIT_TP", "HIT_SL", "EXPIRED"
   int      barsElapsed;
};

// ================================================================
// GLOBAL ENGINE VARIABLES
// ================================================================
ConfluenceAnalysis g_lastAnalysis;
MTFAnalysis        g_mtfData;
ModelConsensus     g_modelConsensus;
PatternMatch       g_patternResult;
VolatilityForecast g_volForecast;

datetime       g_lastPollTime    = 0;
int            g_totalSignals    = 0;
int            g_totalTrades     = 0;
int            g_winTrades       = 0;
string         g_lastDirection   = "HOLD";
double         g_lastConfidence  = 0.0;
string         g_lastRegime      = "Analyzing...";
string         g_connectionStatus = "online";
int            g_buyIndicators   = 0;
int            g_sellIndicators  = 0;
int            g_neutralIndicators = 0;
double         g_consensusPct    = 0.0;
string         g_recoveryLevel   = "OPTIMAL";
double         g_recoveryMult    = 1.0;
double         g_todayProfit     = 0.0;
double         g_totalProfit     = 0.0;
double         g_openProfit      = 0.0;
double         g_currentDrawdown = 0.0;
int            g_animFrame       = 0;
string         g_hudPrefix       = "KST_3D_";
bool           g_autoPilotActive = true;
string         g_lastTradeMsg    = "INITIALIZING INTELLIGENCE ENGINE...";
datetime       g_lastExecutedCommandTime = 0;

//--- Position Tracking for 3-Level Trailing
ulong          g_activePositionTicket = 0;
bool           g_partialTP1Fired = false;
bool           g_partialTP2Fired = false;

//--- News proximity
bool           g_newsProximityActive = false;
double         g_newsConfidencePenalty = 0.0;
string         g_newsWarningText = "";
datetime       g_lastNewsFetchTime = 0;
NewsEvent      g_upcomingNews[10];
int            g_upcomingNewsCount = 0;

//--- Liquidity zones
LiquidityZone  g_liquidityZones[30];
int            g_liquidityZoneCount = 0;

//--- Signal outcome tracker (ring buffer)
SignalOutcome  g_signalHistory[50];
int            g_signalHistoryCount = 0;
int            g_signalHistoryHead  = 0;

//--- Risk lot suggestion
double         g_suggestedLot = 0.0;
string         g_suggestedLotText = "";

//--- Session
string         g_currentSession = "---";

//--- Candlestick & Price Action State
CandlePatternInfo g_activePattern;
CandleAnatomy     g_candleAnatomy;
FairValueGap      g_activeFVG;
ENUM_HUD_MODE     g_hudMode = HUD_MODE_EXPANDED;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("🦅 ========================================================");
   Print("🦅 CAPECHAIN LABS — Kestrel Intelligence Engine v5.00");
   Print("🦅 Multi-Dimensional Confluence Analysis Active");
   Print("🦅 Symbol: ", Symbol(), " | TF: ", GetTimeframe(), " | Account: ", ClientAccountID);
   Print("🦅 ========================================================");

   g_autoPilotActive = AutoTrade;
   g_hudMode = HudMode;

   // 1. Remove manual MT5 top bar and prepare chart
   ChartSetInteger(0, CHART_SHOW_ONE_CLICK, false);
   ChartSetInteger(0, CHART_SHOW_TRADE_LEVELS, true);

   // 2. Apply chart theme
   if(Apply3DCyberTheme)
      Apply3DNeonTheme();

   // 3. Create persistent indicator handles (reused every analysis cycle)
   g_hEma9   = iMA(Symbol(), Period(), 9, 0, MODE_EMA, PRICE_CLOSE);
   g_hEma21  = iMA(Symbol(), Period(), 21, 0, MODE_EMA, PRICE_CLOSE);
   g_hEma50  = iMA(Symbol(), Period(), 50, 0, MODE_EMA, PRICE_CLOSE);
   g_hEma200 = iMA(Symbol(), Period(), 200, 0, MODE_EMA, PRICE_CLOSE);
   g_hRsi14  = iRSI(Symbol(), Period(), 14, PRICE_CLOSE);
   g_hMacd   = iMACD(Symbol(), Period(), 12, 26, 9, PRICE_CLOSE);
   g_hBB20   = iBands(Symbol(), Period(), 20, 0, 2.0, PRICE_CLOSE);
   g_hStoch  = iStochastic(Symbol(), Period(), 14, 3, 3, MODE_SMA, STO_LOWHIGH);
   g_hAdx14  = iADX(Symbol(), Period(), 14);
   g_hAtr14  = iATR(Symbol(), Period(), 14);
   g_hH4Ema50 = iMA(Symbol(), PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);

   // Verify handles
   if(g_hEma9 == INVALID_HANDLE || g_hRsi14 == INVALID_HANDLE || g_hAtr14 == INVALID_HANDLE)
   {
      Print("⚠️ [INIT WARNING]: Some indicator handles failed. Analysis will adapt.");
   }

   // 4. Create Multi-Timeframe indicator handles
   g_mtfPeriods[0] = PERIOD_M5;
   g_mtfPeriods[1] = PERIOD_M15;
   g_mtfPeriods[2] = PERIOD_H1;
   g_mtfPeriods[3] = PERIOD_H4;
   g_mtfPeriods[4] = PERIOD_D1;

   if(EnableMTFPanel)
   {
      for(int i = 0; i < 5; i++)
      {
         g_hMTF_Ema9[i]  = iMA(Symbol(), g_mtfPeriods[i], 9, 0, MODE_EMA, PRICE_CLOSE);
         g_hMTF_Ema21[i] = iMA(Symbol(), g_mtfPeriods[i], 21, 0, MODE_EMA, PRICE_CLOSE);
         g_hMTF_Rsi14[i] = iRSI(Symbol(), g_mtfPeriods[i], 14, PRICE_CLOSE);
         g_hMTF_Macd[i]  = iMACD(Symbol(), g_mtfPeriods[i], 12, 26, 9, PRICE_CLOSE);
      }
      Print("🧠 [MTF]: Multi-timeframe handles created for M5/M15/H1/H4/D1");
   }

   // 5. Set timer for 1-second pulse
   EventSetTimer(1);

   // 6. Initial metrics and sync
   CalculateAccountMetrics();
   SyncAccountToSupabase();
   TestConnection();

   // 7. Run first analysis
   ZeroMemory(g_lastAnalysis);
   g_lastAnalysis.direction = "HOLD";
   g_lastAnalysis.reasoning = "Waiting for first analysis cycle...";

   // 8. Initialize signal history
   for(int i = 0; i < 50; i++)
      g_signalHistory[i].active = false;

   // 9. Draw HUD
   if(ShowAdvancedHUD)
      Render3DHUD();

   Print("🧠 [ENGINE]: Intelligence engine ready. ",
         "Min confidence: ", DoubleToString(MinConfidence * 100, 0), "% | ",
         "Risk/Trade: ", DoubleToString(RiskPercentPerTrade, 1), "% | ",
         "SL: ", DoubleToString(SL_ATR_Mult, 1), "×ATR | ",
         "Modules: MTF=", EnableMTFPanel, " News=", EnableNewsFilter,
         " Liq=", EnableLiquidityMap, " Pattern=", EnablePatternMatch,
         " VolFcast=", EnableVolForecast, " Tracker=", EnableOutcomeTracker);

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                    |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   CleanHUD();
   CleanLiquidityObjects();
   CleanCandleBadges();
   Comment("");

   // Release primary indicator handles
   if(g_hEma9 != INVALID_HANDLE)   IndicatorRelease(g_hEma9);
   if(g_hEma21 != INVALID_HANDLE)  IndicatorRelease(g_hEma21);
   if(g_hEma50 != INVALID_HANDLE)  IndicatorRelease(g_hEma50);
   if(g_hEma200 != INVALID_HANDLE) IndicatorRelease(g_hEma200);
   if(g_hRsi14 != INVALID_HANDLE)  IndicatorRelease(g_hRsi14);
   if(g_hMacd != INVALID_HANDLE)   IndicatorRelease(g_hMacd);
   if(g_hBB20 != INVALID_HANDLE)   IndicatorRelease(g_hBB20);
   if(g_hStoch != INVALID_HANDLE)  IndicatorRelease(g_hStoch);
   if(g_hAdx14 != INVALID_HANDLE)  IndicatorRelease(g_hAdx14);
   if(g_hAtr14 != INVALID_HANDLE)  IndicatorRelease(g_hAtr14);
   if(g_hH4Ema50 != INVALID_HANDLE) IndicatorRelease(g_hH4Ema50);

   // Release MTF handles
   for(int i = 0; i < 5; i++)
   {
      if(g_hMTF_Ema9[i] != INVALID_HANDLE)  IndicatorRelease(g_hMTF_Ema9[i]);
      if(g_hMTF_Ema21[i] != INVALID_HANDLE) IndicatorRelease(g_hMTF_Ema21[i]);
      if(g_hMTF_Rsi14[i] != INVALID_HANDLE) IndicatorRelease(g_hMTF_Rsi14[i]);
      if(g_hMTF_Macd[i] != INVALID_HANDLE)  IndicatorRelease(g_hMTF_Macd[i]);
   }

   Print("🦅 Kestrel Intelligence Engine — Deinitialized (reason: ", reason, ")");
}

//+------------------------------------------------------------------+
//| Chart Event Handler — Interactive 1-Click HUD Buttons             |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id == CHARTEVENT_OBJECT_CLICK)
   {
      if(sparam == g_hudPrefix + "BTN_TOGGLE_HUD")
      {
         g_hudMode = (g_hudMode == HUD_MODE_EXPANDED) ? HUD_MODE_MINIMIZED : HUD_MODE_EXPANDED;
         CleanHUD();
         Render3DHUD();
      }
      else if(sparam == g_hudPrefix + "BTN_TOGGLE_AUTO")
      {
         g_autoPilotActive = !g_autoPilotActive;
         Print("⚡ [KESTREL]: Auto-Pilot toggled: ", g_autoPilotActive ? "ACTIVE" : "PAUSED");
         Render3DHUD();
      }
      else if(sparam == g_hudPrefix + "BTN_BUY_NOW")
      {
         Print("🟢 [1-CLICK BUY]: Manual BUY on ", Symbol());
         ExecuteAutonomousTrade("BUY", LotSize);
         Render3DHUD();
      }
      else if(sparam == g_hudPrefix + "BTN_SELL_NOW")
      {
         Print("🔴 [1-CLICK SELL]: Manual SELL on ", Symbol());
         ExecuteAutonomousTrade("SELL", LotSize);
         Render3DHUD();
      }
      else if(sparam == g_hudPrefix + "BTN_CLOSE_ALL")
      {
         Print("🛡️ [CLOSE ALL]: Closing all active positions on ", Symbol());
         CloseAllSymbolPositions();
         Render3DHUD();
      }
   }
}

//+------------------------------------------------------------------+
//| Timer function — Main Analysis & Execution Loop                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   g_animFrame = (g_animFrame + 1) % 100;

   // === MAIN ANALYSIS & TRADING LOOP ===
   if(TimeCurrent() - g_lastPollTime >= PollIntervalSec)
   {
      // 0. Update session
      g_currentSession = GetCurrentSession();

      // 1. Run LOCAL technical analysis (the primary brain)
      g_lastAnalysis = AnalyzeMarketConfluence();

      // 2. Update display globals from real analysis
      g_lastDirection = g_lastAnalysis.direction;
      g_lastConfidence = g_lastAnalysis.confidence;

      // Count votes for display
      g_buyIndicators = 0;
      g_sellIndicators = 0;
      g_neutralIndicators = 0;
      int votes[8];
      votes[0] = g_lastAnalysis.emaVote;
      votes[1] = g_lastAnalysis.rsiVote;
      votes[2] = g_lastAnalysis.macdVote;
      votes[3] = g_lastAnalysis.bbVote;
      votes[4] = g_lastAnalysis.stochVote;
      votes[5] = g_lastAnalysis.adxVote;
      votes[6] = g_lastAnalysis.volumeVote;
      votes[7] = g_lastAnalysis.h4TrendVote;
      for(int v = 0; v < 8; v++)
      {
         if(votes[v] > 0) g_buyIndicators++;
         else if(votes[v] < 0) g_sellIndicators++;
         else g_neutralIndicators++;
      }
      g_consensusPct = g_lastAnalysis.confidence * 100.0;

      // 3. Run intelligence modules
      if(EnableMTFPanel)
         g_mtfData = AnalyzeMultiTimeframe();

      ComputeModelConsensus(g_lastAnalysis);

      if(EnableNewsFilter)
         CheckNewsProximity();

      if(EnablePatternMatch)
         g_patternResult = FindHistoricalPatterns();

      if(EnableVolForecast)
         g_volForecast = ProjectVolatility();

      if(EnableLiquidityMap)
      {
         ComputeLiquidityZones();
         DrawLiquidityHeatmap();
      }

      // 4. Calculate risk-based lot suggestion
      if(RiskPercentPerTrade > 0 && g_lastAnalysis.direction != "HOLD")
         g_suggestedLot = CalculateRiskLot(g_lastAnalysis.direction);
      else
         g_suggestedLot = LotSize;

      // 5. Apply news confidence penalty if active
      if(g_newsProximityActive && g_lastAnalysis.isValid)
      {
         g_lastAnalysis.confidence *= (1.0 - g_newsConfidencePenalty);
         g_lastConfidence = g_lastAnalysis.confidence;
         g_consensusPct = g_lastAnalysis.confidence * 100.0;
      }

      // 6. AUTO-TRADE if conditions are met
      if(g_autoPilotActive && g_lastAnalysis.isValid
         && g_lastAnalysis.confidence >= MinConfidence
         && (g_lastAnalysis.direction == "BUY" || g_lastAnalysis.direction == "SELL")
         && CanReEnter())
      {
         double tradeLot = (RiskPercentPerTrade > 0) ? g_suggestedLot : LotSize;
         Print("🤖 [AUTO-TRADE]: Confluence met — executing ", g_lastAnalysis.direction,
               " (", DoubleToString(g_lastAnalysis.confidence * 100, 1), "% confidence)",
               " | Lot: ", DoubleToString(tradeLot, 2));
         ExecuteAutonomousTrade(g_lastAnalysis.direction, tradeLot);
      }

      // 7. Record signal for outcome tracking
      if(EnableOutcomeTracker && g_lastAnalysis.isValid
         && (g_lastAnalysis.direction == "BUY" || g_lastAnalysis.direction == "SELL")
         && g_lastAnalysis.confidence >= MinConfidence)
      {
         RecordSignal(g_lastAnalysis.direction,
                      SymbolInfoDouble(Symbol(), g_lastAnalysis.direction == "BUY" ? SYMBOL_ASK : SYMBOL_BID),
                      g_lastAnalysis.confidence,
                      g_lastAnalysis.suggestedTP1, g_lastAnalysis.suggestedSL);
      }

      // 8. Cloud sync (secondary — for dashboard, not for trading decisions)
      RequestSwarmSignal();

      g_lastPollTime = TimeCurrent();
      g_totalSignals++;
   }

   // Update signal outcomes every tick cycle
   if(EnableOutcomeTracker)
      UpdateSignalOutcomes();

   // Position close detection — reset tracking when position disappears
   if(g_activePositionTicket > 0)
   {
      bool found = false;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionGetSymbol(i) == Symbol() && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            if(PositionGetTicket(i) == g_activePositionTicket)
            {
               found = true;
               break;
            }
         }
      }
      if(!found)
      {
         g_activePositionTicket = 0;
         g_partialTP1Fired = false;
         g_partialTP2Fired = false;
      }
   }

   // Trailing stop management
   if(UseTrailingStop)
      ManageTrailingStops();

   // Supabase sync
   if(g_animFrame % 8 == 0)
      SyncAccountToSupabase();

   // Copy trading receiver
   if(EnableCopyReceiver && g_animFrame % 2 == 0)
      PollRemoteWebCommands();

   // Metrics and HUD
   CalculateAccountMetrics();
   if(ShowAdvancedHUD)
      Render3DHUD();
}

//+------------------------------------------------------------------+
//| Tick function                                                       |
//+------------------------------------------------------------------+
void OnTick()
{
   CalculateAccountMetrics();
}

//+------------------------------------------------------------------+
//| Apply 3D Obsidian & Neon Candle Theme                             |
//+------------------------------------------------------------------+
void Apply3DNeonTheme()
{
   ChartSetInteger(0, CHART_MODE, CHART_CANDLES);
   ChartSetInteger(0, CHART_COLOR_BACKGROUND, C'8,11,18');
   ChartSetInteger(0, CHART_COLOR_FOREGROUND, C'170,185,210');
   ChartSetInteger(0, CHART_COLOR_GRID, C'18,24,38');
   ChartSetInteger(0, CHART_COLOR_CANDLE_BULL, C'0,255,136');
   ChartSetInteger(0, CHART_COLOR_CANDLE_BEAR, C'255,34,85');
   ChartSetInteger(0, CHART_COLOR_CHART_UP, C'0,255,136');
   ChartSetInteger(0, CHART_COLOR_CHART_DOWN, C'255,34,85');
   ChartSetInteger(0, CHART_COLOR_CHART_LINE, C'0,229,255');
   ChartSetInteger(0, CHART_COLOR_BID, C'130,150,175');
   ChartSetInteger(0, CHART_COLOR_ASK, C'0,240,255');
   ChartSetInteger(0, CHART_SHOW_PERIOD_SEP, false);
   ChartSetInteger(0, CHART_AUTOSCROLL, true);
   ChartSetInteger(0, CHART_SHIFT, true);
   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| Calculate Financials, Win Rate, and Drawdown                      |
//+------------------------------------------------------------------+
void CalculateAccountMetrics()
{
   g_openProfit = AccountInfoDouble(ACCOUNT_PROFIT);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   if(balance > 0)
   {
      double dd = (balance - equity) / balance * 100.0;
      g_currentDrawdown = (dd > 0) ? dd : 0.0;
   }

   datetime todayStart = StringToTime(TimeToString(TimeCurrent(), TIME_DATE) + " 00:00:00");
   HistorySelect(todayStart, TimeCurrent());

   int totalDeals = HistoryDealsTotal();
   g_todayProfit = 0.0;
   int todayWins = 0;
   int todayCount = 0;

   for(int i = 0; i < totalDeals; i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket > 0)
      {
         long entry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
         if(entry == DEAL_ENTRY_OUT)
         {
            double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
            g_todayProfit += profit;
            todayCount++;
            if(profit > 0) todayWins++;
         }
      }
   }

   g_totalTrades = todayCount;
   g_winTrades = todayWins;
   g_totalProfit = g_todayProfit;

   if(g_currentDrawdown < 2.0)
   {
      g_recoveryLevel = "OPTIMAL (1.0x)";
      g_recoveryMult = 1.0;
   }
   else if(g_currentDrawdown < 5.0)
   {
      g_recoveryLevel = "CAUTION (0.85x)";
      g_recoveryMult = 0.85;
   }
   else if(g_currentDrawdown < 10.0)
   {
      g_recoveryLevel = "SHIELD (0.60x)";
      g_recoveryMult = 0.60;
   }
   else
   {
      g_recoveryLevel = "RECOVERY (0.35x)";
      g_recoveryMult = 0.35;
   }
}

string GetInstrument() { return Symbol(); }
string GetTimeframe()
{
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
      default:         return "H1";
   }
}

//+------------------------------------------------------------------+
//| Session Detection Utility                                          |
//+------------------------------------------------------------------+
string GetCurrentSession()
{
   MqlDateTime gmtTime;
   TimeGMT(gmtTime);
   int hour = gmtTime.hour;

   // Overlapping sessions
   bool sydney  = (hour >= 22 || hour < 7);
   bool tokyo   = (hour >= 0 && hour < 9);
   bool london  = (hour >= 7 && hour < 16);
   bool newyork = (hour >= 12 && hour < 21);

   if(london && newyork) return "LONDON/NY";
   if(sydney && tokyo)   return "SYDNEY/TOKYO";
   if(london)            return "LONDON";
   if(newyork)           return "NEW YORK";
   if(tokyo)             return "TOKYO";
   if(sydney)            return "SYDNEY";
   return "OFF-HOURS";
}

//+------------------------------------------------------------------+
//| Get Signal Strength Label                                          |
//+------------------------------------------------------------------+
string GetSignalStrength(double confidence)
{
   if(confidence >= 0.85) return "VERY STRONG";
   if(confidence >= 0.70) return "STRONG";
   if(confidence >= 0.55) return "MODERATE";
   if(confidence >= 0.40) return "WEAK";
   return "MINIMAL";
}

//+------------------------------------------------------------------+
//| Get Star Rating String from Confidence                             |
//+------------------------------------------------------------------+
string GetStarRating(double confidence)
{
   double pct = confidence * 100.0;
   if(pct >= 90.0) return "★★★★★";
   if(pct >= 75.0) return "★★★★☆";
   if(pct >= 65.0) return "★★★☆☆";
   if(pct >= 50.0) return "★★☆☆☆";
   return "★☆☆☆☆";
}

void TestConnection()
{
   string url = KestrelAPIUrl + "/api/status";
   string headers = "Authorization: Bearer " + KestrelAPIToken + "\r\nContent-Type: application/json\r\n";
   char post_data[], result[];
   string result_headers;
   ResetLastError();
   WebRequest("GET", url, headers, NULL, 4000, post_data, 0, result, result_headers);
   g_connectionStatus = "online";
}

//+------------------------------------------------------------------+
//| CANDLESTICK PATTERN & PRICE ACTION ANALYSIS ENGINE               |
//| Advanced recognition of 12+ institutional candle patterns,       |
//| Wick Rejection Force, Candle Anatomy, and Fair Value Gaps (FVG)   |
//+------------------------------------------------------------------+
void CleanCandleBadges()
{
   ObjectsDeleteAll(0, g_hudPrefix + "CND_");
}

void ComputeCandleAnatomy(const double &o[], const double &h[], const double &l[], const double &c[])
{
   double range0 = h[0] - l[0];
   double body0 = MathAbs(c[0] - o[0]);
   double upperWick0 = h[0] - MathMax(o[0], c[0]);
   double lowerWick0 = MathMin(o[0], c[0]) - l[0];

   if(range0 > 0)
   {
      g_candleAnatomy.bodyPct = (body0 / range0) * 100.0;
      g_candleAnatomy.upperWickPct = (upperWick0 / range0) * 100.0;
      g_candleAnatomy.lowerWickPct = (lowerWick0 / range0) * 100.0;

      // Real-time buying vs selling pressure calculation
      double buyerContribution = lowerWick0 + (c[0] > o[0] ? body0 : 0.0);
      g_candleAnatomy.buyingPressurePct = (buyerContribution / range0) * 100.0;
      g_candleAnatomy.sellingPressurePct = 100.0 - g_candleAnatomy.buyingPressurePct;
   }
   else
   {
      g_candleAnatomy.bodyPct = 0;
      g_candleAnatomy.upperWickPct = 0;
      g_candleAnatomy.lowerWickPct = 0;
      g_candleAnatomy.buyingPressurePct = 50.0;
      g_candleAnatomy.sellingPressurePct = 50.0;
   }

   // ATR relative ratio (20-bar average range)
   double avgRange = 0;
   for(int b = 1; b <= 20; b++)
      avgRange += (h[b] - l[b]);
   avgRange /= 20.0;

   if(avgRange > 0)
   {
      double range1 = h[1] - l[1];
      g_candleAnatomy.atrRatio = range1 / avgRange;
      g_candleAnatomy.isExpansionBar = (g_candleAnatomy.atrRatio >= 1.4);
      g_candleAnatomy.isCompressionBar = (g_candleAnatomy.atrRatio <= 0.6);
   }

   // Candle Countdown Timer
   datetime barTime = iTime(Symbol(), Period(), 0);
   int secLeft = (int)(barTime + PeriodSeconds() - TimeCurrent());
   if(secLeft < 0) secLeft = 0;
   g_candleAnatomy.secondsRemaining = secLeft;

   int mins = secLeft / 60;
   int secs = secLeft % 60;
   g_candleAnatomy.timeRemainingText = StringFormat("%02d:%02d", mins, secs);

   // Consecutive Direction Count
   int dir = 0;
   int count = 0;
   for(int b = 1; b <= 10; b++)
   {
      int currentDir = (c[b] > o[b]) ? 1 : ((c[b] < o[b]) ? -1 : 0);
      if(b == 1)
      {
         dir = currentDir;
         if(dir != 0) count++;
         else break;
      }
      else
      {
         if(currentDir == dir) count++;
         else break;
      }
   }
   g_candleAnatomy.consecutiveDir = dir;
   g_candleAnatomy.consecutiveCount = count;
}

bool DetectThreeCandlePatterns(const double &o[], const double &h[], const double &l[], const double &c[], const datetime &t[])
{
   double r1 = h[1] - l[1];
   double b1 = MathAbs(c[1] - o[1]);
   double r2 = h[2] - l[2];
   double b2 = MathAbs(c[2] - o[2]);
   double r3 = h[3] - l[3];
   double b3 = MathAbs(c[3] - o[3]);

   if(r1 <= 0 || r2 <= 0 || r3 <= 0) return false;

   // 1. Morning Star (Bullish Reversal: Bear bar 3 -> small bar 2 -> Bull bar 1)
   if(c[3] < o[3] && b3 / r3 >= 0.45 &&
      b2 <= b3 * 0.5 &&
      c[1] > o[1] && c[1] >= (o[3] + c[3]) / 2.0)
   {
      g_activePattern.patternName = "Morning Star";
      g_activePattern.direction = "BULLISH";
      g_activePattern.confidence = 0.95;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "3-bar bullish reversal with strong rejection";
      g_activePattern.vote = 1;
      return true;
   }

   // 2. Evening Star (Bearish Reversal: Bull bar 3 -> small bar 2 -> Bear bar 1)
   if(c[3] > o[3] && b3 / r3 >= 0.45 &&
      b2 <= b3 * 0.5 &&
      c[1] < o[1] && c[1] <= (o[3] + c[3]) / 2.0)
   {
      g_activePattern.patternName = "Evening Star";
      g_activePattern.direction = "BEARISH";
      g_activePattern.confidence = 0.95;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "3-bar bearish reversal with strong rejection";
      g_activePattern.vote = -1;
      return true;
   }

   // 3. Three White Soldiers (Strong Bullish Continuation)
   if(c[1] > o[1] && c[2] > o[2] && c[3] > o[3] &&
      c[1] > c[2] && c[2] > c[3] &&
      b1 / r1 >= 0.60 && b2 / r2 >= 0.60 && b3 / r3 >= 0.60)
   {
      g_activePattern.patternName = "3 White Soldiers";
      g_activePattern.direction = "BULLISH";
      g_activePattern.confidence = 0.92;
      g_activePattern.category = "CONTINUATION";
      g_activePattern.description = "Consecutive institutional buying pressure";
      g_activePattern.vote = 1;
      return true;
   }

   // 4. Three Black Crows (Strong Bearish Continuation)
   if(c[1] < o[1] && c[2] < o[2] && c[3] < o[3] &&
      c[1] < c[2] && c[2] < c[3] &&
      b1 / r1 >= 0.60 && b2 / r2 >= 0.60 && b3 / r3 >= 0.60)
   {
      g_activePattern.patternName = "3 Black Crows";
      g_activePattern.direction = "BEARISH";
      g_activePattern.confidence = 0.92;
      g_activePattern.category = "CONTINUATION";
      g_activePattern.description = "Consecutive institutional selling pressure";
      g_activePattern.vote = -1;
      return true;
   }

   return false;
}

bool DetectTwoCandlePatterns(const double &o[], const double &h[], const double &l[], const double &c[], const datetime &t[])
{
   double r1 = h[1] - l[1];
   double b1 = MathAbs(c[1] - o[1]);
   double r2 = h[2] - l[2];
   double b2 = MathAbs(c[2] - o[2]);

   if(r1 <= 0 || r2 <= 0) return false;

   // 1. Bullish Engulfing
   if(c[2] < o[2] && c[1] > o[1] &&
      c[1] >= o[2] && o[1] <= c[2] && b1 > b2)
   {
      g_activePattern.patternName = "Bullish Engulfing";
      g_activePattern.direction = "BULLISH";
      g_activePattern.confidence = 0.92;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Bull candle completely engulfs previous bear body";
      g_activePattern.vote = 1;
      return true;
   }

   // 2. Bearish Engulfing
   if(c[2] > o[2] && c[1] < o[1] &&
      c[1] <= o[2] && o[1] >= c[2] && b1 > b2)
   {
      g_activePattern.patternName = "Bearish Engulfing";
      g_activePattern.direction = "BEARISH";
      g_activePattern.confidence = 0.92;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Bear candle completely engulfs previous bull body";
      g_activePattern.vote = -1;
      return true;
   }

   // 3. Piercing Line (Bullish reversal)
   if(c[2] < o[2] && c[1] > o[1] &&
      o[1] < l[2] && c[1] >= (o[2] + c[2]) / 2.0 && c[1] < o[2])
   {
      g_activePattern.patternName = "Piercing Line";
      g_activePattern.direction = "BULLISH";
      g_activePattern.confidence = 0.84;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Bullish piercing >50% into bear candle body";
      g_activePattern.vote = 1;
      return true;
   }

   // 4. Dark Cloud Cover (Bearish reversal)
   if(c[2] > o[2] && c[1] < o[1] &&
      o[1] > h[2] && c[1] <= (o[2] + c[2]) / 2.0 && c[1] > o[2])
   {
      g_activePattern.patternName = "Dark Cloud Cover";
      g_activePattern.direction = "BEARISH";
      g_activePattern.confidence = 0.84;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Bearish cloud piercing >50% into bull candle body";
      g_activePattern.vote = -1;
      return true;
   }

   // 5. Tweezer Tops (Equal highs with upper wicks)
   double highDiff = MathAbs(h[1] - h[2]);
   double upperWick1 = h[1] - MathMax(o[1], c[1]);
   double upperWick2 = h[2] - MathMax(o[2], c[2]);
   if(highDiff <= r1 * 0.10 && upperWick1 >= r1 * 0.35 && upperWick2 >= r2 * 0.35)
   {
      g_activePattern.patternName = "Tweezer Top";
      g_activePattern.direction = "BEARISH";
      g_activePattern.confidence = 0.86;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Dual rejection from ceiling resistance";
      g_activePattern.vote = -1;
      return true;
   }

   // 6. Tweezer Bottoms (Equal lows with lower wicks)
   double lowDiff = MathAbs(l[1] - l[2]);
   double lowerWick1 = MathMin(o[1], c[1]) - l[1];
   double lowerWick2 = MathMin(o[2], c[2]) - l[2];
   if(lowDiff <= r1 * 0.10 && lowerWick1 >= r1 * 0.35 && lowerWick2 >= r2 * 0.35)
   {
      g_activePattern.patternName = "Tweezer Bottom";
      g_activePattern.direction = "BULLISH";
      g_activePattern.confidence = 0.86;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Dual rejection from floor support";
      g_activePattern.vote = 1;
      return true;
   }

   // 7. Inside Bar / Harami (Compression / Breakout Pending)
   if(h[1] <= h[2] && l[1] >= l[2])
   {
      g_activePattern.patternName = "Inside Bar";
      g_activePattern.direction = "NEUTRAL";
      g_activePattern.confidence = 0.78;
      g_activePattern.category = "COMPRESSION";
      g_activePattern.description = "Volatility compression inside mother bar — breakout imminent";
      g_activePattern.vote = 0;
      return true;
   }

   return false;
}

bool DetectSingleCandlePatterns(const double &o[], const double &h[], const double &l[], const double &c[], const datetime &t[])
{
   double r1 = h[1] - l[1];
   double b1 = MathAbs(c[1] - o[1]);
   double upperWick1 = h[1] - MathMax(o[1], c[1]);
   double lowerWick1 = MathMin(o[1], c[1]) - l[1];

   if(r1 <= 0) return false;

   // 1. Hammer / Pin Bar (Bullish Rejection: Lower wick >= 55% of range, small upper wick)
   if(lowerWick1 >= r1 * 0.55 && upperWick1 <= r1 * 0.20 && b1 <= r1 * 0.38)
   {
      g_activePattern.patternName = "Hammer / Pin Bar";
      g_activePattern.direction = "BULLISH";
      g_activePattern.confidence = 0.88;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Rejection of lower prices by aggressive buyers";
      g_activePattern.vote = 1;
      return true;
   }

   // 2. Shooting Star / Pin Bar (Bearish Rejection: Upper wick >= 55% of range, small lower wick)
   if(upperWick1 >= r1 * 0.55 && lowerWick1 <= r1 * 0.20 && b1 <= r1 * 0.38)
   {
      g_activePattern.patternName = "Shooting Star";
      g_activePattern.direction = "BEARISH";
      g_activePattern.confidence = 0.88;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Rejection of higher prices by aggressive sellers";
      g_activePattern.vote = -1;
      return true;
   }

   // 3. Institutional Marubozu (Expansion momentum candle: body >= 80% of range)
   if(b1 >= r1 * 0.80)
   {
      if(c[1] > o[1])
      {
         g_activePattern.patternName = "Bullish Marubozu";
         g_activePattern.direction = "BULLISH";
         g_activePattern.confidence = 0.85;
         g_activePattern.category = "CONTINUATION";
         g_activePattern.description = "Institutional expansion candle with upward momentum";
         g_activePattern.vote = 1;
         return true;
      }
      else
      {
         g_activePattern.patternName = "Bearish Marubozu";
         g_activePattern.direction = "BEARISH";
         g_activePattern.confidence = 0.85;
         g_activePattern.category = "CONTINUATION";
         g_activePattern.description = "Institutional expansion candle with downward momentum";
         g_activePattern.vote = -1;
         return true;
      }
   }

   // 4. Dragonfly Doji (Bullish Reversal: Open ~ Close at top, long lower shadow)
   if(b1 <= r1 * 0.10 && lowerWick1 >= r1 * 0.65)
   {
      g_activePattern.patternName = "Dragonfly Doji";
      g_activePattern.direction = "BULLISH";
      g_activePattern.confidence = 0.82;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Rejection from lows with minimal body";
      g_activePattern.vote = 1;
      return true;
   }

   // 5. Gravestone Doji (Bearish Reversal: Open ~ Close at bottom, long upper shadow)
   if(b1 <= r1 * 0.10 && upperWick1 >= r1 * 0.65)
   {
      g_activePattern.patternName = "Gravestone Doji";
      g_activePattern.direction = "BEARISH";
      g_activePattern.confidence = 0.82;
      g_activePattern.category = "REVERSAL";
      g_activePattern.description = "Rejection from highs with minimal body";
      g_activePattern.vote = -1;
      return true;
   }

   // 6. Neutral Doji (Indecision)
   if(b1 <= r1 * 0.10)
   {
      g_activePattern.patternName = "Doji Indecision";
      g_activePattern.direction = "NEUTRAL";
      g_activePattern.confidence = 0.60;
      g_activePattern.category = "COMPRESSION";
      g_activePattern.description = "Market equilibrium and pause before next impulse";
      g_activePattern.vote = 0;
      return true;
   }

   return false;
}

void DetectFairValueGaps(const double &o[], const double &h[], const double &l[], const double &c[], const datetime &t[])
{
   g_activeFVG.active = false;
   double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);

   for(int i = 1; i <= 8; i++)
   {
      // Bullish FVG: Low of candle i > High of candle i+2
      if(l[i] > h[i+2] + point * 5)
      {
         bool mitigated = false;
         for(int m = 0; m < i; m++)
         {
            if(l[m] <= h[i+2]) { mitigated = true; break; }
         }
         if(!mitigated)
         {
            g_activeFVG.active = true;
            g_activeFVG.direction = "BULLISH";
            g_activeFVG.topPrice = l[i];
            g_activeFVG.bottomPrice = h[i+2];
            g_activeFVG.barIndex = i;
            g_activeFVG.barTime = t[i];
            g_activeFVG.mitigated = false;
            break;
         }
      }
      // Bearish FVG: High of candle i < Low of candle i+2
      else if(h[i] < l[i+2] - point * 5)
      {
         bool mitigated = false;
         for(int m = 0; m < i; m++)
         {
            if(h[m] >= l[i+2]) { mitigated = true; break; }
         }
         if(!mitigated)
         {
            g_activeFVG.active = true;
            g_activeFVG.direction = "BEARISH";
            g_activeFVG.topPrice = l[i+2];
            g_activeFVG.bottomPrice = h[i];
            g_activeFVG.barIndex = i;
            g_activeFVG.barTime = t[i];
            g_activeFVG.mitigated = false;
            break;
         }
      }
   }
}

void CollectAndDrawCandleBadges(const double &o[], const double &h[], const double &l[], const double &c[], const datetime &t[])
{
   CleanCandleBadges();
   int badgesDrawn = 0;

   for(int b = 1; b <= 15 && badgesDrawn < MaxCandleBadges; b++)
   {
      double r = h[b] - l[b];
      double body = MathAbs(c[b] - o[b]);
      double upper = h[b] - MathMax(o[b], c[b]);
      double lower = MathMin(o[b], c[b]) - l[b];
      if(r <= 0) continue;

      string badgeText = "";
      color badgeCol = C'255,255,255';
      double tagPrice = 0;

      // 1. Engulfing
      if(b <= 14 && c[b+1] < o[b+1] && c[b] > o[b] && c[b] >= o[b+1] && o[b] <= c[b+1] && body > MathAbs(c[b+1] - o[b+1]))
      {
         badgeText = "▲ ENGULF";
         badgeCol = C'0,255,136';
         tagPrice = l[b] - r * 0.20;
      }
      else if(b <= 14 && c[b+1] > o[b+1] && c[b] < o[b] && c[b] <= o[b+1] && o[b] >= c[b+1] && body > MathAbs(c[b+1] - o[b+1]))
      {
         badgeText = "▼ ENGULF";
         badgeCol = C'255,45,85';
         tagPrice = h[b] + r * 0.20;
      }
      // 2. Pin bar / Hammer
      else if(lower >= r * 0.55 && upper <= r * 0.20)
      {
         badgeText = "▲ HAMMER";
         badgeCol = C'0,255,136';
         tagPrice = l[b] - r * 0.20;
      }
      else if(upper >= r * 0.55 && lower <= r * 0.20)
      {
         badgeText = "▼ STAR";
         badgeCol = C'255,45,85';
         tagPrice = h[b] + r * 0.20;
      }
      // 3. Marubozu
      else if(body >= r * 0.80)
      {
         if(c[b] > o[b]) { badgeText = "▲ MARUBOZU"; badgeCol = C'0,229,255'; tagPrice = l[b] - r * 0.20; }
         else            { badgeText = "▼ MARUBOZU"; badgeCol = C'255,100,200'; tagPrice = h[b] + r * 0.20; }
      }

      if(badgeText != "")
      {
         string objName = g_hudPrefix + "CND_" + IntegerToString(b);
         ObjectCreate(0, objName, OBJ_TEXT, 0, t[b], tagPrice);
         ObjectSetString(0, objName, OBJPROP_TEXT, badgeText);
         ObjectSetString(0, objName, OBJPROP_FONT, "Segoe UI Bold");
         ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, 7);
         ObjectSetInteger(0, objName, OBJPROP_COLOR, badgeCol);
         ObjectSetInteger(0, objName, OBJPROP_ANCHOR, (tagPrice > h[b]) ? ANCHOR_LOWER : ANCHOR_UPPER);
         ObjectSetInteger(0, objName, OBJPROP_BACK, false);
         ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
         badgesDrawn++;
      }
   }

   // Subtle outline for active FVG
   if(EnableFVGDetection && g_activeFVG.active)
   {
      string fvgName = g_hudPrefix + "CND_FVG_BOX";
      datetime t1 = g_activeFVG.barTime;
      datetime t2 = iTime(Symbol(), Period(), 0) + PeriodSeconds() * 8;
      ObjectCreate(0, fvgName, OBJ_RECTANGLE, 0, t1, g_activeFVG.topPrice, t2, g_activeFVG.bottomPrice);
      color fvgCol = (g_activeFVG.direction == "BULLISH") ? C'0,180,120' : C'200,60,80';
      ObjectSetInteger(0, fvgName, OBJPROP_COLOR, fvgCol);
      ObjectSetInteger(0, fvgName, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, fvgName, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, fvgName, OBJPROP_FILL, false); // CLEAN OUTLINE, NO SOLID OPACITY
      ObjectSetInteger(0, fvgName, OBJPROP_BACK, true);
      ObjectSetInteger(0, fvgName, OBJPROP_SELECTABLE, false);
      ObjectSetString(0, fvgName, OBJPROP_TOOLTIP, "Fair Value Gap (" + g_activeFVG.direction + ")");
   }
}

void AnalyzeCandlesticks()
{
   int barsNeeded = 25;
   double o[], h[], l[], c[];
   datetime t[];
   ArraySetAsSeries(o, true);
   ArraySetAsSeries(h, true);
   ArraySetAsSeries(l, true);
   ArraySetAsSeries(c, true);
   ArraySetAsSeries(t, true);

   if(CopyOpen(Symbol(), Period(), 0, barsNeeded, o) < barsNeeded ||
      CopyHigh(Symbol(), Period(), 0, barsNeeded, h) < barsNeeded ||
      CopyLow(Symbol(), Period(), 0, barsNeeded, l) < barsNeeded ||
      CopyClose(Symbol(), Period(), 0, barsNeeded, c) < barsNeeded ||
      CopyTime(Symbol(), Period(), 0, barsNeeded, t) < barsNeeded)
      return;

   // 1. Compute Live Candle Anatomy & Countdown (Bar 0 & Bar 1)
   ComputeCandleAnatomy(o, h, l, c);

   // 2. Clear Active Pattern
   g_activePattern.patternName = "";
   g_activePattern.direction = "NEUTRAL";
   g_activePattern.confidence = 0.0;
   g_activePattern.category = "NONE";
   g_activePattern.barIndex = 1;
   g_activePattern.barTime = t[1];
   g_activePattern.patternPrice = c[1];
   g_activePattern.description = "Normal Price Action";
   g_activePattern.vote = 0;

   // 3. Detect 3-bar, 2-bar, and 1-bar patterns on confirmed closed candles (Bar 1)
   bool patternFound = false;

   // Check 3-Bar Formations first
   patternFound = DetectThreeCandlePatterns(o, h, l, c, t);

   // If not found, check 2-Bar Formations
   if(!patternFound)
      patternFound = DetectTwoCandlePatterns(o, h, l, c, t);

   // If not found, check 1-Bar Formations
   if(!patternFound)
      DetectSingleCandlePatterns(o, h, l, c, t);

   // 4. Detect Fair Value Gaps (FVG)
   if(EnableFVGDetection)
      DetectFairValueGaps(o, h, l, c, t);

   // 5. Draw badges on chart
   if(ShowCandleBadges)
      CollectAndDrawCandleBadges(o, h, l, c, t);
}

//+------------------------------------------------------------------+
//| ★ CORE: Multi-Indicator Confluence Analysis Engine ★              |
//| This is the REAL brain — 9 weighted indicators, no randomness    |
//+------------------------------------------------------------------+
ConfluenceAnalysis AnalyzeMarketConfluence()
{
   ConfluenceAnalysis result;
   ZeroMemory(result);
   result.analysisTime = TimeCurrent();
   result.direction = "HOLD";
   result.isValid = false;

   double totalScore = 0.0;
   double totalWeight = 0.0;
   int indicatorsOk = 0;
   string reasons = "";

   double closePrice = iClose(Symbol(), Period(), 0);
   double openPrice  = iOpen(Symbol(), Period(), 0);

   // ================================================================
   // 1. EMA STACK ANALYSIS (Weight: 0.20)
   // ================================================================
   double ema9[], ema21[], ema50[], ema200[];
   ArraySetAsSeries(ema9, true);
   ArraySetAsSeries(ema21, true);
   ArraySetAsSeries(ema50, true);
   ArraySetAsSeries(ema200, true);

   bool emaOk = (g_hEma9 != INVALID_HANDLE && g_hEma21 != INVALID_HANDLE &&
                 g_hEma50 != INVALID_HANDLE && g_hEma200 != INVALID_HANDLE &&
                 CopyBuffer(g_hEma9, 0, 0, 2, ema9) >= 2 &&
                 CopyBuffer(g_hEma21, 0, 0, 2, ema21) >= 2 &&
                 CopyBuffer(g_hEma50, 0, 0, 1, ema50) >= 1 &&
                 CopyBuffer(g_hEma200, 0, 0, 1, ema200) >= 1);

   if(emaOk)
   {
      double w = 0.20;
      int vote = 0;
      result.ema9Val  = ema9[0];
      result.ema21Val = ema21[0];
      result.ema50Val = ema50[0];
      result.ema200Val = ema200[0];

      if(ema9[0] > ema21[0] && ema21[0] > ema50[0] && ema50[0] > ema200[0])
      {
         vote = 1;
         reasons += "EMA Bullish Stack, ";
      }
      else if(ema9[0] < ema21[0] && ema21[0] < ema50[0] && ema50[0] < ema200[0])
      {
         vote = -1;
         reasons += "EMA Bearish Stack, ";
      }
      else if(ema9[0] > ema21[0] && closePrice > ema50[0])
      {
         vote = 1;
         reasons += "EMA Bullish Cross, ";
      }
      else if(ema9[0] < ema21[0] && closePrice < ema50[0])
      {
         vote = -1;
         reasons += "EMA Bearish Cross, ";
      }
      else
      {
         reasons += "EMA Mixed, ";
      }

      result.emaVote = vote;
      totalScore += vote * w;
      totalWeight += w;
      indicatorsOk++;
   }

   // ================================================================
   // 2. RSI 14 (Weight: 0.15)
   // ================================================================
   double rsi[];
   ArraySetAsSeries(rsi, true);

   bool rsiOk = (g_hRsi14 != INVALID_HANDLE && CopyBuffer(g_hRsi14, 0, 0, 1, rsi) >= 1);

   if(rsiOk)
   {
      double w = 0.15;
      int vote = 0;
      result.rsiValue = rsi[0];

      if(rsi[0] > 55.0 && rsi[0] < 75.0)
      {
         vote = 1;
         reasons += "RSI Bullish(" + DoubleToString(rsi[0], 1) + "), ";
      }
      else if(rsi[0] < 45.0 && rsi[0] > 25.0)
      {
         vote = -1;
         reasons += "RSI Bearish(" + DoubleToString(rsi[0], 1) + "), ";
      }
      else if(rsi[0] >= 75.0)
      {
         vote = 0;
         reasons += "RSI Overbought(" + DoubleToString(rsi[0], 1) + "), ";
      }
      else if(rsi[0] <= 25.0)
      {
         vote = 0;
         reasons += "RSI Oversold(" + DoubleToString(rsi[0], 1) + "), ";
      }
      else
      {
         reasons += "RSI Neutral(" + DoubleToString(rsi[0], 1) + "), ";
      }

      result.rsiVote = vote;
      totalScore += vote * w;
      totalWeight += w;
      indicatorsOk++;
   }

   // ================================================================
   // 3. MACD (12,26,9) (Weight: 0.12)
   // ================================================================
   double macdMain[], macdSignal[];
   ArraySetAsSeries(macdMain, true);
   ArraySetAsSeries(macdSignal, true);

   bool macdOk = (g_hMacd != INVALID_HANDLE &&
                  CopyBuffer(g_hMacd, 0, 0, 1, macdMain) >= 1 &&
                  CopyBuffer(g_hMacd, 1, 0, 1, macdSignal) >= 1);

   if(macdOk)
   {
      double w = 0.12;
      int vote = 0;
      result.macdMain = macdMain[0];
      result.macdSignal = macdSignal[0];
      double histogram = macdMain[0] - macdSignal[0];

      if(macdMain[0] > macdSignal[0] && histogram > 0)
      {
         vote = 1;
         reasons += "MACD Bullish, ";
      }
      else if(macdMain[0] < macdSignal[0] && histogram < 0)
      {
         vote = -1;
         reasons += "MACD Bearish, ";
      }
      else
      {
         reasons += "MACD Crossing, ";
      }

      result.macdVote = vote;
      totalScore += vote * w;
      totalWeight += w;
      indicatorsOk++;
   }

   // ================================================================
   // 4. BOLLINGER BANDS 20,2 (Weight: 0.10)
   // ================================================================
   double bbMid[], bbUpper[], bbLower[];
   ArraySetAsSeries(bbMid, true);
   ArraySetAsSeries(bbUpper, true);
   ArraySetAsSeries(bbLower, true);

   bool bbOk = (g_hBB20 != INVALID_HANDLE &&
                CopyBuffer(g_hBB20, 0, 0, 1, bbMid) >= 1 &&
                CopyBuffer(g_hBB20, 1, 0, 1, bbUpper) >= 1 &&
                CopyBuffer(g_hBB20, 2, 0, 1, bbLower) >= 1);

   if(bbOk)
   {
      double w = 0.10;
      int vote = 0;
      result.bbUpper = bbUpper[0];
      result.bbLower = bbLower[0];

      if(closePrice > bbMid[0] && closePrice < bbUpper[0])
      {
         vote = 1;
         reasons += "BB Above Mid, ";
      }
      else if(closePrice < bbMid[0] && closePrice > bbLower[0])
      {
         vote = -1;
         reasons += "BB Below Mid, ";
      }
      else if(closePrice >= bbUpper[0])
      {
         vote = 0;
         reasons += "BB Upper Touch, ";
      }
      else if(closePrice <= bbLower[0])
      {
         vote = 0;
         reasons += "BB Lower Touch, ";
      }

      result.bbVote = vote;
      totalScore += vote * w;
      totalWeight += w;
      indicatorsOk++;
   }

   // ================================================================
   // 5. STOCHASTIC (14,3,3) (Weight: 0.08)
   // ================================================================
   double stochK[];
   ArraySetAsSeries(stochK, true);

   bool stochOk = (g_hStoch != INVALID_HANDLE && CopyBuffer(g_hStoch, 0, 0, 1, stochK) >= 1);

   if(stochOk)
   {
      double w = 0.08;
      int vote = 0;
      result.stochMain = stochK[0];

      if(stochK[0] > 50.0 && stochK[0] < 80.0)
      {
         vote = 1;
         reasons += "Stoch Bullish(" + DoubleToString(stochK[0], 0) + "), ";
      }
      else if(stochK[0] < 50.0 && stochK[0] > 20.0)
      {
         vote = -1;
         reasons += "Stoch Bearish(" + DoubleToString(stochK[0], 0) + "), ";
      }
      else if(stochK[0] >= 80.0)
      {
         vote = 0;
         reasons += "Stoch OB(" + DoubleToString(stochK[0], 0) + "), ";
      }
      else
      {
         vote = 0;
         reasons += "Stoch OS(" + DoubleToString(stochK[0], 0) + "), ";
      }

      result.stochVote = vote;
      totalScore += vote * w;
      totalWeight += w;
      indicatorsOk++;
   }

   // ================================================================
   // 6. ADX 14 (Weight: 0.10)
   // ================================================================
   double adx[], plusDI[], minusDI[];
   ArraySetAsSeries(adx, true);
   ArraySetAsSeries(plusDI, true);
   ArraySetAsSeries(minusDI, true);

   bool adxOk = (g_hAdx14 != INVALID_HANDLE &&
                 CopyBuffer(g_hAdx14, 0, 0, 1, adx) >= 1 &&
                 CopyBuffer(g_hAdx14, 1, 0, 1, plusDI) >= 1 &&
                 CopyBuffer(g_hAdx14, 2, 0, 1, minusDI) >= 1);

   if(adxOk)
   {
      double w = 0.10;
      int vote = 0;
      result.adxValue = adx[0];

      if(adx[0] > 25.0)
      {
         if(plusDI[0] > minusDI[0])
         {
            vote = 1;
            reasons += "ADX Uptrend(" + DoubleToString(adx[0], 0) + "), ";
         }
         else
         {
            vote = -1;
            reasons += "ADX Downtrend(" + DoubleToString(adx[0], 0) + "), ";
         }
      }
      else if(adx[0] < 20.0)
      {
         vote = 0;
         reasons += "ADX Ranging(" + DoubleToString(adx[0], 0) + "), ";
      }
      else
      {
         if(plusDI[0] > minusDI[0]) vote = 1;
         else vote = -1;
         reasons += "ADX Weak(" + DoubleToString(adx[0], 0) + "), ";
      }

      result.adxVote = vote;
      totalScore += vote * w;
      totalWeight += w;
      indicatorsOk++;
   }

   // ================================================================
   // 7. VOLUME CONFIRMATION (Weight: 0.10)
   // ================================================================
   long tickVol[];
   ArraySetAsSeries(tickVol, true);

   bool volOk = (CopyTickVolume(Symbol(), Period(), 0, 22, tickVol) >= 22);

   if(volOk)
   {
      double w = 0.10;
      int vote = 0;

      long currentVol = tickVol[1];
      double avgVol = 0;
      for(int v = 2; v <= 21; v++)
         avgVol += (double)tickVol[v];
      avgVol /= 20.0;

      if(avgVol > 0 && (double)currentVol > avgVol * 1.2)
      {
         double prevClose = iClose(Symbol(), Period(), 1);
         double prevOpen  = iOpen(Symbol(), Period(), 1);
         if(prevClose > prevOpen)
         {
            vote = 1;
            reasons += "Vol Bullish, ";
         }
         else
         {
            vote = -1;
            reasons += "Vol Bearish, ";
         }
      }
      else
      {
         vote = 0;
         reasons += "Vol Low, ";
      }

      result.volumeVote = vote;
      totalScore += vote * w;
      totalWeight += w;
      indicatorsOk++;
   }

   // ================================================================
   // 8. H4 HIGHER-TIMEFRAME TREND (Weight: 0.15)
   // ================================================================
   double h4Ema[];
   double h4Close[];
   ArraySetAsSeries(h4Ema, true);
   ArraySetAsSeries(h4Close, true);

   bool h4Ok = (g_hH4Ema50 != INVALID_HANDLE &&
                CopyBuffer(g_hH4Ema50, 0, 0, 1, h4Ema) >= 1 &&
                CopyClose(Symbol(), PERIOD_H4, 0, 1, h4Close) >= 1);

   if(h4Ok)
   {
      double w = 0.15;
      int vote = 0;

      if(h4Close[0] > h4Ema[0])
      {
         vote = 1;
         reasons += "H4 Bullish, ";
      }
      else
      {
         vote = -1;
         reasons += "H4 Bearish, ";
      }

      result.h4TrendVote = vote;
      totalScore += vote * w;
      totalWeight += w;
      indicatorsOk++;
   }

   // ================================================================
   // 9. CANDLESTICK PATTERN & ANATOMY (Weight: 0.12)
   // ================================================================
   if(EnableCandleAnalysis)
   {
      AnalyzeCandlesticks();
      double w = 0.12;
      result.candleVote = g_activePattern.vote;
      totalScore += g_activePattern.vote * w;
      totalWeight += w;
      indicatorsOk++;
      if(g_activePattern.vote > 0)
         reasons += "Candle:" + g_activePattern.patternName + "↑, ";
      else if(g_activePattern.vote < 0)
         reasons += "Candle:" + g_activePattern.patternName + "↓, ";
      else if(g_activePattern.patternName != "")
         reasons += "Candle:" + g_activePattern.patternName + ", ";
   }
   else
   {
      result.candleVote = 0;
   }

   // ================================================================
   // CRASH/BOOM DIRECTIONAL BIAS (Bonus Adjustment)
   // ================================================================
   string sym = Symbol();
   if(EnableSpikeHunter)
   {
      if(StringFind(sym, "Crash") >= 0)
      {
         totalScore += 0.08;
         reasons += "Crash↑Bias, ";
      }
      else if(StringFind(sym, "Boom") >= 0)
      {
         totalScore -= 0.08;
         reasons += "Boom↓Bias, ";
      }
   }

   // ================================================================
   // FINAL CONFLUENCE CALCULATION
   // ================================================================
   result.indicatorsAvailable = indicatorsOk;
   int maxExpected = EnableCandleAnalysis ? 9 : 8;

   if(indicatorsOk < 5)
   {
      result.isValid = false;
      result.direction = "HOLD";
      result.confidence = 0.0;
      result.reasoning = "Insufficient data (" + IntegerToString(indicatorsOk) + "/" + IntegerToString(maxExpected) + " indicators)";
      Print("⚠️ [ANALYSIS]: Only ", indicatorsOk, "/", maxExpected, " indicators available. Waiting for data...");
      return result;
   }

   double normalizedScore = (totalWeight > 0) ? totalScore / totalWeight : 0.0;
   double availabilityFactor = MathSqrt((double)indicatorsOk / (double)maxExpected);
   normalizedScore *= availabilityFactor;

   result.score = normalizedScore;
   result.confidence = MathAbs(normalizedScore);

   if(normalizedScore > 0.0 && result.confidence >= 0.25)
      result.direction = "BUY";
   else if(normalizedScore < 0.0 && result.confidence >= 0.25)
      result.direction = "SELL";
   else
      result.direction = "HOLD";

   if(StringLen(reasons) > 2)
      reasons = StringSubstr(reasons, 0, StringLen(reasons) - 2);
   result.reasoning = result.direction + ": " + reasons;

   result.isValid = true;

   // ================================================================
   // ATR-BASED SL/TP CALCULATION
   // ================================================================
   double atrBuf[];
   ArraySetAsSeries(atrBuf, true);
   double atrVal = 0;
   if(g_hAtr14 != INVALID_HANDLE && CopyBuffer(g_hAtr14, 0, 0, 1, atrBuf) >= 1)
      atrVal = atrBuf[0];

   double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
   if(atrVal <= 0)
      atrVal = point * 300;

   if(EnableSpikeHunter && (StringFind(sym, "Boom") >= 0 || StringFind(sym, "Crash") >= 0))
      atrVal *= 1.8;

   result.atrValue = atrVal;

   double ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
   double bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);
   int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);

   if(result.direction == "BUY")
   {
      result.suggestedSL  = NormalizeDouble(ask - atrVal * SL_ATR_Mult, digits);
      result.suggestedTP1 = NormalizeDouble(ask + atrVal * TP1_ATR_Mult, digits);
      result.suggestedTP2 = NormalizeDouble(ask + atrVal * TP2_ATR_Mult, digits);
      result.suggestedTP3 = NormalizeDouble(ask + atrVal * TP3_ATR_Mult, digits);
   }
   else if(result.direction == "SELL")
   {
      result.suggestedSL  = NormalizeDouble(bid + atrVal * SL_ATR_Mult, digits);
      result.suggestedTP1 = NormalizeDouble(bid - atrVal * TP1_ATR_Mult, digits);
      result.suggestedTP2 = NormalizeDouble(bid - atrVal * TP2_ATR_Mult, digits);
      result.suggestedTP3 = NormalizeDouble(bid - atrVal * TP3_ATR_Mult, digits);
   }

   if(adxOk && adx[0] > 25.0)
      g_lastRegime = "Trending (" + DoubleToString(adx[0], 0) + " ADX)";
   else if(adxOk && adx[0] < 20.0)
      g_lastRegime = "Ranging (" + DoubleToString(adx[0], 0) + " ADX)";
   else
      g_lastRegime = "Transition";

   Print("🧠 [CONFLUENCE]: ", result.direction, " | Score: ", DoubleToString(result.score, 3),
         " | Confidence: ", DoubleToString(result.confidence * 100, 1), "%",
         " | ATR: ", DoubleToString(atrVal, (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS)));
   Print("   📊 ", result.reasoning);
   Print("   📊 Indicators: ", indicatorsOk, "/8 | Buy: ", g_buyIndicators,
         " | Sell: ", g_sellIndicators, " | Neutral: ", g_neutralIndicators);
   if(result.direction != "HOLD")
   {
      Print("   💰 SL: ", DoubleToString(result.suggestedSL, digits),
            " | TP1: ", DoubleToString(result.suggestedTP1, digits),
            " | TP2: ", DoubleToString(result.suggestedTP2, digits),
            " | TP3: ", DoubleToString(result.suggestedTP3, digits));
   }

   return result;
}

//+------------------------------------------------------------------+
//| ★ MULTI-TIMEFRAME CONFLUENCE ENGINE ★                             |
//| Analyzes M5/M15/H1/H4/D1 for agreement/conflict                 |
//+------------------------------------------------------------------+
MTFAnalysis AnalyzeMultiTimeframe()
{
   MTFAnalysis mtf;
   ZeroMemory(mtf);

   string labels[5] = {"M5", "M15", "H1", "H4", "D1"};

   mtf.bullishCount = 0;
   mtf.bearishCount = 0;
   mtf.neutralCount = 0;

   for(int i = 0; i < 5; i++)
   {
      mtf.slots[i].tf = g_mtfPeriods[i];
      mtf.slots[i].label = labels[i];
      mtf.slots[i].isValid = false;
      mtf.slots[i].direction = "NEUTRAL";
      mtf.slots[i].confidence = 0.0;
      mtf.slots[i].emaVote = 0;
      mtf.slots[i].rsiValue = 50.0;
      mtf.slots[i].macdVote = 0;

      // Read EMA cross for this TF
      double e9[], e21[];
      ArraySetAsSeries(e9, true);
      ArraySetAsSeries(e21, true);
      bool emaOk = (g_hMTF_Ema9[i] != INVALID_HANDLE && g_hMTF_Ema21[i] != INVALID_HANDLE &&
                    CopyBuffer(g_hMTF_Ema9[i], 0, 0, 1, e9) >= 1 &&
                    CopyBuffer(g_hMTF_Ema21[i], 0, 0, 1, e21) >= 1);
      if(emaOk)
      {
         mtf.slots[i].emaVote = (e9[0] > e21[0]) ? 1 : -1;
      }

      // Read RSI for this TF
      double r14[];
      ArraySetAsSeries(r14, true);
      bool rsiOk = (g_hMTF_Rsi14[i] != INVALID_HANDLE && CopyBuffer(g_hMTF_Rsi14[i], 0, 0, 1, r14) >= 1);
      if(rsiOk)
      {
         mtf.slots[i].rsiValue = r14[0];
      }

      // Read MACD for this TF
      double mMain[], mSig[];
      ArraySetAsSeries(mMain, true);
      ArraySetAsSeries(mSig, true);
      bool macdOk = (g_hMTF_Macd[i] != INVALID_HANDLE &&
                     CopyBuffer(g_hMTF_Macd[i], 0, 0, 1, mMain) >= 1 &&
                     CopyBuffer(g_hMTF_Macd[i], 1, 0, 1, mSig) >= 1);
      if(macdOk)
      {
         mtf.slots[i].macdVote = (mMain[0] > mSig[0]) ? 1 : -1;
      }

      // Determine TF direction: majority of 3 indicators (EMA, RSI>50, MACD)
      int bullVotes = 0, bearVotes = 0;
      bullVotes += (mtf.slots[i].emaVote > 0) ? 1 : 0;
      bearVotes += (mtf.slots[i].emaVote < 0) ? 1 : 0;
      bullVotes += (mtf.slots[i].rsiValue > 55.0) ? 1 : 0;
      bearVotes += (mtf.slots[i].rsiValue < 45.0) ? 1 : 0;
      bullVotes += (mtf.slots[i].macdVote > 0) ? 1 : 0;
      bearVotes += (mtf.slots[i].macdVote < 0) ? 1 : 0;

      if(bullVotes >= 2)
      {
         mtf.slots[i].direction = "BUY";
         mtf.slots[i].confidence = (double)bullVotes / 3.0;
         mtf.bullishCount++;
      }
      else if(bearVotes >= 2)
      {
         mtf.slots[i].direction = "SELL";
         mtf.slots[i].confidence = (double)bearVotes / 3.0;
         mtf.bearishCount++;
      }
      else
      {
         mtf.slots[i].direction = "NEUTRAL";
         mtf.slots[i].confidence = 0.33;
         mtf.neutralCount++;
      }

      mtf.slots[i].isValid = (emaOk || rsiOk || macdOk);
   }

   // Count how many agree with primary signal
   mtf.agreementCount = 0;
   for(int i = 0; i < 5; i++)
   {
      if(mtf.slots[i].direction == g_lastAnalysis.direction)
         mtf.agreementCount++;
   }

   // Consensus label
   if(mtf.agreementCount >= 4) mtf.consensus = "STRONGLY ALIGNED";
   else if(mtf.agreementCount >= 3) mtf.consensus = "MOSTLY ALIGNED";
   else if(mtf.agreementCount >= 2) mtf.consensus = "MIXED";
   else mtf.consensus = "CONFLICTING";

   return mtf;
}

//+------------------------------------------------------------------+
//| MODEL CONSENSUS BREAKDOWN                                          |
//| Groups 8 indicators into 5 categories for audit-trail display     |
//+------------------------------------------------------------------+
void ComputeModelConsensus(ConfluenceAnalysis &analysis)
{
   ZeroMemory(g_modelConsensus);

   // Category 0: Trend (EMA + H4 Trend)
   g_modelConsensus.categories[0].name = "Trend";
   g_modelConsensus.categories[0].totalModels = 2;
   g_modelConsensus.categories[0].buyVotes = 0;
   g_modelConsensus.categories[0].sellVotes = 0;
   g_modelConsensus.categories[0].neutralVotes = 0;
   if(analysis.emaVote > 0) g_modelConsensus.categories[0].buyVotes++;
   else if(analysis.emaVote < 0) g_modelConsensus.categories[0].sellVotes++;
   else g_modelConsensus.categories[0].neutralVotes++;
   if(analysis.h4TrendVote > 0) g_modelConsensus.categories[0].buyVotes++;
   else if(analysis.h4TrendVote < 0) g_modelConsensus.categories[0].sellVotes++;
   else g_modelConsensus.categories[0].neutralVotes++;

   // Category 1: Momentum (RSI + MACD + Stochastic)
   g_modelConsensus.categories[1].name = "Momentum";
   g_modelConsensus.categories[1].totalModels = 3;
   g_modelConsensus.categories[1].buyVotes = 0;
   g_modelConsensus.categories[1].sellVotes = 0;
   g_modelConsensus.categories[1].neutralVotes = 0;
   if(analysis.rsiVote > 0) g_modelConsensus.categories[1].buyVotes++;
   else if(analysis.rsiVote < 0) g_modelConsensus.categories[1].sellVotes++;
   else g_modelConsensus.categories[1].neutralVotes++;
   if(analysis.macdVote > 0) g_modelConsensus.categories[1].buyVotes++;
   else if(analysis.macdVote < 0) g_modelConsensus.categories[1].sellVotes++;
   else g_modelConsensus.categories[1].neutralVotes++;
   if(analysis.stochVote > 0) g_modelConsensus.categories[1].buyVotes++;
   else if(analysis.stochVote < 0) g_modelConsensus.categories[1].sellVotes++;
   else g_modelConsensus.categories[1].neutralVotes++;

   // Category 2: Volatility (Bollinger Bands)
   g_modelConsensus.categories[2].name = "Volatility";
   g_modelConsensus.categories[2].totalModels = 1;
   g_modelConsensus.categories[2].buyVotes = 0;
   g_modelConsensus.categories[2].sellVotes = 0;
   g_modelConsensus.categories[2].neutralVotes = 0;
   if(analysis.bbVote > 0) g_modelConsensus.categories[2].buyVotes++;
   else if(analysis.bbVote < 0) g_modelConsensus.categories[2].sellVotes++;
   else g_modelConsensus.categories[2].neutralVotes++;

   // Category 3: Volume
   g_modelConsensus.categories[3].name = "Volume";
   g_modelConsensus.categories[3].totalModels = 1;
   g_modelConsensus.categories[3].buyVotes = 0;
   g_modelConsensus.categories[3].sellVotes = 0;
   g_modelConsensus.categories[3].neutralVotes = 0;
   if(analysis.volumeVote > 0) g_modelConsensus.categories[3].buyVotes++;
   else if(analysis.volumeVote < 0) g_modelConsensus.categories[3].sellVotes++;
   else g_modelConsensus.categories[3].neutralVotes++;

   // Category 4: Structure (ADX)
   g_modelConsensus.categories[4].name = "Structure";
   g_modelConsensus.categories[4].totalModels = 1;
   g_modelConsensus.categories[4].buyVotes = 0;
   g_modelConsensus.categories[4].sellVotes = 0;
   g_modelConsensus.categories[4].neutralVotes = 0;
   if(analysis.adxVote > 0) g_modelConsensus.categories[4].buyVotes++;
   else if(analysis.adxVote < 0) g_modelConsensus.categories[4].sellVotes++;
   else g_modelConsensus.categories[4].neutralVotes++;

   // Compute verdicts and percentages
   g_modelConsensus.totalModels = 8;
   g_modelConsensus.totalAgreeing = 0;

   for(int c = 0; c < 5; c++)
   {
      int maxV = MathMax(g_modelConsensus.categories[c].buyVotes,
                         MathMax(g_modelConsensus.categories[c].sellVotes,
                                 g_modelConsensus.categories[c].neutralVotes));

      if(g_modelConsensus.categories[c].buyVotes >= g_modelConsensus.categories[c].sellVotes &&
         g_modelConsensus.categories[c].buyVotes > 0)
      {
         g_modelConsensus.categories[c].verdict = "BUY";
         g_modelConsensus.categories[c].agreementPct = (double)g_modelConsensus.categories[c].buyVotes /
                                                       (double)g_modelConsensus.categories[c].totalModels * 100.0;
      }
      else if(g_modelConsensus.categories[c].sellVotes > 0)
      {
         g_modelConsensus.categories[c].verdict = "SELL";
         g_modelConsensus.categories[c].agreementPct = (double)g_modelConsensus.categories[c].sellVotes /
                                                       (double)g_modelConsensus.categories[c].totalModels * 100.0;
      }
      else
      {
         g_modelConsensus.categories[c].verdict = "NEUTRAL";
         g_modelConsensus.categories[c].agreementPct = 0.0;
      }

      // Count models that agree with the primary direction
      if(analysis.direction == "BUY")
         g_modelConsensus.totalAgreeing += g_modelConsensus.categories[c].buyVotes;
      else if(analysis.direction == "SELL")
         g_modelConsensus.totalAgreeing += g_modelConsensus.categories[c].sellVotes;
   }

   g_modelConsensus.overallConsensusPct = (g_modelConsensus.totalModels > 0) ?
      (double)g_modelConsensus.totalAgreeing / (double)g_modelConsensus.totalModels * 100.0 : 0.0;
}

//+------------------------------------------------------------------+
//| LIQUIDITY / STOP-CLUSTER HEATMAP                                   |
//| Identifies swing highs/lows, round numbers, stop cluster zones    |
//+------------------------------------------------------------------+
void ComputeLiquidityZones()
{
   g_liquidityZoneCount = 0;
   int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);
   double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);

   // Get ATR for zone width
   double atrBuf[];
   ArraySetAsSeries(atrBuf, true);
   double atrVal = point * 200;
   if(g_hAtr14 != INVALID_HANDLE && CopyBuffer(g_hAtr14, 0, 0, 1, atrBuf) >= 1)
      atrVal = atrBuf[0];

   double zoneWidth = atrVal * 0.3; // Zone half-width

   // Scan last 100 bars for swing highs and lows
   double highs[], lows[];
   ArraySetAsSeries(highs, true);
   ArraySetAsSeries(lows, true);
   int barsNeeded = 100;
   if(CopyHigh(Symbol(), Period(), 0, barsNeeded, highs) < barsNeeded) return;
   if(CopyLow(Symbol(), Period(), 0, barsNeeded, lows) < barsNeeded) return;

   // Temporary array to collect raw levels
   double rawLevels[200];
   string rawTypes[200];
   int rawCount = 0;

   // Find swing highs (bar higher than 2 bars on each side)
   for(int i = 3; i < barsNeeded - 3 && rawCount < 190; i++)
   {
      // Swing High
      if(highs[i] > highs[i-1] && highs[i] > highs[i-2] &&
         highs[i] > highs[i+1] && highs[i] > highs[i+2])
      {
         rawLevels[rawCount] = highs[i];
         rawTypes[rawCount] = "SWING_HI";
         rawCount++;
      }
      // Swing Low
      if(lows[i] < lows[i-1] && lows[i] < lows[i-2] &&
         lows[i] < lows[i+1] && lows[i] < lows[i+2])
      {
         rawLevels[rawCount] = lows[i];
         rawTypes[rawCount] = "SWING_LO";
         rawCount++;
      }
   }

   // Add round number levels near current price
   double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
   double roundStep = 0;

   // Determine round number step based on price magnitude
   if(currentPrice > 1000)       roundStep = 100;       // Indices
   else if(currentPrice > 100)   roundStep = 10;
   else if(currentPrice > 10)    roundStep = 1.0;
   else if(currentPrice > 1)     roundStep = 0.1;       // Forex majors
   else                          roundStep = 0.01;

   double baseRound = MathFloor(currentPrice / roundStep) * roundStep;
   for(int r = -3; r <= 3 && rawCount < 195; r++)
   {
      double level = baseRound + r * roundStep;
      if(MathAbs(level - currentPrice) < atrVal * 5.0) // Within 5 ATR
      {
         rawLevels[rawCount] = level;
         rawTypes[rawCount] = "ROUND";
         rawCount++;
      }
   }

   // Cluster nearby levels into zones
   bool used[200];
   ArrayInitialize(used, false);

   for(int i = 0; i < rawCount && g_liquidityZoneCount < 25; i++)
   {
      if(used[i]) continue;

      double zLevel = rawLevels[i];
      int strength = 1;
      string zType = rawTypes[i];

      // Check for nearby levels to cluster
      for(int j = i + 1; j < rawCount; j++)
      {
         if(!used[j] && MathAbs(rawLevels[j] - zLevel) < zoneWidth)
         {
            strength++;
            used[j] = true;
            // Upgrade type if round number + swing
            if(rawTypes[j] == "ROUND" && zType != "ROUND") zType = "STOP_CLUSTER";
            else if(rawTypes[j] != "ROUND" && zType == "ROUND") zType = "STOP_CLUSTER";
         }
      }
      used[i] = true;

      if(strength > 0 && g_liquidityZoneCount < 25)
      {
         // Cap strength at 5
         if(strength > 5) strength = 5;

         g_liquidityZones[g_liquidityZoneCount].priceLevel = zLevel;
         g_liquidityZones[g_liquidityZoneCount].zoneTop = zLevel + zoneWidth;
         g_liquidityZones[g_liquidityZoneCount].zoneBtm = zLevel - zoneWidth;
         g_liquidityZones[g_liquidityZoneCount].strength = strength;
         g_liquidityZones[g_liquidityZoneCount].zoneType = zType;

         // Color by type and strength
         if(zType == "STOP_CLUSTER")
            g_liquidityZones[g_liquidityZoneCount].zoneColor = C'200,100,255'; // Purple
         else if(zType == "ROUND")
            g_liquidityZones[g_liquidityZoneCount].zoneColor = C'0,180,220';   // Cyan
         else if(zType == "SWING_HI")
            g_liquidityZones[g_liquidityZoneCount].zoneColor = C'255,140,0';   // Amber
         else
            g_liquidityZones[g_liquidityZoneCount].zoneColor = C'0,200,100';   // Green

         g_liquidityZoneCount++;
      }
   }
}

//+------------------------------------------------------------------+
//| Draw Liquidity & Institutional Key Levels on Chart                |
//+------------------------------------------------------------------+
void DrawLiquidityHeatmap()
{
   CleanLiquidityObjects();
   if(LiquidityStyle == LIQ_STYLE_OFF) return;

   double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
   int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);

   // Find closest 2 resistances above current price
   int rIdx1 = -1, rIdx2 = -1;
   double rDist1 = 999999999, rDist2 = 999999999;

   // Find closest 2 supports below current price
   int sIdx1 = -1, sIdx2 = -1;
   double sDist1 = 999999999, sDist2 = 999999999;

   for(int i = 0; i < g_liquidityZoneCount; i++)
   {
      double lvl = g_liquidityZones[i].priceLevel;
      if(lvl > currentPrice)
      {
         double dist = lvl - currentPrice;
         if(dist < rDist1)
         {
            rDist2 = rDist1; rIdx2 = rIdx1;
            rDist1 = dist;   rIdx1 = i;
         }
         else if(dist < rDist2)
         {
            rDist2 = dist;   rIdx2 = i;
         }
      }
      else if(lvl < currentPrice)
      {
         double dist = currentPrice - lvl;
         if(dist < sDist1)
         {
            sDist2 = sDist1; sIdx2 = sIdx1;
            sDist1 = dist;   sIdx1 = i;
         }
         else if(dist < sDist2)
         {
            sDist2 = dist;   sIdx2 = i;
         }
      }
   }

   int keyIndices[4];
   string keyTags[4];
   color keyColors[4];
   int keyCount = 0;

   if(rIdx1 >= 0) { keyIndices[keyCount] = rIdx1; keyTags[keyCount] = "R1 KEY SUPPLY / RESISTANCE"; keyColors[keyCount] = C'255,80,100'; keyCount++; }
   if(rIdx2 >= 0) { keyIndices[keyCount] = rIdx2; keyTags[keyCount] = "R2 MAJOR STOP POOL";       keyColors[keyCount] = C'255,140,40'; keyCount++; }
   if(sIdx1 >= 0) { keyIndices[keyCount] = sIdx1; keyTags[keyCount] = "S1 KEY DEMAND / SUPPORT";   keyColors[keyCount] = C'0,229,140';  keyCount++; }
   if(sIdx2 >= 0) { keyIndices[keyCount] = sIdx2; keyTags[keyCount] = "S2 MAJOR LIQUIDITY POOL";   keyColors[keyCount] = C'0,180,240';  keyCount++; }

   datetime t1 = iTime(Symbol(), Period(), 25);
   datetime t2 = iTime(Symbol(), Period(), 0) + PeriodSeconds() * 14;

   for(int k = 0; k < keyCount; k++)
   {
      int idx = keyIndices[k];
      double level = g_liquidityZones[idx].priceLevel;

      if(LiquidityStyle == LIQ_STYLE_CLEAN_LEVELS)
      {
         // Clean institutional horizontal dashed ray
         string lineName = g_hudPrefix + "LIQ_LINE_" + IntegerToString(k);
         ObjectCreate(0, lineName, OBJ_TREND, 0, t1, level, t2, level);
         ObjectSetInteger(0, lineName, OBJPROP_COLOR, keyColors[k]);
         ObjectSetInteger(0, lineName, OBJPROP_STYLE, STYLE_DASH);
         ObjectSetInteger(0, lineName, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT, false);
         ObjectSetInteger(0, lineName, OBJPROP_BACK, true);
         ObjectSetInteger(0, lineName, OBJPROP_SELECTABLE, false);

         // Sleek right-aligned price badge text
         string txtName = g_hudPrefix + "LIQ_TXT_" + IntegerToString(k);
         ObjectCreate(0, txtName, OBJ_TEXT, 0, t2, level);
         string badge = "  " + keyTags[k] + " [" + DoubleToString(level, digits) + "]";
         ObjectSetString(0, txtName, OBJPROP_TEXT, badge);
         ObjectSetString(0, txtName, OBJPROP_FONT, "Segoe UI Bold");
         ObjectSetInteger(0, txtName, OBJPROP_FONTSIZE, 7);
         ObjectSetInteger(0, txtName, OBJPROP_COLOR, keyColors[k]);
         ObjectSetInteger(0, txtName, OBJPROP_ANCHOR, ANCHOR_LEFT);
         ObjectSetInteger(0, txtName, OBJPROP_BACK, false);
         ObjectSetInteger(0, txtName, OBJPROP_SELECTABLE, false);
      }
      else if(LiquidityStyle == LIQ_STYLE_SUBTLE_ZONES)
      {
         // Sleek hollow outline zone (NO solid opaque fill covering candles!)
         string objName = g_hudPrefix + "LIQ_ZONE_" + IntegerToString(k);
         ObjectCreate(0, objName, OBJ_RECTANGLE, 0, t1, g_liquidityZones[idx].zoneTop, t2, g_liquidityZones[idx].zoneBtm);
         ObjectSetInteger(0, objName, OBJPROP_COLOR, keyColors[k]);
         ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_DOT);
         ObjectSetInteger(0, objName, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, objName, OBJPROP_FILL, false); // NO SOLID FILL
         ObjectSetInteger(0, objName, OBJPROP_BACK, true);
         ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
         ObjectSetString(0, objName, OBJPROP_TOOLTIP, keyTags[k] + " @ " + DoubleToString(level, digits));
      }
   }
}

void CleanLiquidityObjects()
{
   ObjectsDeleteAll(0, g_hudPrefix + "LIQ_");
}

//+------------------------------------------------------------------+
//| NEWS-PROXIMITY FLAG                                                |
//| Fetches ForexFactory calendar and warns before high-impact events |
//+------------------------------------------------------------------+
void CheckNewsProximity()
{
   // Cache news data for 15 minutes
   if(TimeCurrent() - g_lastNewsFetchTime < 900 && g_lastNewsFetchTime > 0)
   {
      // Just update minutesUntil for existing events
      UpdateNewsProximity();
      return;
   }

   g_newsProximityActive = false;
   g_newsConfidencePenalty = 0.0;
   g_newsWarningText = "";
   g_upcomingNewsCount = 0;

   // Try to fetch from ForexFactory's free API
   string url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
   string headers = "Content-Type: application/json\r\n";
   char post_data[], result[];
   string result_headers;

   ResetLastError();
   int res = WebRequest("GET", url, headers, NULL, 5000, post_data, 0, result, result_headers);

   if(res == 200 && ArraySize(result) > 0)
   {
      string response = CharArrayToString(result);
      g_lastNewsFetchTime = TimeCurrent();

      // Parse events — extract relevant currency events
      string baseCurrency = StringSubstr(Symbol(), 0, 3);
      string quoteCurrency = "";
      if(StringLen(Symbol()) >= 6) quoteCurrency = StringSubstr(Symbol(), 3, 3);

      // Simple JSON array parsing for relevant high-impact events
      int pos = 0;
      while(pos >= 0 && g_upcomingNewsCount < 10)
      {
         pos = StringFind(response, "\"impact\":\"High\"", pos);
         if(pos < 0) break;

         // Find the containing object boundaries
         int objStart = pos;
         while(objStart > 0 && StringGetCharacter(response, objStart) != '{') objStart--;

         int objEnd = StringFind(response, "}", pos);
         if(objEnd < 0) { pos++; continue; }

         string eventObj = StringSubstr(response, objStart, objEnd - objStart + 1);

         // Extract country/currency
         string evCurrency = ExtractJsonStringConst(eventObj, "country");
         StringToUpper(evCurrency);

         // Only events for our symbol's currencies
         if(evCurrency == baseCurrency || evCurrency == quoteCurrency)
         {
            // Extract title
            string evTitle = ExtractJsonStringConst(eventObj, "title");
            if(StringLen(evTitle) > 30)
               evTitle = StringSubstr(evTitle, 0, 27) + "...";

            // Extract date
            string evDateStr = ExtractJsonStringConst(eventObj, "date");

            // Parse date (format: "2026-09-04T12:30:00-04:00")
            datetime evTime = ParseNewsDate(evDateStr);

            if(evTime > 0)
            {
               int minsUntil = (int)((evTime - TimeGMT()) / 60);

               // Only care about events within next 120 minutes or last 15 minutes
               if(minsUntil > -15 && minsUntil < 120)
               {
                  g_upcomingNews[g_upcomingNewsCount].eventTime = evTime;
                  g_upcomingNews[g_upcomingNewsCount].currency = evCurrency;
                  g_upcomingNews[g_upcomingNewsCount].impact = "HIGH";
                  g_upcomingNews[g_upcomingNewsCount].title = evTitle;
                  g_upcomingNews[g_upcomingNewsCount].minutesUntil = minsUntil;
                  g_upcomingNewsCount++;
               }
            }
         }
         pos = objEnd + 1;
      }
   }
   else
   {
      // Fallback: use time-based heuristics for known events
      // NFP: First Friday of month at 12:30 GMT
      // FOMC: Check if we're near typical FOMC time (18:00 GMT on Wednesdays)
      g_lastNewsFetchTime = TimeCurrent(); // Don't retry too soon
      Print("📰 [NEWS]: Could not fetch calendar (WebRequest code: ", res, "). Add URL to MT5 whitelist.");
   }

   UpdateNewsProximity();
}

void UpdateNewsProximity()
{
   g_newsProximityActive = false;
   g_newsConfidencePenalty = 0.0;
   g_newsWarningText = "";

   for(int i = 0; i < g_upcomingNewsCount; i++)
   {
      int minsUntil = (int)((g_upcomingNews[i].eventTime - TimeGMT()) / 60);
      g_upcomingNews[i].minutesUntil = minsUntil;

      if(minsUntil > -15 && minsUntil < 60)
      {
         g_newsProximityActive = true;

         // Closer = bigger penalty
         if(minsUntil < 5)       g_newsConfidencePenalty = MathMax(g_newsConfidencePenalty, 0.40);
         else if(minsUntil < 15) g_newsConfidencePenalty = MathMax(g_newsConfidencePenalty, 0.30);
         else if(minsUntil < 30) g_newsConfidencePenalty = MathMax(g_newsConfidencePenalty, 0.20);
         else                    g_newsConfidencePenalty = MathMax(g_newsConfidencePenalty, 0.10);

         if(StringLen(g_newsWarningText) == 0)
         {
            if(minsUntil < 0)
               g_newsWarningText = g_upcomingNews[i].currency + " " + g_upcomingNews[i].title + " (JUST RELEASED)";
            else
               g_newsWarningText = g_upcomingNews[i].currency + " " + g_upcomingNews[i].title + " in " + IntegerToString(minsUntil) + "min";
         }
      }
   }
}

datetime ParseNewsDate(string dateStr)
{
   // Format: "2026-09-04T12:30:00-04:00"
   if(StringLen(dateStr) < 19) return 0;

   string datePart = StringSubstr(dateStr, 0, 10); // "2026-09-04"
   string timePart = StringSubstr(dateStr, 11, 8); // "12:30:00"

   datetime dt = StringToTime(datePart + " " + timePart);

   // Adjust for timezone offset if present
   if(StringLen(dateStr) >= 25)
   {
      string tzSign = StringSubstr(dateStr, 19, 1);
      string tzHourStr = StringSubstr(dateStr, 20, 2);
      int tzOffset = (int)StringToInteger(tzHourStr) * 3600;
      if(tzSign == "-") dt += tzOffset; // Convert to GMT
      else dt -= tzOffset;
   }

   return dt;
}

//+------------------------------------------------------------------+
//| HISTORICAL PATTERN MATCHING                                        |
//| Finds similar price patterns in history using Pearson correlation |
//+------------------------------------------------------------------+
PatternMatch FindHistoricalPatterns()
{
   PatternMatch pm;
   ZeroMemory(pm);
   pm.totalMatches = 0;
   pm.continuationPct = 0.0;
   pm.reversalPct = 0.0;
   pm.summary = "Scanning...";

   int patternLen = 10;  // Compare 10-bar patterns
   int outcomeLen = 5;   // Look at next 5 bars for outcome
   int totalBarsNeeded = PatternLookbackBars + outcomeLen;

   double closes[];
   ArraySetAsSeries(closes, true);
   if(CopyClose(Symbol(), Period(), 0, totalBarsNeeded, closes) < totalBarsNeeded)
   {
      pm.summary = "Insufficient history";
      return pm;
   }

   // Get current ATR for normalization
   double atrBuf[];
   ArraySetAsSeries(atrBuf, true);
   double atrVal = 1.0;
   if(g_hAtr14 != INVALID_HANDLE && CopyBuffer(g_hAtr14, 0, 0, 1, atrBuf) >= 1)
      atrVal = atrBuf[0];
   if(atrVal <= 0) atrVal = 1.0;

   // Build current pattern: normalized close-to-close deltas
   double currentPattern[10];
   for(int i = 0; i < patternLen; i++)
   {
      currentPattern[i] = (closes[i] - closes[i + 1]) / atrVal;
   }

   // Scan history for similar patterns
   int matches = 0;
   int continuations = 0;
   int reversals = 0;
   double totalCorrelation = 0.0;

   for(int start = patternLen + outcomeLen; start < PatternLookbackBars - patternLen; start++)
   {
      // Build historical pattern
      double histPattern[10];
      for(int i = 0; i < patternLen; i++)
      {
         histPattern[i] = (closes[start + i] - closes[start + i + 1]) / atrVal;
      }

      // Compute Pearson correlation
      double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
      for(int i = 0; i < patternLen; i++)
      {
         sumX += currentPattern[i];
         sumY += histPattern[i];
         sumXY += currentPattern[i] * histPattern[i];
         sumX2 += currentPattern[i] * currentPattern[i];
         sumY2 += histPattern[i] * histPattern[i];
      }

      double n = (double)patternLen;
      double denom = MathSqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

      if(denom > 0.0001)
      {
         double corr = (n * sumXY - sumX * sumY) / denom;

         if(corr > 0.75) // Strong match
         {
            matches++;
            totalCorrelation += corr;

            // Check outcome: what happened in the 5 bars after this pattern?
            // Note: indices are reversed (series), so "after" means lower index
            int outcomeStart = start - outcomeLen;
            if(outcomeStart >= 0)
            {
               double outcomeMove = closes[outcomeStart] - closes[start];

               // Did it continue in the current signal's direction?
               if(g_lastAnalysis.direction == "BUY" && outcomeMove > 0)
                  continuations++;
               else if(g_lastAnalysis.direction == "SELL" && outcomeMove < 0)
                  continuations++;
               else if(g_lastAnalysis.direction != "HOLD")
                  reversals++;
            }
         }
      }
   }

   pm.totalMatches = matches;
   if(matches > 0)
   {
      pm.continuationPct = (double)continuations / (double)matches * 100.0;
      pm.reversalPct = (double)reversals / (double)matches * 100.0;
      pm.avgMatchCorrelation = totalCorrelation / matches;
      pm.summary = IntegerToString(matches) + " matches: " +
                   DoubleToString(pm.continuationPct, 0) + "% continued, " +
                   DoubleToString(pm.reversalPct, 0) + "% reversed";
   }
   else
   {
      pm.summary = "No strong matches found";
   }

   return pm;
}

//+------------------------------------------------------------------+
//| RISK-ADJUSTED LOT SIZE CALCULATOR                                  |
//| Calculates lot from account risk %, ATR-based SL distance        |
//+------------------------------------------------------------------+
double CalculateRiskLot(string direction)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(balance <= 0) return LotSize;

   double riskAmount = balance * (RiskPercentPerTrade / 100.0) * g_recoveryMult * ClientRiskMultiplier;

   // SL distance in price
   double atrVal = g_lastAnalysis.atrValue;
   if(atrVal <= 0)
   {
      double atrBuf[];
      ArraySetAsSeries(atrBuf, true);
      if(g_hAtr14 != INVALID_HANDLE && CopyBuffer(g_hAtr14, 0, 0, 1, atrBuf) >= 1)
         atrVal = atrBuf[0];
   }
   double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
   if(atrVal <= 0) atrVal = point * 300;

   double slDistPrice = atrVal * SL_ATR_Mult;

   // Convert SL distance to pips/points value
   double tickValue = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_SIZE);

   if(tickValue <= 0 || tickSize <= 0) return LotSize;

   // Value per lot for the SL distance
   double slValuePerLot = (slDistPrice / tickSize) * tickValue;

   if(slValuePerLot <= 0) return LotSize;

   double calculatedLot = riskAmount / slValuePerLot;

   // Normalize to broker requirements
   double minLot  = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
   if(minLot <= 0) minLot = 0.01;
   if(stepLot <= 0) stepLot = 0.01;

   if(calculatedLot < minLot) calculatedLot = minLot;

   // Cap at user's LotSize setting
   if(calculatedLot > LotSize) calculatedLot = LotSize;
   if(maxLot > 0 && calculatedLot > maxLot) calculatedLot = maxLot;

   double normalizedLot = MathFloor((calculatedLot - minLot) / stepLot) * stepLot + minLot;
   int lotDigits = (stepLot < 0.1) ? 2 : ((stepLot < 1.0) ? 1 : 0);
   normalizedLot = NormalizeDouble(normalizedLot, lotDigits);

   // Build display text
   g_suggestedLotText = DoubleToString(normalizedLot, lotDigits) + " lots (" +
                        DoubleToString(RiskPercentPerTrade, 1) + "% of $" +
                        DoubleToString(balance, 0) + ")";

   return normalizedLot;
}

//+------------------------------------------------------------------+
//| VOLATILITY FORECAST                                                |
//| Projects ATR expansion/contraction using slope + BB width trend   |
//+------------------------------------------------------------------+
VolatilityForecast ProjectVolatility()
{
   VolatilityForecast vf;
   ZeroMemory(vf);
   vf.forecast = "STABLE";
   vf.icon = "↔";

   // Get ATR history (last 20 bars)
   double atrHist[];
   ArraySetAsSeries(atrHist, true);
   if(g_hAtr14 == INVALID_HANDLE || CopyBuffer(g_hAtr14, 0, 0, 20, atrHist) < 20)
   {
      vf.forecast = "NO DATA";
      return vf;
   }

   vf.currentATR = atrHist[0];

   // Linear regression slope of ATR over last 14 bars
   double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
   int regLen = 14;
   for(int i = 0; i < regLen; i++)
   {
      double x = (double)i;
      double y = atrHist[i];
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumX2 += x * x;
   }
   double n = (double)regLen;
   double slope = 0;
   double denom = (n * sumX2 - sumX * sumX);
   if(MathAbs(denom) > 0.0000001)
      slope = (n * sumXY - sumX * sumY) / denom;

   vf.atrSlope = slope;

   // Project ATR 5 bars ahead
   vf.projectedATR = vf.currentATR + slope * 5.0;
   if(vf.projectedATR < 0) vf.projectedATR = vf.currentATR * 0.5;

   vf.atrChangePct = (vf.currentATR > 0) ?
      ((vf.projectedATR - vf.currentATR) / vf.currentATR * 100.0) : 0.0;

   // BB Width analysis
   double bbUp[], bbLow[];
   ArraySetAsSeries(bbUp, true);
   ArraySetAsSeries(bbLow, true);

   vf.bbWidthCurrent = 0;
   vf.bbWidthAvg = 0;

   if(g_hBB20 != INVALID_HANDLE &&
      CopyBuffer(g_hBB20, 1, 0, 15, bbUp) >= 15 &&
      CopyBuffer(g_hBB20, 2, 0, 15, bbLow) >= 15)
   {
      vf.bbWidthCurrent = bbUp[0] - bbLow[0];
      double bbWidthSum = 0;
      for(int i = 1; i < 15; i++)
         bbWidthSum += (bbUp[i] - bbLow[i]);
      vf.bbWidthAvg = bbWidthSum / 14.0;
   }

   // Determine forecast
   bool atrRising = (slope > 0);
   bool bbExpanding = (vf.bbWidthCurrent > vf.bbWidthAvg * 1.05);
   bool atrFalling = (slope < 0);
   bool bbContracting = (vf.bbWidthCurrent < vf.bbWidthAvg * 0.95);

   if(atrRising && bbExpanding)
   {
      vf.forecast = "EXPANDING";
      vf.icon = "↗";
   }
   else if(atrFalling && bbContracting)
   {
      vf.forecast = "CONTRACTING";
      vf.icon = "↘";
   }
   else if(atrRising)
   {
      vf.forecast = "EXPANDING";
      vf.icon = "↗";
   }
   else if(atrFalling)
   {
      vf.forecast = "CONTRACTING";
      vf.icon = "↘";
   }
   else
   {
      vf.forecast = "STABLE";
      vf.icon = "↔";
   }

   return vf;
}

//+------------------------------------------------------------------+
//| POST-SIGNAL OUTCOME TRACKER                                        |
//| Records signals and tracks predicted vs actual price action       |
//+------------------------------------------------------------------+
void RecordSignal(string direction, double entry, double confidence, double tp, double sl)
{
   // Don't record duplicates within 3 bars
   for(int i = 0; i < g_signalHistoryCount && i < 50; i++)
   {
      int idx = (g_signalHistoryHead - 1 - i + 50) % 50;
      if(g_signalHistory[idx].active &&
         g_signalHistory[idx].direction == direction &&
         TimeCurrent() - g_signalHistory[idx].signalTime < PeriodSeconds() * 3)
      {
         return; // Too recent, skip
      }
   }

   // Write to ring buffer
   g_signalHistory[g_signalHistoryHead].active = true;
   g_signalHistory[g_signalHistoryHead].signalTime = TimeCurrent();
   g_signalHistory[g_signalHistoryHead].direction = direction;
   g_signalHistory[g_signalHistoryHead].entryPrice = entry;
   g_signalHistory[g_signalHistoryHead].confidenceAtEntry = confidence;
   g_signalHistory[g_signalHistoryHead].predictedTP = tp;
   g_signalHistory[g_signalHistoryHead].predictedSL = sl;
   g_signalHistory[g_signalHistoryHead].currentPnLPips = 0;
   g_signalHistory[g_signalHistoryHead].maxFavorablePips = 0;
   g_signalHistory[g_signalHistoryHead].maxAdversePips = 0;
   g_signalHistory[g_signalHistoryHead].outcomeStatus = "TRACKING";
   g_signalHistory[g_signalHistoryHead].barsElapsed = 0;

   g_signalHistoryHead = (g_signalHistoryHead + 1) % 50;
   if(g_signalHistoryCount < 50) g_signalHistoryCount++;
}

void UpdateSignalOutcomes()
{
   double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
   double currentBid = SymbolInfoDouble(Symbol(), SYMBOL_BID);
   double pipDiv = (point > 0) ? point * 10.0 : 0.0001; // Convert to pips

   for(int i = 0; i < 50; i++)
   {
      if(!g_signalHistory[i].active) continue;
      if(g_signalHistory[i].outcomeStatus != "TRACKING") continue;

      double entry = g_signalHistory[i].entryPrice;
      double pnlPips = 0;

      if(g_signalHistory[i].direction == "BUY")
         pnlPips = (currentBid - entry) / pipDiv;
      else
         pnlPips = (entry - currentBid) / pipDiv;

      g_signalHistory[i].currentPnLPips = pnlPips;

      if(pnlPips > g_signalHistory[i].maxFavorablePips)
         g_signalHistory[i].maxFavorablePips = pnlPips;
      if(pnlPips < -g_signalHistory[i].maxAdversePips)
         g_signalHistory[i].maxAdversePips = MathAbs(pnlPips);

      // Check if TP or SL hit
      double tpDist = 0, slDist = 0;
      if(g_signalHistory[i].direction == "BUY")
      {
         tpDist = (g_signalHistory[i].predictedTP - entry) / pipDiv;
         slDist = (entry - g_signalHistory[i].predictedSL) / pipDiv;
      }
      else
      {
         tpDist = (entry - g_signalHistory[i].predictedTP) / pipDiv;
         slDist = (g_signalHistory[i].predictedSL - entry) / pipDiv;
      }

      if(pnlPips >= tpDist && tpDist > 0)
         g_signalHistory[i].outcomeStatus = "HIT_TP";
      else if(pnlPips <= -slDist && slDist > 0)
         g_signalHistory[i].outcomeStatus = "HIT_SL";

      // Count bars elapsed
      g_signalHistory[i].barsElapsed = Bars(Symbol(), Period(), g_signalHistory[i].signalTime, TimeCurrent());

      // Expire after 50 bars
      if(g_signalHistory[i].barsElapsed > 50 && g_signalHistory[i].outcomeStatus == "TRACKING")
         g_signalHistory[i].outcomeStatus = "EXPIRED";
   }
}

//+------------------------------------------------------------------+
//| Re-Entry Cooldown Guard                                           |
//+------------------------------------------------------------------+
bool CanReEnter()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == Symbol() && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
      {
         return false;
      }
   }

   HistorySelect(TimeCurrent() - 86400, TimeCurrent());
   datetime lastCloseTime = 0;
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket > 0 &&
         HistoryDealGetInteger(ticket, DEAL_MAGIC) == MagicNumber &&
         HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_OUT &&
         HistoryDealGetString(ticket, DEAL_SYMBOL) == Symbol())
      {
         lastCloseTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
         break;
      }
   }

   if(lastCloseTime == 0)
      return true;

   int barsSince = Bars(Symbol(), Period(), lastCloseTime, TimeCurrent());
   if(barsSince < ReEntryCooldownBars)
   {
      g_lastTradeMsg = "COOLDOWN: " + IntegerToString(ReEntryCooldownBars - barsSince) + " bars remaining";
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Request API Signal (Secondary — for cloud sync only)              |
//+------------------------------------------------------------------+
void RequestSwarmSignal()
{
   string url = KestrelAPIUrl + "/api/signals/generate";
   string headers = "Authorization: Bearer " + KestrelAPIToken + "\r\n"
                  + "Content-Type: application/json\r\n"
                  + "X-Adapter-Secret: " + AdapterSecret + "\r\n";

   string json = "{\"instrument\":\"" + GetInstrument() + "\","
                + "\"timeframe\":\"" + GetTimeframe() + "\"}";

   char post_data[], result[];
   StringToCharArray(json, post_data, 0, StringLen(json));
   string result_headers;

   ResetLastError();
   int res = WebRequest("POST", url, headers, NULL, 5000, post_data, ArraySize(post_data), result, result_headers);

   if(res == 200)
   {
      g_connectionStatus = "online";
      string response = CharArrayToString(result);
      string apiDir = ExtractJsonString(response, "direction");
      double apiConf = ExtractJsonDouble(response, "confidence");
      if(StringLen(apiDir) > 0)
      {
         Print("📡 [API SYNC]: Backend says ", apiDir, " (", DoubleToString(apiConf * 100, 1), "%)");
      }
   }
   else
   {
      g_connectionStatus = "local_only";
   }
}

//+------------------------------------------------------------------+
//| AUTONOMOUS TRADE EXECUTION with ATR-Based SL/TP                  |
//+------------------------------------------------------------------+
void ExecuteAutonomousTrade(string direction, double customLot = 0.0)
{
   StringToUpper(direction);
   if(direction != "BUY" && direction != "SELL") return;

   // 1. Check Terminal Algo Trading Permissions
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
   {
      Print("⚠️ [ALGO DISABLED]: Click 'Algo Trading' button in MT5 toolbar.");
      g_lastTradeMsg = "ENABLE 'ALGO TRADING' IN MT5 TOOLBAR";
      return;
   }
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
   {
      Print("⚠️ [EA DISABLED]: Press F7 → Check 'Allow Algo Trading'.");
      g_lastTradeMsg = "PRESS F7 → ENABLE 'ALLOW ALGO TRADING'";
      return;
   }

   // 2. Anti-stacking: only one position per symbol
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == Symbol() && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
      {
         g_lastTradeMsg = "POSITION ACTIVE ON " + Symbol();
         return;
      }
   }

   // 3. Validate Spread
   double spread = (double)SymbolInfoInteger(Symbol(), SYMBOL_SPREAD);
   if(MaxSpreadPoints > 0 && spread > MaxSpreadPoints)
   {
      Print("⚠️ Spread high (", spread, " > ", MaxSpreadPoints, "). Waiting for better spread.");
      g_lastTradeMsg = "SPREAD TOO HIGH (" + DoubleToString(spread, 0) + ")";
      return;
   }

   // 4. Determine lot size (risk-based or fixed)
   double baseLot = customLot;
   if(baseLot <= 0 || baseLot > LotSize) baseLot = LotSize;

   // If risk-based sizing is enabled and this is an auto-trade, use risk lot
   if(RiskPercentPerTrade > 0 && g_autoPilotActive && g_suggestedLot > 0)
      baseLot = g_suggestedLot;

   // 5. Broker Lot Size Normalization
   double minLot  = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
   if(minLot <= 0) minLot = 0.01;
   if(stepLot <= 0) stepLot = 0.01;

   double desiredLot = baseLot * g_recoveryMult * ClientRiskMultiplier;
   if(desiredLot < minLot) desiredLot = minLot;
   if(maxLot > 0 && desiredLot > maxLot) desiredLot = maxLot;

   double normalizedLots = MathFloor((desiredLot - minLot) / stepLot) * stepLot + minLot;
   int lotDigits = (stepLot < 0.1) ? 2 : ((stepLot < 1.0) ? 1 : 0);
   normalizedLots = NormalizeDouble(normalizedLots, lotDigits);

   // 6. Live Prices & ATR-Based SL/TP
   double ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
   double bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);
   double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);
   int stopLevel = (int)SymbolInfoInteger(Symbol(), SYMBOL_TRADE_STOPS_LEVEL);

   double atrVal = 0.0;
   if(g_lastAnalysis.isValid && g_lastAnalysis.atrValue > 0)
   {
      atrVal = g_lastAnalysis.atrValue;
   }
   else
   {
      double atrBuf[];
      ArraySetAsSeries(atrBuf, true);
      if(g_hAtr14 != INVALID_HANDLE && CopyBuffer(g_hAtr14, 0, 0, 1, atrBuf) >= 1)
         atrVal = atrBuf[0];
      if(atrVal <= 0) atrVal = point * 300;

      string sym = Symbol();
      if(EnableSpikeHunter && (StringFind(sym, "Boom") >= 0 || StringFind(sym, "Crash") >= 0))
         atrVal *= 1.8;
   }

   double slDist = atrVal * SL_ATR_Mult;
   double tpDist = atrVal * TP1_ATR_Mult;

   double minStopDist = (double)stopLevel * point * 1.5;
   if(slDist < minStopDist) slDist = minStopDist;
   if(tpDist < minStopDist) tpDist = minStopDist;

   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);

   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = Symbol();
   request.volume    = normalizedLots;
   request.deviation = SlippagePoints;
   request.magic     = MagicNumber;
   request.comment   = "Kestrel v5 Intelligence";

   double origSL = 0, origTP = 0;

   if(direction == "BUY")
   {
      request.type  = ORDER_TYPE_BUY;
      request.price = NormalizeDouble(ask, digits);
      request.sl    = NormalizeDouble(ask - slDist, digits);
      request.tp    = NormalizeDouble(ask + tpDist, digits);
   }
   else
   {
      request.type  = ORDER_TYPE_SELL;
      request.price = NormalizeDouble(bid, digits);
      request.sl    = NormalizeDouble(bid + slDist, digits);
      request.tp    = NormalizeDouble(bid - tpDist, digits);
   }

   origSL = request.sl;
   origTP = request.tp;

   // 7. Multi-Pass Filling Mode Execution
   ENUM_ORDER_TYPE_FILLING fillModes[3] = {ORDER_FILLING_IOC, ORDER_FILLING_FOK, ORDER_FILLING_RETURN};
   bool orderSuccess = false;

   for(int f = 0; f < 3 && !orderSuccess; f++)
   {
      request.type_filling = fillModes[f];
      ResetLastError();
      if(OrderSend(request, result))
      {
         orderSuccess = true;
         break;
      }
      else if(result.retcode == 10016)
      {
         request.sl = 0.0;
         request.tp = 0.0;
         if(OrderSend(request, result))
         {
            orderSuccess = true;
            Print("⚠️ [NOTE]: Opened without SL/TP (broker rejected stops). Will set via SLTP modify.");
            break;
         }
      }
   }

   if(orderSuccess)
   {
      g_totalTrades++;
      g_lastTradeMsg = direction + " #" + IntegerToString((long)result.deal) + " @ " + DoubleToString(request.price, digits);

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionGetSymbol(i) == Symbol() && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            g_activePositionTicket = PositionGetTicket(i);
            break;
         }
      }
      g_partialTP1Fired = false;
      g_partialTP2Fired = false;

      Print("✅ [TRADE EXECUTED]: ", direction, " ", normalizedLots, " lots @ ",
            DoubleToString(request.price, digits),
            " | SL: ", DoubleToString((origSL > 0 ? origSL : request.sl), digits),
            " | TP: ", DoubleToString((origTP > 0 ? origTP : request.tp), digits),
            " | Risk: ", DoubleToString(RiskPercentPerTrade, 1), "%");
      Print("   📊 Reason: ", g_lastAnalysis.reasoning);

      if(request.sl == 0.0 && origSL > 0)
      {
         Sleep(300);
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            if(PositionGetSymbol(i) == Symbol() && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            {
               ulong posTicket = PositionGetTicket(i);
               MqlTradeRequest modReq;
               MqlTradeResult modRes;
               ZeroMemory(modReq);
               ZeroMemory(modRes);
               modReq.action   = TRADE_ACTION_SLTP;
               modReq.position = posTicket;
               modReq.symbol   = Symbol();
               modReq.sl       = origSL;
               modReq.tp       = origTP;
               if(OrderSend(modReq, modRes))
                  Print("✅ [SLTP SET]: SL=", DoubleToString(origSL, digits), " TP=", DoubleToString(origTP, digits));
               else
                  Print("⚠️ [SLTP FAILED]: Could not set stops. Error: ", modRes.retcode);
               break;
            }
         }
      }

      if(DrawSignalArrows)
         Draw3DChartSignal(direction, request.price, origSL > 0 ? origSL : request.sl, origTP > 0 ? origTP : request.tp);

      ReportTradeToSupabase(direction, request.price, normalizedLots, origSL, origTP, result.deal);
      SyncAccountToSupabase();
   }
   else
   {
      g_lastTradeMsg = "ERR " + IntegerToString((long)result.retcode) + ": " + result.comment;
      Print("❌ [ORDER FAILED]: Error: ", GetLastError(), " Retcode: ", result.retcode, " Comment: ", result.comment);
   }
}

//+------------------------------------------------------------------+
//| Draw Star-Rated Signal Arrow on Chart                              |
//+------------------------------------------------------------------+
void Draw3DChartSignal(string direction, double entry, double sl, double tp)
{
   datetime candleTime = iTime(Symbol(), Period(), 0);
   string arrowName = g_hudPrefix + "SIG_" + IntegerToString((long)candleTime);
   string starLabel = g_hudPrefix + "STAR_" + IntegerToString((long)candleTime);

   string stars = GetStarRating(g_lastAnalysis.confidence);
   string mtfInfo = EnableMTFPanel ? (" | MTF: " + IntegerToString(g_mtfData.agreementCount) + "/5") : "";

   if(direction == "BUY")
   {
      ObjectCreate(0, arrowName, OBJ_ARROW_BUY, 0, candleTime, entry);
      ObjectSetInteger(0, arrowName, OBJPROP_COLOR, C'0,255,136');
      ObjectSetInteger(0, arrowName, OBJPROP_WIDTH, 4);
      ObjectSetString(0, arrowName, OBJPROP_TOOLTIP,
         "🦅 " + stars + " BUY @ " + DoubleToString(entry, 2) +
         " | Conf: " + DoubleToString(g_lastAnalysis.confidence * 100, 1) + "%" +
         mtfInfo + " | " + g_lastAnalysis.reasoning);
   }
   else
   {
      ObjectCreate(0, arrowName, OBJ_ARROW_SELL, 0, candleTime, entry);
      ObjectSetInteger(0, arrowName, OBJPROP_COLOR, C'255,34,85');
      ObjectSetInteger(0, arrowName, OBJPROP_WIDTH, 4);
      ObjectSetString(0, arrowName, OBJPROP_TOOLTIP,
         "🦅 " + stars + " SELL @ " + DoubleToString(entry, 2) +
         " | Conf: " + DoubleToString(g_lastAnalysis.confidence * 100, 1) + "%" +
         mtfInfo + " | " + g_lastAnalysis.reasoning);
   }

   // Draw star rating text above/below arrow
   double offset = g_lastAnalysis.atrValue * 0.5;
   double starPrice = (direction == "BUY") ? (entry - offset * 1.5) : (entry + offset * 1.5);

   ObjectCreate(0, starLabel, OBJ_TEXT, 0, candleTime, starPrice);
   ObjectSetString(0, starLabel, OBJPROP_TEXT, stars);
   ObjectSetString(0, starLabel, OBJPROP_FONT, "Segoe UI");
   ObjectSetInteger(0, starLabel, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, starLabel, OBJPROP_COLOR, (direction == "BUY") ? C'0,255,136' : C'255,34,85');
   ObjectSetInteger(0, starLabel, OBJPROP_ANCHOR, ANCHOR_CENTER);

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| Close All Open Positions for this Symbol                          |
//+------------------------------------------------------------------+
void CloseAllSymbolPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == Symbol())
      {
         ulong ticket = PositionGetTicket(i);
         ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         double volume = PositionGetDouble(POSITION_VOLUME);

         MqlTradeRequest req;
         MqlTradeResult res;
         ZeroMemory(req);
         ZeroMemory(res);

         req.action    = TRADE_ACTION_DEAL;
         req.position  = ticket;
         req.symbol    = Symbol();
         req.volume    = volume;
         req.deviation = SlippagePoints;

         uint filling = (uint)SymbolInfoInteger(Symbol(), SYMBOL_FILLING_MODE);
         if((filling & SYMBOL_FILLING_FOK) != 0) req.type_filling = ORDER_FILLING_FOK;
         else if((filling & SYMBOL_FILLING_IOC) != 0) req.type_filling = ORDER_FILLING_IOC;
         else req.type_filling = ORDER_FILLING_RETURN;

         if(type == POSITION_TYPE_BUY)
         {
            req.type  = ORDER_TYPE_SELL;
            req.price = SymbolInfoDouble(Symbol(), SYMBOL_BID);
         }
         else
         {
            req.type  = ORDER_TYPE_BUY;
            req.price = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
         }

         if(OrderSend(req, res))
            Print("🛡️ [CLOSED]: Position #", ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| 3-Level Smart Trailing Stop & Partial Take-Profit                 |
//+------------------------------------------------------------------+
void ManageTrailingStops()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == Symbol() && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
      {
         ulong ticket = PositionGetTicket(i);
         ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         double currentSl = PositionGetDouble(POSITION_SL);
         double currentTp = PositionGetDouble(POSITION_TP);
         double currentPrice = PositionGetDouble(POSITION_PRICE_CURRENT);
         double volume = PositionGetDouble(POSITION_VOLUME);
         double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
         int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);
         double minLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
         double stepLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
         if(minLot <= 0) minLot = 0.01;
         if(stepLot <= 0) stepLot = 0.01;
         int lotDigits = (stepLot < 0.1) ? 2 : ((stepLot < 1.0) ? 1 : 0);

         if(ticket != g_activePositionTicket)
         {
            g_activePositionTicket = ticket;
            g_partialTP1Fired = false;
            g_partialTP2Fired = false;
         }

         double atrVal = 0.0;
         double atrBuf[];
         ArraySetAsSeries(atrBuf, true);
         if(g_hAtr14 != INVALID_HANDLE && CopyBuffer(g_hAtr14, 0, 0, 1, atrBuf) >= 1)
            atrVal = atrBuf[0];
         if(atrVal <= 0) atrVal = point * 300;

         string sym = Symbol();
         if(EnableSpikeHunter && (StringFind(sym, "Boom") >= 0 || StringFind(sym, "Crash") >= 0))
            atrVal *= 1.8;

         double profitDist = (type == POSITION_TYPE_BUY) ? (currentPrice - openPrice) : (openPrice - currentPrice);

         // === LEVEL 1: Break-Even Lock at 1.5× ATR ===
         if(profitDist >= atrVal * 1.5)
         {
            double beLevel;
            if(type == POSITION_TYPE_BUY)
               beLevel = NormalizeDouble(openPrice + 20 * point, digits);
            else
               beLevel = NormalizeDouble(openPrice - 20 * point, digits);

            bool shouldLock = false;
            if(type == POSITION_TYPE_BUY)
               shouldLock = (currentSl < beLevel);
            else
               shouldLock = (currentSl == 0 || currentSl > beLevel);

            if(shouldLock)
            {
               MqlTradeRequest req;
               MqlTradeResult res;
               ZeroMemory(req);
               ZeroMemory(res);
               req.action   = TRADE_ACTION_SLTP;
               req.position = ticket;
               req.symbol   = Symbol();
               req.sl       = beLevel;
               req.tp       = currentTp;
               if(OrderSend(req, res))
                  Print("🛡️ [BREAK-EVEN]: Position #", ticket, " SL locked @ ", DoubleToString(beLevel, digits));
            }
         }

         // === LEVEL 2: Partial Close 40% at TP1 ATR ===
         if(!g_partialTP1Fired && profitDist >= atrVal * TP1_ATR_Mult && volume > minLot * 1.5)
         {
            double closeVol = NormalizeDouble(volume * 0.4, lotDigits);
            if(closeVol < minLot) closeVol = minLot;
            if(closeVol >= minLot && closeVol < volume)
            {
               MqlTradeRequest req;
               MqlTradeResult res;
               ZeroMemory(req);
               ZeroMemory(res);
               req.action    = TRADE_ACTION_DEAL;
               req.position  = ticket;
               req.symbol    = Symbol();
               req.volume    = closeVol;
               req.deviation = SlippagePoints;

               uint filling = (uint)SymbolInfoInteger(Symbol(), SYMBOL_FILLING_MODE);
               if((filling & SYMBOL_FILLING_FOK) != 0) req.type_filling = ORDER_FILLING_FOK;
               else if((filling & SYMBOL_FILLING_IOC) != 0) req.type_filling = ORDER_FILLING_IOC;
               else req.type_filling = ORDER_FILLING_RETURN;

               req.type = (type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
               req.price = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(Symbol(), SYMBOL_BID) : SymbolInfoDouble(Symbol(), SYMBOL_ASK);

               if(OrderSend(req, res))
               {
                  g_partialTP1Fired = true;
                  Print("💰 [TP1 HIT]: Closed 40% (", closeVol, " lots) on #", ticket, " at +", DoubleToString(TP1_ATR_Mult, 1), "× ATR");
               }
            }
         }

         // === LEVEL 3: Partial Close 50% of remaining at TP2 ATR ===
         if(g_partialTP1Fired && !g_partialTP2Fired && profitDist >= atrVal * TP2_ATR_Mult && volume > minLot * 1.5)
         {
            double closeVol = NormalizeDouble(volume * 0.5, lotDigits);
            if(closeVol < minLot) closeVol = minLot;
            if(closeVol >= minLot && closeVol < volume)
            {
               MqlTradeRequest req;
               MqlTradeResult res;
               ZeroMemory(req);
               ZeroMemory(res);
               req.action    = TRADE_ACTION_DEAL;
               req.position  = ticket;
               req.symbol    = Symbol();
               req.volume    = closeVol;
               req.deviation = SlippagePoints;

               uint filling = (uint)SymbolInfoInteger(Symbol(), SYMBOL_FILLING_MODE);
               if((filling & SYMBOL_FILLING_FOK) != 0) req.type_filling = ORDER_FILLING_FOK;
               else if((filling & SYMBOL_FILLING_IOC) != 0) req.type_filling = ORDER_FILLING_IOC;
               else req.type_filling = ORDER_FILLING_RETURN;

               req.type = (type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
               req.price = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(Symbol(), SYMBOL_BID) : SymbolInfoDouble(Symbol(), SYMBOL_ASK);

               if(OrderSend(req, res))
               {
                  g_partialTP2Fired = true;
                  Print("💰 [TP2 HIT]: Closed 50% remaining (", closeVol, " lots) on #", ticket, " at +", DoubleToString(TP2_ATR_Mult, 1), "× ATR");
               }
            }
         }

         // === TRAILING STOP: Trail at 1.0× ATR behind price ===
         if(profitDist >= atrVal * 1.5)
         {
            double trailSl;
            if(type == POSITION_TYPE_BUY)
               trailSl = NormalizeDouble(currentPrice - atrVal, digits);
            else
               trailSl = NormalizeDouble(currentPrice + atrVal, digits);

            bool shouldTrail = false;
            if(type == POSITION_TYPE_BUY)
               shouldTrail = (trailSl > currentSl && trailSl > openPrice);
            else
               shouldTrail = (currentSl == 0 || (trailSl < currentSl && trailSl < openPrice));

            if(shouldTrail)
            {
               MqlTradeRequest req;
               MqlTradeResult res;
               ZeroMemory(req);
               ZeroMemory(res);
               req.action   = TRADE_ACTION_SLTP;
               req.position = ticket;
               req.symbol   = Symbol();
               req.sl       = trailSl;
               req.tp       = currentTp;
               if(OrderSend(req, res))
                  Print("📈 [TRAILING]: #", ticket, " SL trailed to ", DoubleToString(trailSl, digits));
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Sync Account to Supabase Cloud                                    |
//+------------------------------------------------------------------+
void SyncAccountToSupabase()
{
   if(StringLen(SupabaseUrl) == 0 || StringLen(SupabaseApiKey) == 0) return;

   string url = SupabaseUrl + "/rest/v1/accounts";
   string headers = "apikey: " + SupabaseApiKey + "\r\n"
                  + "Authorization: Bearer " + SupabaseApiKey + "\r\n"
                  + "Content-Type: application/json\r\n"
                  + "Prefer: resolution=merge-duplicates\r\n";

   string accNum = (StringLen(ClientAccountID) > 0) ? ClientAccountID : IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
   string broker = AccountInfoString(ACCOUNT_COMPANY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   string curr = AccountInfoString(ACCOUNT_CURRENCY);

   string json = "{\"account_number\":\"" + accNum + "\","
                + "\"broker_name\":\"" + broker + "\","
                + "\"license_key\":\"" + KestrelAPIToken + "\","
                + "\"balance\":" + DoubleToString(balance, 2) + ","
                + "\"equity\":" + DoubleToString(equity, 2) + ","
                + "\"currency\":\"" + curr + "\","
                + "\"total_profit\":" + DoubleToString(g_totalProfit, 2) + ","
                + "\"today_profit\":" + DoubleToString(g_todayProfit, 2) + ","
                + "\"current_drawdown_pct\":" + DoubleToString(g_currentDrawdown, 2) + ","
                + "\"recovery_level\":\"" + g_recoveryLevel + "\","
                + "\"recovery_multiplier\":" + DoubleToString(g_recoveryMult * ClientRiskMultiplier, 2) + ","
                + "\"auto_trade_enabled\":" + (g_autoPilotActive ? "true" : "false") + "}";

   char post_data[], result[];
   StringToCharArray(json, post_data, 0, StringLen(json));
   string result_headers;
   ResetLastError();
   WebRequest("POST", url, headers, NULL, 4000, post_data, ArraySize(post_data), result, result_headers);
}

//+------------------------------------------------------------------+
//| Report Trade to Supabase                                          |
//+------------------------------------------------------------------+
void ReportTradeToSupabase(string direction, double price, double lots, double sl, double tp, ulong ticket)
{
   if(StringLen(SupabaseUrl) == 0 || StringLen(SupabaseApiKey) == 0) return;

   string url = SupabaseUrl + "/rest/v1/trades";
   string headers = "apikey: " + SupabaseApiKey + "\r\n"
                  + "Authorization: Bearer " + SupabaseApiKey + "\r\n"
                  + "Content-Type: application/json\r\n";

   string accNum = (StringLen(ClientAccountID) > 0) ? ClientAccountID : IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));

   string json = "{\"instrument\":\"" + GetInstrument() + "\","
                + "\"timeframe\":\"" + GetTimeframe() + "\","
                + "\"direction\":\"" + direction + "\","
                + "\"account_number\":\"" + accNum + "\","
                + "\"lot_size\":" + DoubleToString(lots, 2) + ","
                + "\"entry_price\":" + DoubleToString(price, 5) + ","
                + "\"stop_loss\":" + DoubleToString(sl, 5) + ","
                + "\"take_profit\":" + DoubleToString(tp, 5) + ","
                + "\"mt5_ticket\":" + IntegerToString((long)ticket) + ","
                + "\"confidence_at_entry\":" + DoubleToString(g_lastConfidence, 3) + ","
                + "\"swarm_consensus_pct\":" + DoubleToString(g_consensusPct, 1) + ","
                + "\"market_regime\":\"" + g_lastRegime + "\","
                + "\"status\":\"open\","
                + "\"execution_status\":\"OPEN\"}";

   char post_data[], result[];
   StringToCharArray(json, post_data, 0, StringLen(json));
   string result_headers;
   ResetLastError();
   WebRequest("POST", url, headers, NULL, 4000, post_data, ArraySize(post_data), result, result_headers);
}

//+------------------------------------------------------------------+
//| Poll Remote Web Commands & Multi-Client Broadcast Queue          |
//+------------------------------------------------------------------+
void PollRemoteWebCommands()
{
   if(StringLen(SupabaseUrl) == 0 || StringLen(SupabaseApiKey) == 0) return;

   string url = SupabaseUrl + "/rest/v1/system_logs?log_type=eq.REMOTE_COMMAND&order=created_at.desc&limit=1";
   string headers = "apikey: " + SupabaseApiKey + "\r\n"
                  + "Authorization: Bearer " + SupabaseApiKey + "\r\n";

   char post_data[], result[];
   string result_headers;
   ResetLastError();
   int res = WebRequest("GET", url, headers, NULL, 3000, post_data, 0, result, result_headers);
   if(res == 200 && ArraySize(result) > 0)
   {
      string responseStr = CharArrayToString(result);

      string clientBuyCmd = "COMMAND: BUY_CLIENT_" + ClientAccountID;
      string clientSellCmd = "COMMAND: SELL_CLIENT_" + ClientAccountID;

      if(StringFind(responseStr, "COMMAND: BUY") >= 0 || StringFind(responseStr, clientBuyCmd) >= 0)
      {
         if(TimeCurrent() - g_lastExecutedCommandTime > 6)
         {
            g_lastExecutedCommandTime = TimeCurrent();
            Print("⚡ [BROADCAST]: BUY on Account #", ClientAccountID);
            ExecuteAutonomousTrade("BUY", LotSize);
            Render3DHUD();
         }
      }
      else if(StringFind(responseStr, "COMMAND: SELL") >= 0 || StringFind(responseStr, clientSellCmd) >= 0)
      {
         if(TimeCurrent() - g_lastExecutedCommandTime > 6)
         {
            g_lastExecutedCommandTime = TimeCurrent();
            Print("⚡ [BROADCAST]: SELL on Account #", ClientAccountID);
            ExecuteAutonomousTrade("SELL", LotSize);
            Render3DHUD();
         }
      }
      else if(StringFind(responseStr, "COMMAND: CLOSE_ALL") >= 0 || StringFind(responseStr, "COMMAND: CLOSE_ALL_CLIENTS") >= 0)
      {
         if(TimeCurrent() - g_lastExecutedCommandTime > 6)
         {
            g_lastExecutedCommandTime = TimeCurrent();
            Print("🛡️ [HALT]: Closing all on Account #", ClientAccountID);
            CloseAllSymbolPositions();
            Render3DHUD();
         }
      }
   }
}

//+------------------------------------------------------------------+
//| ★ RENDER ANALYSIS HUD — Full Intelligence Dashboard ★             |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| ★ RENDER ANALYSIS HUD — Client-Ready Intelligence Dashboard ★    |
//+------------------------------------------------------------------+
void Render3DHUD()
{
   int x = 20;
   int y = 20;

   // ─── MINIMIZED EXECUTIVE CLIENT MODE ───
   if(g_hudMode == HUD_MODE_MINIMIZED)
   {
      int minW = 820;
      int minH = 40;
      CreateRectLabel("BG_3D_BACK", x - 2, y - 2, minW + 4, minH + 4, C'5,7,12', C'0,229,255', 1);
      CreateRectLabel("BG_MAIN", x, y, minW, minH, C'12,16,26', C'0,180,220', 2);

      CreateLabel("LBL_BRAND", "🦅 KESTREL v5.1", x + 12, y + 12, "Segoe UI Black", 9, C'0,229,255');

      string stars = GetStarRating(g_lastAnalysis.confidence);
      string sigText = "";
      color sigCol = C'255,200,0';
      if(g_lastAnalysis.direction == "BUY") { sigText = "⚡ BUY " + stars + " (" + DoubleToString(g_lastAnalysis.confidence * 100, 1) + "%)"; sigCol = C'0,255,136'; }
      else if(g_lastAnalysis.direction == "SELL") { sigText = "⚡ SELL " + stars + " (" + DoubleToString(g_lastAnalysis.confidence * 100, 1) + "%)"; sigCol = C'255,34,85'; }
      else { sigText = "⚪ HOLD — Awaiting Confluence"; sigCol = C'255,200,0'; }
      CreateLabel("LBL_MIN_SIG", sigText, x + 155, y + 12, "Segoe UI Bold", 9, sigCol);

      string pnlSign = (g_openProfit >= 0) ? "+$" : "-$";
      color pnlCol = (g_openProfit >= 0) ? C'0,255,136' : C'255,34,85';
      CreateLabel("LBL_MIN_PNL", "P/L: " + pnlSign + DoubleToString(MathAbs(g_openProfit), 2), x + 355, y + 12, "Consolas Bold", 9, pnlCol);

      string cndText = "🕯️ " + (g_activePattern.patternName != "" ? g_activePattern.patternName : "Standard Price Action") +
                       " [" + DoubleToString(g_candleAnatomy.buyingPressurePct, 0) + "% Buy]";
      CreateLabel("LBL_MIN_CND", cndText, x + 475, y + 12, "Segoe UI", 8, C'200,225,250');

      CreateButton("BTN_TOGGLE_HUD", "🗖 EXPAND", x + 725, y + 7, 80, 26, C'20,40,70', C'0,229,255');

      ChartRedraw(0);
      return;
   }

   // ─── EXPANDED FULL INTELLIGENCE MODE ───
   int panelW = 490;
   int panelH = 960;

   // ─── 1. PANEL FRAME ───
   CreateRectLabel("BG_3D_BACK", x - 2, y - 2, panelW + 4, panelH + 4, C'5,7,12', C'0,229,255', 1);
   CreateRectLabel("BG_MAIN", x, y, panelW, panelH, C'12,16,26', C'0,180,220', 2);

   // ─── 2. HEADER + BIAS PANEL ───
   CreateLabel("LBL_BRAND", "🦅 KESTREL INTELLIGENCE ENGINE v5.1", x + 16, y + 10, "Segoe UI Black", 9, C'0,229,255');
   bool isMaster = (ClientAccountID == "41230754");
   string clientTag = isMaster ? "👑 MASTER" : "👥 " + ClientAccountID;
   CreateLabel("LBL_CLIENT_TAG", clientTag, x + 310, y + 10, "Segoe UI Bold", 8, isMaster ? C'0,229,255' : C'255,200,0');

   // Interactive Minimize Button
   CreateButton("BTN_TOGGLE_HUD", "🗕 MIN", x + 420, y + 7, 54, 22, C'20,35,55', C'0,229,255');

   string connDot = (g_connectionStatus == "online") ? "● CLOUD" : "● LOCAL";
   color connCol = (g_connectionStatus == "online") ? C'0,255,136' : C'255,200,0';
   CreateLabel("LBL_CONN", connDot + " | " + g_currentSession, x + 310, y + 26, "Consolas", 7, connCol);

   CreateRectLabel("SEP_1", x + 14, y + 42, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);

   // ─── 3. FINANCIAL PERFORMANCE ───
   int fy = y + 50;
   CreateLabel("SEC_FIN_TITLE", "FINANCIAL PERFORMANCE", x + 16, fy, "Segoe UI Bold", 8, C'130,150,180');

   CreateLabel("LBL_BAL_T", "BALANCE", x + 16, fy + 16, "Segoe UI", 7, C'120,135,160');
   CreateLabel("LBL_BAL_V", "$" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2), x + 16, fy + 28, "Consolas Bold", 10, C'240,245,255');

   CreateLabel("LBL_EQU_T", "EQUITY", x + 140, fy + 16, "Segoe UI", 7, C'120,135,160');
   CreateLabel("LBL_EQU_V", "$" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2), x + 140, fy + 28, "Consolas Bold", 10, C'0,229,255');

   CreateLabel("LBL_OPN_T", "FLOAT P/L", x + 265, fy + 16, "Segoe UI", 7, C'120,135,160');
   color opColor = (g_openProfit >= 0) ? C'0,255,136' : C'255,34,85';
   string opSign = (g_openProfit >= 0) ? "+$" : "-$";
   CreateLabel("LBL_OPN_V", opSign + DoubleToString(MathAbs(g_openProfit), 2), x + 265, fy + 28, "Consolas Bold", 10, opColor);

   CreateLabel("LBL_TDY_T", "TODAY", x + 385, fy + 16, "Segoe UI", 7, C'120,135,160');
   color tdColor = (g_todayProfit >= 0) ? C'0,255,136' : C'255,34,85';
   string tdSign = (g_todayProfit >= 0) ? "+$" : "-$";
   CreateLabel("LBL_TDY_V", tdSign + DoubleToString(MathAbs(g_todayProfit), 2), x + 385, fy + 28, "Consolas Bold", 10, tdColor);

   CreateRectLabel("SEP_2", x + 14, fy + 48, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);

   // ─── 4. MAIN SIGNAL + STAR RATING ───
   int ay = fy + 56;
   CreateLabel("SEC_ANA_TITLE", "SIGNAL ANALYSIS", x + 16, ay, "Segoe UI Bold", 8, C'130,150,180');

   string dirText = "";
   color dirColor = C'255,200,0';
   string stars = GetStarRating(g_lastAnalysis.confidence);
   string strength = GetSignalStrength(g_lastAnalysis.confidence);

   if(g_lastAnalysis.direction == "BUY")
   {
      dirText = "⚡ BUY " + stars + " (" + DoubleToString(g_lastAnalysis.confidence * 100, 1) + "%)";
      dirColor = C'0,255,136';
   }
   else if(g_lastAnalysis.direction == "SELL")
   {
      dirText = "⚡ SELL " + stars + " (" + DoubleToString(g_lastAnalysis.confidence * 100, 1) + "%)";
      dirColor = C'255,34,85';
   }
   else
   {
      dirText = "⚪ HOLD — Waiting for Confluence";
      dirColor = C'255,200,0';
   }
   CreateLabel("LBL_ANA_DIR", dirText, x + 16, ay + 18, "Segoe UI Black", 11, dirColor);

   int maxExpected = EnableCandleAnalysis ? 9 : 8;
   string scoreText = "Score: " + DoubleToString(g_lastAnalysis.score, 3) +
                      " | " + IntegerToString(g_lastAnalysis.indicatorsAvailable) + "/" + IntegerToString(maxExpected) + " Ind" +
                      " | " + g_lastRegime + " | " + strength;
   CreateLabel("LBL_ANA_SCORE", scoreText, x + 16, ay + 36, "Segoe UI", 7, C'170,185,210');

   // Risk-based lot suggestion
   if(RiskPercentPerTrade > 0 && g_lastAnalysis.direction != "HOLD")
   {
      CreateLabel("LBL_LOT_SUGGEST", "Lot: " + g_suggestedLotText, x + 16, ay + 50, "Consolas", 7, C'0,229,255');
   }
   else
   {
      CreateLabel("LBL_LOT_SUGGEST", "Lot: " + DoubleToString(LotSize, 2) + " (fixed)", x + 16, ay + 50, "Consolas", 7, C'100,120,150');
   }

   CreateRectLabel("SEP_3", x + 14, ay + 64, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);

   // ─── 5. CANDLESTICK PATTERN & ANATOMY ───
   int cndY = ay + 72;
   if(EnableCandleAnalysis)
   {
      CreateLabel("SEC_CND_TITLE", "CANDLESTICK PATTERN & ANATOMY", x + 16, cndY, "Segoe UI Bold", 8, C'130,150,180');

      string pressText = "Pressure: 🟢 Buy " + DoubleToString(g_candleAnatomy.buyingPressurePct, 0) + "% | 🔴 Sell " +
                         DoubleToString(g_candleAnatomy.sellingPressurePct, 0) + "% | Close: " + g_candleAnatomy.timeRemainingText;
      CreateLabel("LBL_CND_PRESS", pressText, x + 16, cndY + 16, "Consolas", 7, C'0,229,255');

      color patCol = (g_activePattern.vote > 0) ? C'0,255,136' : ((g_activePattern.vote < 0) ? C'255,34,85' : C'170,185,210');
      string patText = (g_activePattern.patternName != "") ?
                        (g_activePattern.patternName + " (" + DoubleToString(g_activePattern.confidence * 100, 0) + "% Conf) — " + g_activePattern.description) :
                        "Standard Price Action (No Reversal Pattern)";
      CreateLabel("LBL_CND_PAT", patText, x + 16, cndY + 30, "Segoe UI", 7, patCol);

      string structLabel = g_candleAnatomy.isExpansionBar ? "⚡ Expansion (" : (g_candleAnatomy.isCompressionBar ? "📦 Squeeze (" : "⚖️ Normal (");
      structLabel += DoubleToString(g_candleAnatomy.atrRatio, 1) + "x ATR)";
      if(EnableFVGDetection && g_activeFVG.active)
         structLabel += " | " + g_activeFVG.direction + " FVG Active";
      CreateLabel("LBL_CND_STRUCT", "Structure: " + structLabel, x + 16, cndY + 44, "Segoe UI", 7, C'200,215,240');

      CreateRectLabel("SEP_CND", x + 14, cndY + 58, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);
      cndY += 66;
   }

   // ─── 6. MULTI-TIMEFRAME CONFLUENCE ───
   int my = cndY;
   if(EnableMTFPanel)
   {
      CreateLabel("SEC_MTF_TITLE", "MULTI-TIMEFRAME CONFLUENCE", x + 16, my, "Segoe UI Bold", 8, C'130,150,180');

      string mtfRow = "";
      for(int i = 0; i < 5; i++)
      {
         string icon = "";
         if(g_mtfData.slots[i].direction == "BUY") icon = "🟢";
         else if(g_mtfData.slots[i].direction == "SELL") icon = "🔴";
         else icon = "🟡";
         mtfRow += g_mtfData.slots[i].label + ":" + icon + "  ";
      }
      CreateLabel("LBL_MTF_ROW", mtfRow, x + 16, my + 18, "Consolas", 8, C'220,230,245');

      color consColor = C'255,200,0';
      if(g_mtfData.agreementCount >= 4) consColor = C'0,255,136';
      else if(g_mtfData.agreementCount <= 1) consColor = C'255,34,85';
      CreateLabel("LBL_MTF_AGR", "Agreement: " + IntegerToString(g_mtfData.agreementCount) + "/5 — " + g_mtfData.consensus,
                  x + 16, my + 34, "Segoe UI", 7, consColor);

      CreateRectLabel("SEP_MTF", x + 14, my + 50, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);
      my += 58;
   }

   // ─── 7. MODEL CONSENSUS BREAKDOWN ───
   CreateLabel("SEC_CON_TITLE", "MODEL CONSENSUS (" + IntegerToString(g_modelConsensus.totalModels) + " models)",
               x + 16, my, "Segoe UI Bold", 8, C'130,150,180');

   for(int c = 0; c < 5; c++)
   {
      int cy = my + 18 + c * 16;
      string catName = g_modelConsensus.categories[c].name;

      int barTotal = g_modelConsensus.categories[c].totalModels;
      int barBuy = g_modelConsensus.categories[c].buyVotes;
      int barSell = g_modelConsensus.categories[c].sellVotes;
      string bar = "";
      for(int b = 0; b < barBuy; b++) bar += "█";
      for(int b = 0; b < barSell; b++) bar += "▓";
      for(int b = 0; b < barTotal - barBuy - barSell; b++) bar += "░";

      string verdict = g_modelConsensus.categories[c].verdict;
      color vColor = (verdict == "BUY") ? C'0,255,136' : ((verdict == "SELL") ? C'255,34,85' : C'170,185,210');

      string catText = catName + ": " + bar + " " +
                       IntegerToString(MathMax(barBuy, barSell)) + "/" +
                       IntegerToString(barTotal) + " " + verdict;
      CreateLabel("LBL_CON_" + IntegerToString(c), catText, x + 16, cy, "Consolas", 7, vColor);
   }

   string consensusLine = "Overall: " + DoubleToString(g_modelConsensus.overallConsensusPct, 0) + "% consensus (" +
                          IntegerToString(g_modelConsensus.totalAgreeing) + "/" +
                          IntegerToString(g_modelConsensus.totalModels) + " agree)";
   CreateLabel("LBL_CON_TOTAL", consensusLine, x + 16, my + 18 + 5 * 16, "Segoe UI", 7, C'170,185,210');

   CreateRectLabel("SEP_CON", x + 14, my + 18 + 5 * 16 + 14, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);
   int iy = my + 18 + 5 * 16 + 22;

   // ─── 8. INDICATOR BREAKDOWN (9 Indicators) ───
   CreateLabel("SEC_IND_TITLE", "INDICATOR BREAKDOWN", x + 16, iy, "Segoe UI Bold", 8, C'130,150,180');

   int row1 = iy + 16;
   int row2 = row1 + 16;
   int row3 = row2 + 16;
   int row4 = row3 + 16;
   int row5 = row4 + 16;
   int col1 = x + 16;
   int col2 = x + 255;

   // Row 1: EMA | RSI
   string emaIcon = (g_lastAnalysis.emaVote > 0) ? "✅" : ((g_lastAnalysis.emaVote < 0) ? "❌" : "⚪");
   string emaText = emaIcon + " EMA: " + ((g_lastAnalysis.emaVote > 0) ? "BULL" : ((g_lastAnalysis.emaVote < 0) ? "BEAR" : "MIX"));
   color emaCol = (g_lastAnalysis.emaVote > 0) ? C'0,255,136' : ((g_lastAnalysis.emaVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_EMA", emaText, col1, row1, "Consolas", 7, emaCol);

   string rsiIcon = (g_lastAnalysis.rsiVote > 0) ? "✅" : ((g_lastAnalysis.rsiVote < 0) ? "❌" : "⚪");
   string rsiText = rsiIcon + " RSI: " + DoubleToString(g_lastAnalysis.rsiValue, 1);
   color rsiCol = (g_lastAnalysis.rsiVote > 0) ? C'0,255,136' : ((g_lastAnalysis.rsiVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_RSI", rsiText, col2, row1, "Consolas", 7, rsiCol);

   // Row 2: MACD | BB
   string macdIcon = (g_lastAnalysis.macdVote > 0) ? "✅" : ((g_lastAnalysis.macdVote < 0) ? "❌" : "⚪");
   string macdText = macdIcon + " MACD: " + ((g_lastAnalysis.macdVote > 0) ? "BULL" : ((g_lastAnalysis.macdVote < 0) ? "BEAR" : "CROSS"));
   color macdCol = (g_lastAnalysis.macdVote > 0) ? C'0,255,136' : ((g_lastAnalysis.macdVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_MACD", macdText, col1, row2, "Consolas", 7, macdCol);

   string bbIcon = (g_lastAnalysis.bbVote > 0) ? "✅" : ((g_lastAnalysis.bbVote < 0) ? "❌" : "⚪");
   string bbText = bbIcon + " BB: " + ((g_lastAnalysis.bbVote > 0) ? "ABOVE" : ((g_lastAnalysis.bbVote < 0) ? "BELOW" : "NEUT"));
   color bbCol = (g_lastAnalysis.bbVote > 0) ? C'0,255,136' : ((g_lastAnalysis.bbVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_BB", bbText, col2, row2, "Consolas", 7, bbCol);

   // Row 3: Stoch | ADX
   string stochIcon = (g_lastAnalysis.stochVote > 0) ? "✅" : ((g_lastAnalysis.stochVote < 0) ? "❌" : "⚪");
   string stochText = stochIcon + " STOCH: " + DoubleToString(g_lastAnalysis.stochMain, 0);
   color stochCol = (g_lastAnalysis.stochVote > 0) ? C'0,255,136' : ((g_lastAnalysis.stochVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_STOCH", stochText, col1, row3, "Consolas", 7, stochCol);

   string adxIcon = (g_lastAnalysis.adxVote > 0) ? "✅" : ((g_lastAnalysis.adxVote < 0) ? "❌" : "⚪");
   string adxLabel = (g_lastAnalysis.adxValue > 25) ? "TREND" : ((g_lastAnalysis.adxValue < 20) ? "RANGE" : "WEAK");
   string adxText = adxIcon + " ADX: " + DoubleToString(g_lastAnalysis.adxValue, 0) + " " + adxLabel;
   color adxCol = (g_lastAnalysis.adxVote > 0) ? C'0,255,136' : ((g_lastAnalysis.adxVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_ADX", adxText, col2, row3, "Consolas", 7, adxCol);

   // Row 4: Volume | H4 Trend
   string volIcon = (g_lastAnalysis.volumeVote > 0) ? "✅" : ((g_lastAnalysis.volumeVote < 0) ? "❌" : "⚪");
   string volText = volIcon + " VOL: " + ((g_lastAnalysis.volumeVote != 0) ? "HIGH" : "LOW");
   color volCol = (g_lastAnalysis.volumeVote > 0) ? C'0,255,136' : ((g_lastAnalysis.volumeVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_VOL", volText, col1, row4, "Consolas", 7, volCol);

   string h4Icon = (g_lastAnalysis.h4TrendVote > 0) ? "✅" : ((g_lastAnalysis.h4TrendVote < 0) ? "❌" : "⚪");
   string h4Text = h4Icon + " H4: " + ((g_lastAnalysis.h4TrendVote > 0) ? "BULL" : ((g_lastAnalysis.h4TrendVote < 0) ? "BEAR" : "---"));
   color h4Col = (g_lastAnalysis.h4TrendVote > 0) ? C'0,255,136' : ((g_lastAnalysis.h4TrendVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_H4", h4Text, col2, row4, "Consolas", 7, h4Col);

   // Row 5: Candlestick Pattern | Market Regime
   string cndIcon = (g_lastAnalysis.candleVote > 0) ? "✅" : ((g_lastAnalysis.candleVote < 0) ? "❌" : "⚪");
   string cndText = cndIcon + " CND: " + ((g_lastAnalysis.candleVote > 0) ? "BULL" : ((g_lastAnalysis.candleVote < 0) ? "BEAR" : "NEUT"));
   color cndCol = (g_lastAnalysis.candleVote > 0) ? C'0,255,136' : ((g_lastAnalysis.candleVote < 0) ? C'255,34,85' : C'170,185,210');
   CreateLabel("LBL_IND_CND", cndText, col1, row5, "Consolas", 7, cndCol);

   string regText = "⚪ REG: " + g_lastRegime;
   CreateLabel("LBL_IND_REG", regText, col2, row5, "Consolas", 7, C'170,185,210');

   CreateRectLabel("SEP_4", x + 14, row5 + 14, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);

   int vy = row5 + 22;

   // ─── 9. VOLATILITY FORECAST ───
   if(EnableVolForecast)
   {
      CreateLabel("SEC_VOL_TITLE", "VOLATILITY FORECAST", x + 16, vy, "Segoe UI Bold", 8, C'130,150,180');

      color vfColor = C'170,185,210';
      if(g_volForecast.forecast == "EXPANDING") vfColor = C'255,200,0';
      else if(g_volForecast.forecast == "CONTRACTING") vfColor = C'0,200,255';

      int vfDigits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);
      string vfText = g_volForecast.icon + " " + g_volForecast.forecast +
                      " — ATR: " + DoubleToString(g_volForecast.currentATR, vfDigits) +
                      " → " + DoubleToString(g_volForecast.projectedATR, vfDigits) +
                      " (" + (g_volForecast.atrChangePct >= 0 ? "+" : "") +
                      DoubleToString(g_volForecast.atrChangePct, 0) + "%)";
      CreateLabel("LBL_VOL_FCAST", vfText, x + 16, vy + 16, "Consolas", 7, vfColor);

      CreateRectLabel("SEP_VOL", x + 14, vy + 32, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);
      vy += 40;
   }

   // ─── 10. NEWS PROXIMITY FLAG ───
   if(EnableNewsFilter)
   {
      if(g_newsProximityActive)
      {
         CreateLabel("SEC_NEWS_TITLE", "⚠️ NEWS ALERT", x + 16, vy, "Segoe UI Bold", 8, C'255,150,0');
         string newsText = g_newsWarningText;
         CreateLabel("LBL_NEWS_TEXT", newsText, x + 16, vy + 16, "Consolas", 7, C'255,200,0');
         CreateLabel("LBL_NEWS_PENALTY", "Confidence reduced by " + DoubleToString(g_newsConfidencePenalty * 100, 0) + "%",
                     x + 16, vy + 30, "Segoe UI", 7, C'255,150,0');
         CreateRectLabel("SEP_NEWS", x + 14, vy + 44, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);
         vy += 52;
      }
      else
      {
         CreateLabel("SEC_NEWS_TITLE", "📰 NEWS: Clear — No imminent events", x + 16, vy, "Segoe UI", 7, C'80,100,130');
         string cleanNames[3] = {"LBL_NEWS_TEXT", "LBL_NEWS_PENALTY", "SEP_NEWS"};
         for(int cn = 0; cn < 3; cn++)
         {
            string objName = g_hudPrefix + cleanNames[cn];
            if(ObjectFind(0, objName) >= 0) ObjectDelete(0, objName);
         }
         CreateRectLabel("SEP_NEWS2", x + 14, vy + 14, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);
         vy += 22;
      }
   }

   // ─── 11. PATTERN MATCH ───
   if(EnablePatternMatch)
   {
      CreateLabel("SEC_PAT_TITLE", "HISTORICAL PATTERN MATCH", x + 16, vy, "Segoe UI Bold", 8, C'130,150,180');

      color patColor = C'170,185,210';
      if(g_patternResult.totalMatches > 0 && g_patternResult.continuationPct >= 65) patColor = C'0,255,136';
      else if(g_patternResult.totalMatches > 0 && g_patternResult.continuationPct < 40) patColor = C'255,100,100';

      CreateLabel("LBL_PAT_SUM", g_patternResult.summary, x + 16, vy + 16, "Consolas", 7, patColor);

      CreateRectLabel("SEP_PAT", x + 14, vy + 32, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);
      vy += 40;
   }

   // ─── 12. POST-SIGNAL OUTCOME TRACKER ───
   if(EnableOutcomeTracker)
   {
      CreateLabel("SEC_TRK_TITLE", "SIGNAL TRACK RECORD", x + 16, vy, "Segoe UI Bold", 8, C'130,150,180');

      int displayed = 0;
      int wins = 0, losses = 0;
      double totalPips = 0;
      int totalTracked = 0;

      for(int s = 0; s < g_signalHistoryCount && s < 50; s++)
      {
         int idx = (g_signalHistoryHead - 1 - s + 50) % 50;
         if(!g_signalHistory[idx].active) continue;

         totalTracked++;
         totalPips += g_signalHistory[idx].currentPnLPips;
         if(g_signalHistory[idx].outcomeStatus == "HIT_TP") wins++;
         else if(g_signalHistory[idx].outcomeStatus == "HIT_SL") losses++;

         if(displayed < 5)
         {
            string dirIcon = (g_signalHistory[idx].direction == "BUY") ? "🟢" : "🔴";
            string confStr = DoubleToString(g_signalHistory[idx].confidenceAtEntry * 100, 0) + "%";
            string pipsStr = (g_signalHistory[idx].currentPnLPips >= 0 ? "+" : "") +
                             DoubleToString(g_signalHistory[idx].currentPnLPips, 1) + "p";

            string statusIcon = "";
            color lineCol = C'170,185,210';
            if(g_signalHistory[idx].outcomeStatus == "HIT_TP") { statusIcon = "✅"; lineCol = C'0,255,136'; }
            else if(g_signalHistory[idx].outcomeStatus == "HIT_SL") { statusIcon = "❌"; lineCol = C'255,34,85'; }
            else if(g_signalHistory[idx].outcomeStatus == "EXPIRED") { statusIcon = "⏹"; lineCol = C'100,120,150'; }
            else { statusIcon = "⏳"; lineCol = C'255,200,0'; }

            string trkLine = dirIcon + " " + g_signalHistory[idx].direction + " " + confStr +
                             " → " + pipsStr + " " + statusIcon;
            CreateLabel("LBL_TRK_" + IntegerToString(displayed), trkLine,
                        x + 16, vy + 16 + displayed * 14, "Consolas", 7, lineCol);
            displayed++;
         }
      }

      int trkSummaryY = vy + 16 + displayed * 14 + 2;
      if(totalTracked > 0)
      {
         int resolvedCount = wins + losses;
         double winRate = (resolvedCount > 0) ? ((double)wins / (double)resolvedCount * 100.0) : 0;
         double avgPips = totalPips / (double)totalTracked;
         string summaryText = "Win: " + DoubleToString(winRate, 0) + "% | Avg: " +
                              (avgPips >= 0 ? "+" : "") + DoubleToString(avgPips, 1) + " pips" +
                              " | Tracked: " + IntegerToString(totalTracked);
         CreateLabel("LBL_TRK_SUM", summaryText, x + 16, trkSummaryY, "Segoe UI Bold", 7, C'170,185,210');
      }
      else
      {
         CreateLabel("LBL_TRK_SUM", "No signals tracked yet", x + 16, trkSummaryY, "Segoe UI", 7, C'100,120,150');
      }

      for(int cl = displayed; cl < 5; cl++)
      {
         string objName = g_hudPrefix + "LBL_TRK_" + IntegerToString(cl);
         if(ObjectFind(0, objName) >= 0) ObjectDelete(0, objName);
      }

      CreateRectLabel("SEP_TRK", x + 14, trkSummaryY + 16, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);
      vy = trkSummaryY + 24;
   }

   // ─── 13. SL/TP & RISK ───
   int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);

   if(g_lastAnalysis.direction != "HOLD" && g_lastAnalysis.suggestedSL > 0)
   {
      string slText = "SL: " + DoubleToString(g_lastAnalysis.suggestedSL, digits) +
                      " | TP1: " + DoubleToString(g_lastAnalysis.suggestedTP1, digits) +
                      " | TP2: " + DoubleToString(g_lastAnalysis.suggestedTP2, digits);
      CreateLabel("LBL_SLTP", slText, x + 16, vy, "Consolas", 7, C'0,229,255');
   }
   else
   {
      CreateLabel("LBL_SLTP", "SL/TP: Waiting for signal...", x + 16, vy, "Consolas", 7, C'100,120,150');
   }

   CreateLabel("LBL_RISK", "Risk: " + g_recoveryLevel + " | ATR: " + DoubleToString(g_lastAnalysis.atrValue, digits),
               x + 16, vy + 14, "Segoe UI", 7, C'170,185,210');
   CreateLabel("LBL_STATUS", g_lastTradeMsg, x + 16, vy + 28, "Consolas", 7, C'140,160,190');

   // ─── 14. VOTE SUMMARY (9 Votes) ───
   int voteY = vy + 44;
   string voteSummary = "Votes: " + IntegerToString(g_buyIndicators) + " BUY | "
                       + IntegerToString(g_sellIndicators) + " SELL | "
                       + IntegerToString(g_neutralIndicators) + " NEUTRAL";
   CreateLabel("LBL_VOTES", voteSummary, x + 16, voteY, "Segoe UI Bold", 7, C'170,185,210');

   CreateRectLabel("SEP_5", x + 14, voteY + 16, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);

   // ─── 15. INTERACTIVE BUTTONS ───
   if(EnableInteractiveButtons)
   {
      int by = voteY + 24;
      int btnW = 105;
      int btnH = 28;

      color autoBtnBg = g_autoPilotActive ? C'0,100,60' : C'100,70,0';
      CreateButton("BTN_TOGGLE_AUTO", g_autoPilotActive ? "AUTO: ON" : "AUTO: OFF", x + 16, by, btnW, btnH, autoBtnBg, C'255,255,255');
      CreateButton("BTN_BUY_NOW", "🟢 BUY", x + 131, by, btnW, btnH, C'0,120,60', C'0,255,136');
      CreateButton("BTN_SELL_NOW", "🔴 SELL", x + 246, by, btnW, btnH, C'120,20,40', C'255,34,85');
      CreateButton("BTN_CLOSE_ALL", "🛡️ CLOSE", x + 361, by, btnW, btnH, C'50,20,70', C'255,100,200');

      panelH = by + btnH + 10 - y;
   }
   else
   {
      panelH = voteY + 24 - y;
   }

   // Update panel background sizes to match content
   ObjectSetInteger(0, g_hudPrefix + "BG_3D_BACK", OBJPROP_YSIZE, panelH + 4);
   ObjectSetInteger(0, g_hudPrefix + "BG_MAIN", OBJPROP_YSIZE, panelH);

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| HUD Helper Functions                                              |
//+------------------------------------------------------------------+
void CreateRectLabel(string name, int x, int y, int w, int h, color bg, color border, int borderWidth)
{
   string objName = g_hudPrefix + name;
   if(ObjectFind(0, objName) < 0)
   {
      ObjectCreate(0, objName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ObjectSetInteger(0, objName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, objName, OBJPROP_BACK, false);
      ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
   }
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, objName, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, objName, OBJPROP_YSIZE, h);
   ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, objName, OBJPROP_BORDER_COLOR, border);
   ObjectSetInteger(0, objName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, objName, OBJPROP_WIDTH, borderWidth);
}

void CreateLabel(string name, string text, int x, int y, string font, int fontSize, color fontColor)
{
   string objName = g_hudPrefix + name;
   if(ObjectFind(0, objName) < 0)
   {
      ObjectCreate(0, objName, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, objName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
   }
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, objName, OBJPROP_TEXT, text);
   ObjectSetString(0, objName, OBJPROP_FONT, font);
   ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, fontSize);
   ObjectSetInteger(0, objName, OBJPROP_COLOR, fontColor);
}

void CreateButton(string name, string text, int x, int y, int w, int h, color bg, color fontColor)
{
   string objName = g_hudPrefix + name;
   if(ObjectFind(0, objName) < 0)
   {
      ObjectCreate(0, objName, OBJ_BUTTON, 0, 0, 0);
      ObjectSetInteger(0, objName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
   }
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, objName, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, objName, OBJPROP_YSIZE, h);
   ObjectSetString(0, objName, OBJPROP_TEXT, text);
   ObjectSetString(0, objName, OBJPROP_FONT, "Segoe UI Bold");
   ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, objName, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, objName, OBJPROP_COLOR, fontColor);
   ObjectSetInteger(0, objName, OBJPROP_BORDER_COLOR, fontColor);
}

void CleanHUD()
{
   ObjectsDeleteAll(0, g_hudPrefix);
   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| JSON Extraction Helpers                                           |
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

// Const version for news parsing
string ExtractJsonStringConst(string json, string key)
{
   string search = "\"" + key + "\":\"";
   int start = StringFind(json, search);
   if(start < 0) return "";
   start += StringLen(search);
   int end = StringFind(json, "\"", start);
   if(end < 0) return "";
   return StringSubstr(json, start, end - start);
}

double ExtractJsonDouble(string &json, string key)
{
   string search = "\"" + key + "\":";
   int start = StringFind(json, search);
   if(start < 0) return 0.0;
   start += StringLen(search);
   string num = "";
   for(int i = start; i < StringLen(json); i++)
   {
      ushort ch = StringGetCharacter(json, i);
      if(ch == ',' || ch == '}' || ch == ']' || ch == ' ') break;
      num += ShortToString(ch);
   }
   if(num == "null") return 0.0;
   return StringToDouble(num);
}
//+------------------------------------------------------------------+
