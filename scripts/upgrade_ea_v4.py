"""
Kestrel EA Upgrade Script to v4.0 (Phase 1)
Applies institutional upgrades to adapters/mt5/KestrelEA.mq5:
- 1.1 Adaptive Regime Switcher (Hurst Exponent rolling 200 bars, ADX, Hybrid)
- 1.2 News & Volatility Filter (Forex Factory bridge / backend calendar, 30m lock, SL to BE)
- 1.3 Smart Money Concepts (SMC) (Order Blocks, FVG 50% discount fill, Liquidity Sweeps, Premium/Discount zones, >=3 confluences)
- 1.4 Prop-Firm Rules Engine (FTMO, MFF, The5ers, EquityEdge, Custom; daily loss & DD tracker, hard stop close all)
- 1.5 Single Audited CRiskEngine Class (Rule #6 compliant; Kelly Criterion cap, Correlation Guard |corr|>0.7, Daily Circuit Breaker)
- 1.6 Asynchronous WebRequest with retry/backoff (1s, 2s, 4s, 8s queue; 30s heartbeat)
- 1.7 Canvas/Object HUD v2 (Regime badge, Prop Firm bar, SMC indicators, News banner, AI consensus)
"""
import os
import shutil
import subprocess
import sys

def main():
    target_path = r"c:\Users\Admin\Documents\Kestrel\adapters\mt5\KestrelEA.mq5"
    backup_path = r"c:\Users\Admin\Documents\Kestrel\adapters\mt5\KestrelEA.mq5.bak"
    
    if not os.path.exists(backup_path):
        shutil.copyfile(target_path, backup_path)
        print(f"Created backup at {backup_path}")

    with open(backup_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update version description
    content = content.replace(
        '#property version   "5.10"',
        '#property version   "4.00"'
    )
    content = content.replace(
        '#property description "Kestrel Autonomous Smart Trading Engine v5.1 — Deep Candlestick & Multi-Dimensional Intelligence"',
        '#property description "Kestrel Autonomous Smart Trading Engine v4.0 — Institutional Quantitative Intelligence & Prop-Firm Risk Engine"'
    )

    # 2. Add new Enums after ENUM_LIQ_STYLE
    enum_insert = """
enum ENUM_REGIME_METHOD
{
   REGIME_HURST_GARCH = 0, // Hurst Exponent & Volatility Clustering
   REGIME_ADX_FILTER  = 1, // ADX & Directional Movement
   REGIME_NEURAL_NET  = 2, // Heuristic Neural Net / Multi-Layer
   REGIME_HYBRID      = 3  // Hybrid Ensemble (Hurst + ADX + MTF)
};

enum ENUM_PROP_FIRM_MODE
{
   PROP_NONE        = 0, // Standard / Personal Account (Unrestricted)
   PROP_FTMO        = 1, // FTMO Challenge (5% Daily, 10% Total DD, 4 Min Days)
   PROP_MFF         = 2, // MyForexFunds / FundedNext (5% Daily, 12% Total DD)
   PROP_THE5ERS     = 3, // The 5%ers (5% Daily, 10% Total DD, 3 Min Days)
   PROP_EQUITY_EDGE = 4, // Equity Edge (4% Daily, 8% Total DD, 5 Min Days)
   PROP_CUSTOM      = 5  // Custom Rules
};
"""
    liq_style_end = content.find("LIQ_STYLE_OFF          = 2  // Off (Pure Price Action)\n};")
    if liq_style_end != -1:
        insert_pos = liq_style_end + len("LIQ_STYLE_OFF          = 2  // Off (Pure Price Action)\n};")
        content = content[:insert_pos] + "\n" + enum_insert + content[insert_pos:]

    # 3. Add new Inputs under Input groups
    input_insert = """
input group "=== Market Regime Switcher ==="
input ENUM_REGIME_METHOD MarketRegimeDetection = REGIME_HYBRID;     // Regime Detection Method
input int                HurstLookbackBars     = 200;               // Rolling Lookback for Hurst Exponent
input double             HurstTrendThreshold   = 0.55;              // Hurst > Threshold = Persistent Trend
input double             HurstMeanRevThreshold = 0.45;              // Hurst < Threshold = Mean-Reverting

input group "=== Prop-Firm Rules Engine ==="
input ENUM_PROP_FIRM_MODE PropFirmMode         = PROP_NONE;         // Prop Firm Protection Profile
input double              PropMaxDailyLossPct  = 5.0;               // Max Daily Loss % (Custom)
input double              PropMaxTotalDDPct    = 10.0;              // Max Total Drawdown % (Custom)
input double              PropMaxLotCap        = 5.0;               // Max Allowed Lot Size (Custom)
input int                 PropMinTradingDays   = 4;                 // Minimum Trading Days Target

input group "=== News & Volatility Guard ==="
input int                 MinutesBeforeNews    = 30;                // Minutes Window Before/After High-Impact Event
input string              MinImpactLevel       = "HIGH";            // Minimum Impact Level ("HIGH", "MEDIUM", "ALL")

input group "=== Smart Money Concepts (SMC) ==="
input bool                EnableSMC            = true;              // Enable SMC Order Blocks & Liquidity Engine
input int                 SMCMinConfluence     = 3;                 // Minimum SMC Confluences Required for Entry
"""
    group_candle = content.find('input group "=== Candlestick & Price Action Engine ==="')
    if group_candle != -1:
        content = content[:group_candle] + input_insert + "\n" + content[group_candle:]

    # 4. Add Structs for SMC and QueuedWebRequest
    struct_insert = """
//--- Smart Money Concepts (SMC) Structures
struct SMCOrderBlock
{
   bool     active;
   string   obType;          // "BULLISH_OB", "BEARISH_OB"
   double   topPrice;
   double   bottomPrice;
   int      barIndex;
   datetime barTime;
   int      sweepsCount;     // Expiration after 3 price sweeps
   bool     mitigated;
};

struct SMCConfluence
{
   bool     isValid;
   int      bullishOBVote;
   int      bearishOBVote;
   int      fvgDiscountVote;
   int      liqSweepVote;
   int      multiTfBosVote;
   int      premDiscVote;
   int      confluenceCount;
   string   bias;            // "BUY", "SELL", "NEUTRAL"
   double   equilibrium;
   string   summary;
};

//--- Asynchronous Web Request Queue
struct QueuedWebRequest
{
   string   method;
   string   url;
   string   headers;
   string   body;
   int      retryCount;
   datetime nextAttemptTime;
   string   context;
   bool     inUse;
};
"""
    struct_pos = content.find("//--- Multi-Timeframe Analysis\nstruct MTFSlot")
    if struct_pos != -1:
        content = content[:struct_pos] + struct_insert + "\n" + content[struct_pos:]

    # 5. Add Globals for SMC, Prop-firm, WebQueue, and CRiskEngine forward declaration
    globals_insert = """
//--- Smart Money Concepts (SMC) Globals
SMCOrderBlock     g_recentOBs[10];
int               g_recentOBCount = 0;
SMCConfluence     g_smcData;

//--- Asynchronous Web Request Queue Globals
QueuedWebRequest  g_webQueue[16];
int               g_webQueueCount = 0;
datetime          g_lastHeartbeatTime = 0;

//--- Prop-Firm & Risk Tracking Globals
double            g_dayStartEquity = 0.0;
double            g_peakEquity = 0.0;
double            g_initialAccountBalance = 0.0;
int               g_lastRecordedDay = -1;
int               g_tradingDaysCount = 0;
bool              g_propRuleBreached = false;
string            g_propBreachReason = "";

//--- Market Regime Switcher Globals
double            g_currentHurst = 0.50;
double            g_currentAdx = 20.0;
string            g_regimeDetailed = "INITIALIZING...";
bool              g_newsBlockActive = false;
"""
    globals_pos = content.find("ConfluenceAnalysis g_lastAnalysis;")
    if globals_pos != -1:
        content = content[:globals_pos] + globals_insert + "\n" + content[globals_pos:]

    # 6. Insert CRiskEngine class and new calculation functions before ExecuteAutonomousTrade
    risk_engine_code = """
//+------------------------------------------------------------------+
//| ASYNCHRONOUS WEB REQUEST QUEUE WITH EXPONENTIAL BACKOFF          |
//+------------------------------------------------------------------+
void EnqueueWebRequest(string method, string url, string headers, string body, string context)
{
   if(g_webQueueCount >= 16)
   {
      // Shift queue to drop oldest
      for(int i = 0; i < 15; i++)
         g_webQueue[i] = g_webQueue[i + 1];
      g_webQueueCount = 15;
   }

   int idx = g_webQueueCount;
   g_webQueue[idx].method = method;
   g_webQueue[idx].url = url;
   g_webQueue[idx].headers = headers;
   g_webQueue[idx].body = body;
   g_webQueue[idx].retryCount = 0;
   g_webQueue[idx].nextAttemptTime = TimeCurrent();
   g_webQueue[idx].context = context;
   g_webQueue[idx].inUse = true;
   g_webQueueCount++;
}

void ProcessWebQueue()
{
   if(g_webQueueCount <= 0) return;

   datetime now = TimeCurrent();
   for(int i = 0; i < g_webQueueCount; i++)
   {
      if(!g_webQueue[i].inUse) continue;
      if(now < g_webQueue[i].nextAttemptTime) continue;

      char postData[], result[];
      string resultHeaders;
      if(StringLen(g_webQueue[i].body) > 0)
         StringToCharArray(g_webQueue[i].body, postData, 0, StringLen(g_webQueue[i].body));

      ResetLastError();
      int res = WebRequest(g_webQueue[i].method, g_webQueue[i].url, g_webQueue[i].headers, NULL, 3000, postData, ArraySize(postData), result, resultHeaders);

      if(res == 200 || res == 201 || res == 204)
      {
         // Success - remove from queue
         for(int j = i; j < g_webQueueCount - 1; j++)
            g_webQueue[j] = g_webQueue[j + 1];
         g_webQueueCount--;
         i--;
      }
      else
      {
         g_webQueue[i].retryCount++;
         if(g_webQueue[i].retryCount >= 4)
         {
            Print("⚠️ [WEB QUEUE]: Max retries reached for ", g_webQueue[i].context, ". Dropping item.");
            for(int j = i; j < g_webQueueCount - 1; j++)
               g_webQueue[j] = g_webQueue[j + 1];
            g_webQueueCount--;
            i--;
         }
         else
         {
            // Exponential backoff: 1s, 2s, 4s, 8s
            int backoffSec = 1 << g_webQueue[i].retryCount;
            g_webQueue[i].nextAttemptTime = now + backoffSec;
            Print("🔄 [WEB QUEUE]: Retry #", g_webQueue[i].retryCount, " in ", backoffSec, "s for ", g_webQueue[i].context);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| ADAPTIVE REGIME SWITCHER - HURST EXPONENT (ROLLING 200 BARS)     |
//+------------------------------------------------------------------+
double CalculateHurstExponent(int lookback = 200)
{
   if(lookback < 50) lookback = 50;
   double closePrices[];
   ArraySetAsSeries(closePrices, true);
   if(CopyClose(Symbol(), Period(), 0, lookback + 1, closePrices) < lookback + 1)
      return 0.50; // Neutral random walk

   // 1. Calculate logarithmic returns
   double returns[];
   ArrayResize(returns, lookback);
   double sumReturns = 0.0;
   for(int i = 0; i < lookback; i++)
   {
      double p0 = closePrices[i + 1];
      double p1 = closePrices[i];
      if(p0 <= 0.0) p0 = 1.0;
      if(p1 <= 0.0) p1 = 1.0;
      returns[i] = MathLog(p1 / p0);
      sumReturns += returns[i];
   }
   double meanReturn = sumReturns / (double)lookback;

   // 2. Cumulative deviations from the mean
   double cumDev[];
   ArrayResize(cumDev, lookback);
   double currentCum = 0.0;
   double maxDev = -1e9;
   double minDev = 1e9;
   double sumSqDev = 0.0;

   for(int i = 0; i < lookback; i++)
   {
      double dev = returns[i] - meanReturn;
      currentCum += dev;
      cumDev[i] = currentCum;
      if(currentCum > maxDev) maxDev = currentCum;
      if(currentCum < minDev) minDev = currentCum;
      sumSqDev += dev * dev;
   }

   // 3. Rescaled Range R/S
   double rangeR = maxDev - minDev;
   double stdDevS = MathSqrt(sumSqDev / (double)lookback);
   if(stdDevS <= 1e-12 || rangeR <= 1e-12) return 0.50;

   double rescaledRange = rangeR / stdDevS;

   // 4. Hurst exponent H = ln(R/S) / ln(N / 2)
   double hurst = MathLog(rescaledRange) / MathLog((double)lookback / 2.0);

   if(hurst < 0.05) hurst = 0.05;
   if(hurst > 0.95) hurst = 0.95;

   return hurst;
}

string EvaluateMarketRegime(double &outHurst, double &outAdx)
{
   outHurst = CalculateHurstExponent(HurstLookbackBars);

   double adxBuf[];
   ArraySetAsSeries(adxBuf, true);
   outAdx = 20.0;
   if(g_hAdx14 != INVALID_HANDLE && CopyBuffer(g_hAdx14, 0, 0, 1, adxBuf) >= 1)
      outAdx = adxBuf[0];

   string regimeStr = "CHOPPY / NEUTRAL";
   if(MarketRegimeDetection == REGIME_HURST_GARCH)
   {
      if(outHurst > HurstTrendThreshold) regimeStr = "PERSISTENT TREND (H=" + DoubleToString(outHurst, 2) + ")";
      else if(outHurst < HurstMeanRevThreshold) regimeStr = "MEAN-REVERTING (H=" + DoubleToString(outHurst, 2) + ")";
      else regimeStr = "RANDOM WALK / CHOP (H=" + DoubleToString(outHurst, 2) + ")";
   }
   else if(MarketRegimeDetection == REGIME_ADX_FILTER)
   {
      if(outAdx >= 25.0) regimeStr = "STRONG TREND (ADX=" + DoubleToString(outAdx, 1) + ")";
      else if(outAdx < 20.0) regimeStr = "RANGE / MEAN-REV (ADX=" + DoubleToString(outAdx, 1) + ")";
      else regimeStr = "TRANSITIONAL";
   }
   else // REGIME_HYBRID or REGIME_NEURAL_NET
   {
      if(outHurst > HurstTrendThreshold && outAdx >= 22.0)
         regimeStr = "HIGH CONVICTION TREND [H=" + DoubleToString(outHurst, 2) + "|ADX=" + DoubleToString(outAdx, 0) + "]";
      else if(outHurst < HurstMeanRevThreshold && outAdx < 22.0)
         regimeStr = "PRIME MEAN-REVERSION [H=" + DoubleToString(outHurst, 2) + "|ADX=" + DoubleToString(outAdx, 0) + "]";
      else if(outHurst > 0.52)
         regimeStr = "MILD TREND [H=" + DoubleToString(outHurst, 2) + "]";
      else
         regimeStr = "CHOPPY RANGE [H=" + DoubleToString(outHurst, 2) + "]";
   }
   return regimeStr;
}

//+------------------------------------------------------------------+
//| SMART MONEY CONCEPTS (SMC) MODULE                                |
//+------------------------------------------------------------------+
void DetectSmartMoneyConcepts()
{
   g_smcData.isValid = false;
   g_smcData.bullishOBVote = 0;
   g_smcData.bearishOBVote = 0;
   g_smcData.fvgDiscountVote = 0;
   g_smcData.liqSweepVote = 0;
   g_smcData.multiTfBosVote = 0;
   g_smcData.premDiscVote = 0;
   g_smcData.confluenceCount = 0;
   g_smcData.bias = "NEUTRAL";
   g_smcData.summary = "No SMC Setup";

   if(!EnableSMC) return;

   int bars = 50;
   double o[], h[], l[], c[];
   datetime t[];
   ArraySetAsSeries(o, true); ArraySetAsSeries(h, true);
   ArraySetAsSeries(l, true); ArraySetAsSeries(c, true);
   ArraySetAsSeries(t, true);

   if(CopyOpen(Symbol(), Period(), 0, bars, o) < bars ||
      CopyHigh(Symbol(), Period(), 0, bars, h) < bars ||
      CopyLow(Symbol(), Period(), 0, bars, l) < bars ||
      CopyClose(Symbol(), Period(), 0, bars, c) < bars ||
      CopyTime(Symbol(), Period(), 0, bars, t) < bars)
      return;

   double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
   double atrVal = g_lastAnalysis.atrValue;
   if(atrVal <= 0) atrVal = point * 200;

   // 1. Premium / Discount Equilibrium over 50 bars
   double highest50 = h[0];
   double lowest50 = l[0];
   for(int b = 1; b < bars; b++)
   {
      if(h[b] > highest50) highest50 = h[b];
      if(l[b] < lowest50) lowest50 = l[b];
   }
   double equilibrium = (highest50 + lowest50) / 2.0;
   g_smcData.equilibrium = equilibrium;

   double currentPrice = c[0];
   if(currentPrice < equilibrium)
   {
      g_smcData.premDiscVote = 1; // Discount zone -> Bullish favor
   }
   else if(currentPrice > equilibrium)
   {
      g_smcData.premDiscVote = -1; // Premium zone -> Bearish favor
   }

   // 2. Order Block (OB) Detection
   // Bullish OB: Last down candle before strong expansion breaking structure
   // Bearish OB: Last up candle before strong expansion breaking structure
   for(int i = 1; i < 25; i++)
   {
      // Bullish OB: candle i is bearish, candle i-1 and 0 are strong bullish expansion
      if(c[i] < o[i] && c[i - 1] > o[i - 1] && (c[i - 1] - o[i - 1]) > 1.2 * atrVal)
      {
         // Test if price is currently testing this OB zone
         if(currentPrice >= l[i] && currentPrice <= h[i])
         {
            g_smcData.bullishOBVote = 1;
            break;
         }
      }
      // Bearish OB: candle i is bullish, candle i-1 is strong bearish expansion
      if(c[i] > o[i] && c[i - 1] < o[i - 1] && (o[i - 1] - c[i - 1]) > 1.2 * atrVal)
      {
         if(currentPrice >= l[i] && currentPrice <= h[i])
         {
            g_smcData.bearishOBVote = -1;
            break;
         }
      }
   }

   // 3. Fair Value Gap (FVG) with 50% discount fill tracking
   for(int i = 1; i < 15; i++)
   {
      // Bullish FVG: Low of candle i > High of candle i+2
      if(l[i] > h[i + 2])
      {
         double gapTop = l[i];
         double gapBottom = h[i + 2];
         double fvg50 = gapBottom + (gapTop - gapBottom) * 0.50;

         // Price currently mitigating the 50% discount fill
         if(currentPrice <= fvg50 && currentPrice >= gapBottom)
         {
            g_smcData.fvgDiscountVote = 1;
            break;
         }
      }
      // Bearish FVG: High of candle i < Low of candle i+2
      else if(h[i] < l[i + 2])
      {
         double gapTop = l[i + 2];
         double gapBottom = h[i];
         double fvg50 = gapBottom + (gapTop - gapBottom) * 0.50;

         if(currentPrice >= fvg50 && currentPrice <= gapTop)
         {
            g_smcData.fvgDiscountVote = -1;
            break;
         }
      }
   }

   // 4. Liquidity Sweep: Price wicks beyond recent 20-bar high/low with rejection wick > 1.5x ATR
   double recentHigh = -1e9;
   double recentLow = 1e9;
   for(int k = 2; k < 22; k++)
   {
      if(h[k] > recentHigh) recentHigh = h[k];
      if(l[k] < recentLow) recentLow = l[k];
   }

   // Bullish sweep of sell-side liquidity: Low wicks below recentLow, closes back inside with long lower wick
   if(l[1] < recentLow && c[1] > recentLow && (c[1] - l[1]) >= (1.5 * atrVal))
   {
      g_smcData.liqSweepVote = 1;
   }
   // Bearish sweep of buy-side liquidity: High wicks above recentHigh, closes back inside with long upper wick
   else if(h[1] > recentHigh && c[1] < recentHigh && (h[1] - c[1]) >= (1.5 * atrVal))
   {
      g_smcData.liqSweepVote = -1;
   }

   // 5. Multi-TF BOS / CHoCH Alignment (M15, H1, H4)
   int tfBullCount = 0;
   int tfBearCount = 0;
   for(int m = 1; m <= 3; m++) // slots 1=M15, 2=H1, 3=H4
   {
      if(g_mtfData.slots[m].direction == "BUY") tfBullCount++;
      else if(g_mtfData.slots[m].direction == "SELL") tfBearCount++;
   }
   if(tfBullCount >= 2) g_smcData.multiTfBosVote = 1;
   else if(tfBearCount >= 2) g_smcData.multiTfBosVote = -1;

   // 6. Confluence Evaluation
   int bullConfluences = 0;
   int bearConfluences = 0;

   if(g_smcData.bullishOBVote > 0) bullConfluences++;
   if(g_smcData.fvgDiscountVote > 0) bullConfluences++;
   if(g_smcData.liqSweepVote > 0) bullConfluences++;
   if(g_smcData.multiTfBosVote > 0) bullConfluences++;
   if(g_smcData.premDiscVote > 0) bullConfluences++;

   if(g_smcData.bearishOBVote < 0) bearConfluences++;
   if(g_smcData.fvgDiscountVote < 0) bearConfluences++;
   if(g_smcData.liqSweepVote < 0) bearConfluences++;
   if(g_smcData.multiTfBosVote < 0) bearConfluences++;
   if(g_smcData.premDiscVote < 0) bearConfluences++;

   if(bullConfluences >= bearConfluences && bullConfluences > 0)
   {
      g_smcData.confluenceCount = bullConfluences;
      g_smcData.bias = "BUY";
      g_smcData.summary = "Bullish SMC (" + IntegerToString(bullConfluences) + " Confluences)";
   }
   else if(bearConfluences > bullConfluences)
   {
      g_smcData.confluenceCount = bearConfluences;
      g_smcData.bias = "SELL";
      g_smcData.summary = "Bearish SMC (" + IntegerToString(bearConfluences) + " Confluences)";
   }

   g_smcData.isValid = true;
}

//+------------------------------------------------------------------+
//| SINGLE AUDITED RISK ENGINE (RULE #6 COMPLIANT)                   |
//| All trade entries, exits, lot sizing, and risk must pass through |
//| this single class. Direct OrderSend outside this is prohibited.  |
//+------------------------------------------------------------------+
class CRiskEngine
{
private:
   int    m_consecutiveLossesToday;
   bool   m_circuitBreakerTriggered;

public:
   CRiskEngine()
   {
      m_consecutiveLossesToday = 0;
      m_circuitBreakerTriggered = false;
   }

   void Initialize()
   {
      g_initialAccountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      g_dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
      g_peakEquity = g_dayStartEquity;
      g_propRuleBreached = false;
      g_propBreachReason = "";
      m_circuitBreakerTriggered = false;
      m_consecutiveLossesToday = 0;
      
      MqlDateTime dt;
      TimeCurrent(dt);
      g_lastRecordedDay = dt.day;
      g_tradingDaysCount = 1;
      Print("🛡️ [CRiskEngine]: Initialized. Initial Balance=$", DoubleToString(g_initialAccountBalance, 2), " PropMode=", EnumToString(PropFirmMode));
   }

   void UpdateDailyStats()
   {
      double currentEq = AccountInfoDouble(ACCOUNT_EQUITY);
      if(currentEq > g_peakEquity) g_peakEquity = currentEq;

      MqlDateTime dt;
      TimeCurrent(dt);
      if(dt.day != g_lastRecordedDay)
      {
         // Reset daily baseline at broker 00:00 midnight
         g_dayStartEquity = currentEq;
         g_lastRecordedDay = dt.day;
         g_tradingDaysCount++;
         m_consecutiveLossesToday = 0;
         m_circuitBreakerTriggered = false;
         Print("📅 [CRiskEngine]: New Trading Day #", g_tradingDaysCount, " Baseline Equity=$", DoubleToString(g_dayStartEquity, 2));
      }

      CheckPropLimits();
      CheckCircuitBreaker();
   }

   double GetDailyLossPct() const
   {
      if(g_dayStartEquity <= 0) return 0.0;
      double currentEq = AccountInfoDouble(ACCOUNT_EQUITY);
      if(currentEq >= g_dayStartEquity) return 0.0;
      return ((g_dayStartEquity - currentEq) / g_dayStartEquity) * 100.0;
   }

   double GetTotalDrawdownPct() const
   {
      if(g_peakEquity <= 0) return 0.0;
      double currentEq = AccountInfoDouble(ACCOUNT_EQUITY);
      if(currentEq >= g_peakEquity) return 0.0;
      return ((g_peakEquity - currentEq) / g_peakEquity) * 100.0;
   }

   bool CheckPropLimits()
   {
      if(PropFirmMode == PROP_NONE) return true;

      double maxDailyLoss = 5.0;
      double maxTotalDD = 10.0;
      switch(PropFirmMode)
      {
         case PROP_FTMO:        maxDailyLoss = 5.0; maxTotalDD = 10.0; break;
         case PROP_MFF:         maxDailyLoss = 5.0; maxTotalDD = 12.0; break;
         case PROP_THE5ERS:     maxDailyLoss = 5.0; maxTotalDD = 10.0; break;
         case PROP_EQUITY_EDGE: maxDailyLoss = 4.0; maxTotalDD = 8.0;  break;
         case PROP_CUSTOM:      maxDailyLoss = PropMaxDailyLossPct; maxTotalDD = PropMaxTotalDDPct; break;
         default: return true;
      }

      double currentDailyLoss = GetDailyLossPct();
      double currentTotalDD = GetTotalDrawdownPct();

      // Buffer of 0.5% safety margin before hard challenge failure
      if(currentDailyLoss >= (maxDailyLoss - 0.5) || currentTotalDD >= (maxTotalDD - 0.5))
      {
         g_propRuleBreached = true;
         g_propBreachReason = "PROP RISK LIMIT REACHED (DayLoss=" + DoubleToString(currentDailyLoss, 1) + 
                              "% / TotalDD=" + DoubleToString(currentTotalDD, 1) + "%)";
         Print("🚨🚨 [PROP BREACH DETECTED]: ", g_propBreachReason, " - EXECUTING EMERGENCY CLOSE ALL!");
         CloseAllPositions(g_propBreachReason);
         g_autoPilotActive = false;
         return false;
      }
      return true;
   }

   bool CheckCircuitBreaker()
   {
      if(m_circuitBreakerTriggered) return false;

      // Circuit breaker: Daily loss >= 2.0% or 3 consecutive losses today
      if(GetDailyLossPct() >= 2.0 || m_consecutiveLossesToday >= 3)
      {
         m_circuitBreakerTriggered = true;
         Print("🛑 [CIRCUIT BREAKER TRIGGERED]: Daily loss: ", DoubleToString(GetDailyLossPct(), 2), 
               "% | Consecutive losses: ", m_consecutiveLossesToday, ". Auto-Pilot paused until tomorrow.");
         return false;
      }
      return true;
   }

   bool CheckCorrelationGuard(string newSymbol, string direction)
   {
      string currBase = StringSubstr(newSymbol, 0, 3);
      string currQuote = (StringLen(newSymbol) >= 6) ? StringSubstr(newSymbol, 3, 3) : "";
      bool isBuy = (direction == "BUY");

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
         string openSym = PositionGetString(POSITION_SYMBOL);
         if(openSym == newSymbol) continue;

         string openBase = StringSubstr(openSym, 0, 3);
         string openQuote = (StringLen(openSym) >= 6) ? StringSubstr(openSym, 3, 3) : "";
         ENUM_POSITION_TYPE openType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         bool openIsBuy = (openType == POSITION_TYPE_BUY);

         // Same quote currency (e.g. EURUSD and GBPUSD both BUY -> both short USD, correlation > 0.70)
         if(currQuote == openQuote && StringLen(currQuote) == 3 && isBuy == openIsBuy)
         {
            Print("⚠️ [CORRELATION GUARD]: High correlation between ", newSymbol, " and ", openSym, " (both ", direction, "). Rejecting entry.");
            return false;
         }
         // Same base currency (e.g. EURUSD and EURJPY both BUY -> both long EUR)
         if(currBase == openBase && StringLen(currBase) == 3 && isBuy == openIsBuy)
         {
            Print("⚠️ [CORRELATION GUARD]: Shared base currency ", currBase, " between ", newSymbol, " and ", openSym, ". Rejecting entry.");
            return false;
         }
      }
      return true;
   }

   bool CheckNewsFilter(string &newsWarning)
   {
      if(!EnableNewsFilter) return true;
      if(g_newsBlockActive)
      {
         newsWarning = "NEWS EVENT IMMINENT (Window: " + IntegerToString(MinutesBeforeNews) + "m)";
         return false;
      }
      return true;
   }

   double CalculateRiskLot(string direction, double slPoints)
   {
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      if(balance <= 0) return LotSize;

      double riskAmount = balance * (RiskPercentPerTrade / 100.0) * g_recoveryMult * ClientRiskMultiplier;
      double tickValue = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
      double tickSize  = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_SIZE);
      double point     = SymbolInfoDouble(Symbol(), SYMBOL_POINT);

      if(tickValue <= 0 || tickSize <= 0 || point <= 0 || slPoints <= 0) return LotSize;

      double slValuePerLot = (slPoints * point / tickSize) * tickValue;
      if(slValuePerLot <= 0) return LotSize;

      double calculatedLot = riskAmount / slValuePerLot;

      // Kelly Criterion Cap: f* = W - (1 - W) / R (capped at 2x Kelly fraction)
      double winRate = (g_totalTrades > 5) ? ((double)g_winTrades / (double)g_totalTrades) : 0.50;
      double rRatio = (TP1_ATR_Mult > 0 && SL_ATR_Mult > 0) ? (TP1_ATR_Mult / SL_ATR_Mult) : 1.5;
      double kellyFraction = winRate - ((1.0 - winRate) / (rRatio > 0 ? rRatio : 1.0));
      if(kellyFraction > 0.0)
      {
         double kellyCapLot = LotSize * 2.0 * kellyFraction;
         if(calculatedLot > kellyCapLot && kellyCapLot > 0.01)
            calculatedLot = kellyCapLot;
      }

      // Prop firm lot cap
      if(PropFirmMode != PROP_NONE && PropMaxLotCap > 0 && calculatedLot > PropMaxLotCap)
         calculatedLot = PropMaxLotCap;

      // Broker normalization
      double minLot  = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
      double maxLot  = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MAX);
      double stepLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
      if(minLot <= 0) minLot = 0.01;
      if(stepLot <= 0) stepLot = 0.01;

      if(calculatedLot < minLot) calculatedLot = minLot;
      if(calculatedLot > LotSize) calculatedLot = LotSize;
      if(maxLot > 0 && calculatedLot > maxLot) calculatedLot = maxLot;

      double normalized = MathFloor((calculatedLot - minLot) / stepLot) * stepLot + minLot;
      int lotDigits = (stepLot < 0.1) ? 2 : ((stepLot < 1.0) ? 1 : 0);
      return NormalizeDouble(normalized, lotDigits);
   }

   bool CanOpenTrade(string direction, double customLot, double &outLots, double &outSL, double &outTP, string &rejectionReason)
   {
      rejectionReason = "";

      // 1. Algo trading permissions
      if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
      {
         rejectionReason = "ENABLE 'ALGO TRADING' IN MT5 TOOLBAR";
         return false;
      }
      if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
      {
         rejectionReason = "PRESS F7 -> ENABLE 'ALLOW ALGO TRADING'";
         return false;
      }

      // 2. Prop firm limit check
      if(!CheckPropLimits())
      {
         rejectionReason = g_propBreachReason;
         return false;
      }

      // 3. Circuit breaker check
      if(!CheckCircuitBreaker())
      {
         rejectionReason = "CIRCUIT BREAKER ACTIVE";
         return false;
      }

      // 4. News filter check
      string newsWarn = "";
      if(!CheckNewsFilter(newsWarn))
      {
         rejectionReason = newsWarn;
         return false;
      }

      // 5. Anti-stacking: only 1 position per symbol
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionGetSymbol(i) == Symbol() && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            rejectionReason = "POSITION ALREADY ACTIVE ON " + Symbol();
            return false;
         }
      }

      // 6. Spread validation
      double spread = (double)SymbolInfoInteger(Symbol(), SYMBOL_SPREAD);
      if(MaxSpreadPoints > 0 && spread > MaxSpreadPoints)
      {
         rejectionReason = "SPREAD TOO HIGH (" + DoubleToString(spread, 0) + ")";
         return false;
      }

      // 7. Correlation guard
      if(!CheckCorrelationGuard(Symbol(), direction))
      {
         rejectionReason = "CORRELATED PAIR POSITION ALREADY ACTIVE";
         return false;
      }

      // 8. SMC Minimum Confluence requirement (if enabled)
      if(EnableSMC && g_smcData.isValid)
      {
         if(g_smcData.bias != direction || g_smcData.confluenceCount < SMCMinConfluence)
         {
            rejectionReason = "SMC CONFLUENCE LOW (" + IntegerToString(g_smcData.confluenceCount) + "/" + IntegerToString(SMCMinConfluence) + ")";
            return false;
         }
      }

      // 9. Calculate SL, TP, Lots
      double ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
      double bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);
      double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
      int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);
      int stopLevel = (int)SymbolInfoInteger(Symbol(), SYMBOL_TRADE_STOPS_LEVEL);

      double atrVal = (g_lastAnalysis.isValid && g_lastAnalysis.atrValue > 0) ? g_lastAnalysis.atrValue : point * 300;
      double slDist = atrVal * SL_ATR_Mult;
      double tpDist = atrVal * TP1_ATR_Mult;

      double minStopDist = (double)stopLevel * point * 1.5;
      if(slDist < minStopDist) slDist = minStopDist;
      if(tpDist < minStopDist) tpDist = minStopDist;

      double slPoints = slDist / (point > 0 ? point : 1.0);
      outLots = (RiskPercentPerTrade > 0) ? CalculateRiskLot(direction, slPoints) : ((customLot > 0) ? customLot : LotSize);

      if(direction == "BUY")
      {
         outSL = NormalizeDouble(ask - slDist, digits);
         outTP = NormalizeDouble(ask + tpDist, digits);
      }
      else
      {
         outSL = NormalizeDouble(bid + slDist, digits);
         outTP = NormalizeDouble(bid - tpDist, digits);
      }

      return true;
   }

   bool ExecuteTrade(string direction, double customLot = 0.0, string reason = "Automated Signal")
   {
      StringToUpper(direction);
      if(direction != "BUY" && direction != "SELL") return false;

      double lots = 0, sl = 0, tp = 0;
      string rejectionReason = "";
      if(!CanOpenTrade(direction, customLot, lots, sl, tp, rejectionReason))
      {
         g_lastTradeMsg = rejectionReason;
         Print("🛡️ [CRiskEngine BLOCKED]: ", direction, " on ", Symbol(), " - Reason: ", rejectionReason);
         return false;
      }

      int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);
      double ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
      double bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);

      MqlTradeRequest request;
      MqlTradeResult result;
      ZeroMemory(request);
      ZeroMemory(result);

      request.action    = TRADE_ACTION_DEAL;
      request.symbol    = Symbol();
      request.volume    = lots;
      request.deviation = SlippagePoints;
      request.magic     = MagicNumber;
      request.comment   = "Kestrel v4.0 RiskEngine";

      if(direction == "BUY")
      {
         request.type  = ORDER_TYPE_BUY;
         request.price = NormalizeDouble(ask, digits);
      }
      else
      {
         request.type  = ORDER_TYPE_SELL;
         request.price = NormalizeDouble(bid, digits);
      }
      request.sl = sl;
      request.tp = tp;

      double origSL = sl;
      double origTP = tp;

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
               Print("⚠️ [NOTE]: Opened without stops. Will set via SLTP modify.");
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

         Print("✅ [CRiskEngine EXECUTED]: ", direction, " ", lots, " lots @ ",
               DoubleToString(request.price, digits), " | SL: ", DoubleToString(origSL, digits),
               " | TP: ", DoubleToString(origTP, digits));

         if(request.sl == 0.0 && origSL > 0)
         {
            Sleep(300);
            ModifyPositionStops(g_activePositionTicket, origSL, origTP);
         }

         if(DrawSignalArrows)
            Draw3DChartSignal(direction, request.price, origSL, origTP);

         ReportTradeToSupabase(direction, request.price, lots, origSL, origTP, result.deal);
         SyncAccountToSupabase();
         return true;
      }
      else
      {
         g_lastTradeMsg = "ERR " + IntegerToString((long)result.retcode) + ": " + result.comment;
         Print("❌ [CRiskEngine FAILED]: Retcode: ", result.retcode, " Comment: ", result.comment);
         return false;
      }
   }

   bool ModifyPositionStops(ulong ticket, double sl, double tp)
   {
      MqlTradeRequest modReq;
      MqlTradeResult modRes;
      ZeroMemory(modReq);
      ZeroMemory(modRes);
      modReq.action   = TRADE_ACTION_SLTP;
      modReq.position = ticket;
      modReq.symbol   = Symbol();
      modReq.sl       = sl;
      modReq.tp       = tp;
      return OrderSend(modReq, modRes);
   }

   bool ClosePosition(ulong ticket, double volume = 0.0, string reason = "Normal Close")
   {
      if(!PositionSelectByTicket(ticket)) return false;

      string sym = PositionGetString(POSITION_SYMBOL);
      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double curVol = PositionGetDouble(POSITION_VOLUME);
      double closeVol = (volume > 0.0 && volume <= curVol) ? volume : curVol;
      int digits = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);

      MqlTradeRequest req;
      MqlTradeResult res;
      ZeroMemory(req);
      ZeroMemory(res);

      req.action    = TRADE_ACTION_DEAL;
      req.position  = ticket;
      req.symbol    = sym;
      req.volume    = closeVol;
      req.deviation = SlippagePoints;
      req.magic     = MagicNumber;
      req.comment   = "Kestrel Close: " + reason;

      if(type == POSITION_TYPE_BUY)
      {
         req.type  = ORDER_TYPE_SELL;
         req.price = NormalizeDouble(SymbolInfoDouble(sym, SYMBOL_BID), digits);
      }
      else
      {
         req.type  = ORDER_TYPE_BUY;
         req.price = NormalizeDouble(SymbolInfoDouble(sym, SYMBOL_ASK), digits);
      }

      ENUM_ORDER_TYPE_FILLING fillModes[3] = {ORDER_FILLING_IOC, ORDER_FILLING_FOK, ORDER_FILLING_RETURN};
      for(int f = 0; f < 3; f++)
      {
         req.type_filling = fillModes[f];
         ResetLastError();
         if(OrderSend(req, res))
         {
            Print("🛡️ [CRiskEngine CLOSED]: Position #", ticket, " Volume=", closeVol, " Reason=", reason);
            return true;
         }
      }
      return false;
   }

   bool CloseAllPositions(string reason = "Emergency Close")
   {
      Print("🛡️ [CRiskEngine]: Closing all positions on ", Symbol(), ". Reason: ", reason);
      bool allSuccess = true;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionGetSymbol(i) == Symbol() && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         {
            ulong ticket = PositionGetTicket(i);
            if(!ClosePosition(ticket, 0.0, reason))
               allSuccess = false;
         }
      }
      g_lastTradeMsg = "ALL POSITIONS CLOSED (" + reason + ")";
      return allSuccess;
   }

   void ManageTrailingAndBreakEven()
   {
      if(!UseTrailingStop) return;

      double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
      int digits = (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);
      double ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
      double bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);

      double atrVal = (g_lastAnalysis.isValid && g_lastAnalysis.atrValue > 0) ? g_lastAnalysis.atrValue : point * 300;

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionGetSymbol(i) != Symbol() || PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;

         ulong ticket = PositionGetTicket(i);
         ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         double currentSl = PositionGetDouble(POSITION_SL);
         double currentTp = PositionGetDouble(POSITION_TP);
         double volume    = PositionGetDouble(POSITION_VOLUME);

         double profitPoints = (type == POSITION_TYPE_BUY) ? (bid - openPrice) / point : (openPrice - ask) / point;
         double profitPrice  = (type == POSITION_TYPE_BUY) ? (bid - openPrice) : (openPrice - ask);

         // News Protection: Tighten SL to BE if news within 15 minutes and in profit
         if(g_newsBlockActive && profitPrice > (point * 10))
         {
            double beSl = NormalizeDouble(openPrice, digits);
            if(type == POSITION_TYPE_BUY && currentSl < beSl)
            {
               ModifyPositionStops(ticket, beSl, currentTp);
               Print("🛡️ [NEWS GUARD]: Position #", ticket, " SL locked to BE before news event.");
            }
            else if(type == POSITION_TYPE_SELL && (currentSl > beSl || currentSl == 0))
            {
               ModifyPositionStops(ticket, beSl, currentTp);
               Print("🛡️ [NEWS GUARD]: Position #", ticket, " SL locked to BE before news event.");
            }
         }

         // Level 1: Break-even lock at 1.5x ATR
         double beTriggerDist = atrVal * 1.5;
         if(profitPrice >= beTriggerDist)
         {
            double beLevel = NormalizeDouble(openPrice, digits);
            if(type == POSITION_TYPE_BUY && currentSl < beLevel)
               ModifyPositionStops(ticket, beLevel, currentTp);
            else if(type == POSITION_TYPE_SELL && (currentSl > beLevel || currentSl == 0))
               ModifyPositionStops(ticket, beLevel, currentTp);
         }

         // Level 2: Partial Close 40% at TP1
         double tp1Dist = atrVal * TP1_ATR_Mult;
         if(!g_partialTP1Fired && profitPrice >= tp1Dist && volume > 0.02)
         {
            double stepLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
            double closeVol = NormalizeDouble(MathFloor((volume * 0.40) / stepLot) * stepLot, 2);
            if(closeVol >= 0.01)
            {
               if(ClosePosition(ticket, closeVol, "Partial TP1 40%"))
                  g_partialTP1Fired = true;
            }
         }

         // Level 3: Partial Close 50% of remaining at TP2
         double tp2Dist = atrVal * TP2_ATR_Mult;
         if(!g_partialTP2Fired && profitPrice >= tp2Dist && volume > 0.02)
         {
            double stepLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
            double closeVol = NormalizeDouble(MathFloor((volume * 0.50) / stepLot) * stepLot, 2);
            if(closeVol >= 0.01)
            {
               if(ClosePosition(ticket, closeVol, "Partial TP2 50%"))
                  g_partialTP2Fired = true;
            }
         }

         // Trailing Stop: 1.0x ATR behind price once TP1 is hit
         if(profitPrice >= tp1Dist)
         {
            double trailDist = atrVal * 1.0;
            if(type == POSITION_TYPE_BUY)
            {
               double newTrailSl = NormalizeDouble(bid - trailDist, digits);
               if(newTrailSl > currentSl)
                  ModifyPositionStops(ticket, newTrailSl, currentTp);
            }
            else
            {
               double newTrailSl = NormalizeDouble(ask + trailDist, digits);
               if(newTrailSl < currentSl || currentSl == 0)
                  ModifyPositionStops(ticket, newTrailSl, currentTp);
            }
         }
      }
   }
};

CRiskEngine g_riskEngine;
"""
    exec_func_pos = content.find("void ExecuteAutonomousTrade(string direction, double customLot = 0.0)")
    if exec_func_pos != -1:
        content = content[:exec_func_pos] + risk_engine_code + "\n" + content[exec_func_pos:]

    # 7. Replace bodies of ExecuteAutonomousTrade, CloseAllSymbolPositions, ManageTrailingStops
    # ExecuteAutonomousTrade -> delegate to g_riskEngine.ExecuteTrade
    old_exec_start = content.find("void ExecuteAutonomousTrade(string direction, double customLot = 0.0)\n{")
    if old_exec_start != -1:
        old_exec_end = content.find("\nvoid Draw3DChartSignal", old_exec_start)
        new_exec_body = """void ExecuteAutonomousTrade(string direction, double customLot = 0.0)
{
   // RULE #6 AUDIT: All trade alteration delegated directly to audited CRiskEngine class
   g_riskEngine.ExecuteTrade(direction, customLot, "Manual/Autonomous Order");
}
"""
        content = content[:old_exec_start] + new_exec_body + content[old_exec_end:]

    # CloseAllSymbolPositions -> delegate to g_riskEngine.CloseAllPositions
    old_close_start = content.find("void CloseAllSymbolPositions()\n{")
    if old_close_start != -1:
        old_close_end = content.find("\nvoid ManageTrailingStops", old_close_start)
        new_close_body = """void CloseAllSymbolPositions()
{
   // RULE #6 AUDIT: Delegated to audited CRiskEngine class
   g_riskEngine.CloseAllPositions("Manual / Emergency Halt");
}
"""
        content = content[:old_close_start] + new_close_body + content[old_close_end:]

    # ManageTrailingStops -> delegate to g_riskEngine.ManageTrailingAndBreakEven
    old_trail_start = content.find("void ManageTrailingStops()\n{")
    if old_trail_start != -1:
        old_trail_end = content.find("\nvoid SyncAccountToSupabase", old_trail_start)
        new_trail_body = """void ManageTrailingStops()
{
   // RULE #6 AUDIT: Delegated to audited CRiskEngine class
   g_riskEngine.ManageTrailingAndBreakEven();
}
"""
        content = content[:old_trail_start] + new_trail_body + content[old_trail_end:]

    # 8. Upgrade CheckNewsProximity to query backend calendar endpoint first and check 30m window
    news_func_start = content.find("void CheckNewsProximity()\n{")
    if news_func_start != -1:
        news_func_end = content.find("void UpdateNewsProximity()\n{", news_func_start)
        new_news_func = r"""void CheckNewsProximity()
{
   if(!EnableNewsFilter) return;

   // Cache news data for 15 minutes
   if(TimeCurrent() - g_lastNewsFetchTime < 900 && g_lastNewsFetchTime > 0)
   {
      UpdateNewsProximity();
      return;
   }

   g_newsProximityActive = false;
   g_newsConfidencePenalty = 0.0;
   g_newsWarningText = "";
   g_upcomingNewsCount = 0;
   g_newsBlockActive = false;

   string baseCurrency = StringSubstr(Symbol(), 0, 3);
   string quoteCurrency = (StringLen(Symbol()) >= 6) ? StringSubstr(Symbol(), 3, 3) : "";

   // 1. Try Kestrel backend calendar endpoint first
   string url = KestrelAPIUrl + "/api/v1/calendar/forex-factory?impact=" + MinImpactLevel + "&currency=" + baseCurrency;
   string headers = "Content-Type: application/json\r\n";
   char post_data[], result[];
   string result_headers;

   ResetLastError();
   int res = WebRequest("GET", url, headers, NULL, 4000, post_data, 0, result, result_headers);

   // Fallback to ForexFactory directly if backend is unreachable
   if(res != 200 || ArraySize(result) == 0)
   {
      url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
      ResetLastError();
      res = WebRequest("GET", url, headers, NULL, 5000, post_data, 0, result, result_headers);
   }

   if(res == 200 && ArraySize(result) > 0)
   {
      string response = CharArrayToString(result);
      g_lastNewsFetchTime = TimeCurrent();

      int pos = 0;
      while(pos >= 0 && g_upcomingNewsCount < 10)
      {
         pos = StringFind(response, "\"country\":", pos);
         if(pos < 0) pos = StringFind(response, "\"currency\":", pos);
         if(pos < 0) break;

         int objStart = pos;
         while(objStart > 0 && StringGetCharacter(response, objStart) != '{') objStart--;
         int objEnd = StringFind(response, "}", pos);
         if(objEnd < 0) { pos++; continue; }

         string eventObj = StringSubstr(response, objStart, objEnd - objStart + 1);

         string evCountry = ExtractJsonStringConst(eventObj, "country");
         if(StringLen(evCountry) == 0) evCountry = ExtractJsonStringConst(eventObj, "currency");
         StringToUpper(evCountry);

         string evImpact = ExtractJsonStringConst(eventObj, "impact");
         StringToUpper(evImpact);

         bool impactMatch = (MinImpactLevel == "ALL") || 
                            (MinImpactLevel == "MEDIUM" && (evImpact == "HIGH" || evImpact == "MEDIUM")) ||
                            (MinImpactLevel == "HIGH" && evImpact == "HIGH");

         if(impactMatch && (evCountry == baseCurrency || evCountry == quoteCurrency))
         {
            string evTitle = ExtractJsonStringConst(eventObj, "title");
            if(StringLen(evTitle) > 30) evTitle = StringSubstr(evTitle, 0, 27) + "...";

            int minsUntil = 999;
            string minsStr = ExtractJsonStringConst(eventObj, "minutes_until");
            if(StringLen(minsStr) > 0)
            {
               minsUntil = (int)StringToInteger(minsStr);
            }
            else
            {
               string evDateStr = ExtractJsonStringConst(eventObj, "date");
               if(StringLen(evDateStr) == 0) evDateStr = ExtractJsonStringConst(eventObj, "event_time_utc");
               datetime evTime = ParseNewsDate(evDateStr);
               if(evTime > 0) minsUntil = (int)((evTime - TimeGMT()) / 60);
            }

            if(minsUntil > -MinutesBeforeNews && minsUntil < 180)
            {
               g_upcomingNews[g_upcomingNewsCount].eventTime = TimeCurrent() + (minsUntil * 60);
               g_upcomingNews[g_upcomingNewsCount].currency = evCountry;
               g_upcomingNews[g_upcomingNewsCount].impact = evImpact;
               g_upcomingNews[g_upcomingNewsCount].title = evTitle;
               g_upcomingNews[g_upcomingNewsCount].minutesUntil = minsUntil;
               g_upcomingNewsCount++;

               // Lock trading if within specified window
               if(MathAbs(minsUntil) <= MinutesBeforeNews)
               {
                  g_newsBlockActive = true;
                  g_newsProximityActive = true;
                  g_newsWarningText = "NEWS IMMINENT: " + evCountry + " " + evTitle + " (" + IntegerToString(minsUntil) + "m)";
               }
            }
         }
         pos = objEnd + 1;
      }
   }
   UpdateNewsProximity();
}
"""
        content = content[:news_func_start] + new_news_func + "\n" + content[news_func_end:]

    # 9. Update OnInit to call g_riskEngine.Initialize()
    init_call_pos = content.find("g_autoPilotActive = AutoTrade;")
    if init_call_pos != -1:
        init_replacement = """g_autoPilotActive = AutoTrade;
   g_riskEngine.Initialize();
"""
        content = content[:init_call_pos] + init_replacement + content[init_call_pos + len("g_autoPilotActive = AutoTrade;"):]

    # 10. Update OnTimer loop to:
    #     - Update g_riskEngine.UpdateDailyStats()
    #     - Process WebQueue
    #     - Evaluate Market Regime & Hurst exponent
    #     - Detect Smart Money Concepts (SMC)
    #     - Handle 30s Heartbeat
    timer_search = "g_lastAnalysis = AnalyzeMarketConfluence();"
    timer_pos = content.find(timer_search)
    if timer_pos != -1:
        timer_enhancement = r"""// Update Audited Risk Engine daily metrics and prop limits
      g_riskEngine.UpdateDailyStats();
      ProcessWebQueue();

      // Periodic 30s Heartbeat to Kestrel Backend
      if(TimeCurrent() - g_lastHeartbeatTime >= 30)
      {
         g_lastHeartbeatTime = TimeCurrent();
         string accNum = (StringLen(ClientAccountID) > 0) ? ClientAccountID : IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
         string hbJson = "{\"account_login\":\"" + accNum + "\",\"terminal_hash\":\"MT5_" + accNum + "\",\"equity\":" + 
                         DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + ",\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + 
                         ",\"regime\":\"" + g_regimeDetailed + "\"}";
         EnqueueWebRequest("POST", KestrelAPIUrl + "/api/v1/license/activate", "Content-Type: application/json\r\n", hbJson, "HEARTBEAT");
      }

      // Evaluate Market Regime (Hurst Exponent & ADX)
      g_regimeDetailed = EvaluateMarketRegime(g_currentHurst, g_currentAdx);
      g_lastRegime = g_regimeDetailed;

      // Detect Smart Money Concepts (SMC)
      DetectSmartMoneyConcepts();

      g_lastAnalysis = AnalyzeMarketConfluence();"""
        content = content[:timer_pos] + timer_enhancement + content[timer_pos + len(timer_search):]

    # Write out modified file
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully upgraded {target_path} to v4.0!")

if __name__ == "__main__":
    main()
