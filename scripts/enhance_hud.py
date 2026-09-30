"""
HUD Enhancements for KestrelEA.mq5 v4.0
Adds Prop-Firm Risk Control Bar, Market Regime Badge, Macro News Guard Countdown, and SMC Confluences to Render3DHUD.
"""
def main():
    target = r"adapters\mt5\KestrelEA.mq5"
    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace header text to v4.0
    content = content.replace('KESTREL INTELLIGENCE ENGINE v5.1', 'KESTREL INSTITUTIONAL ENGINE v4.0')

    # Enhance HUD with Prop-firm status bar, Regime badge, SMC and News alerts
    old_fin_end = """   CreateRectLabel("SEP_2", x + 14, fy + 48, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);

   // ─── 4. MAIN SIGNAL + STAR RATING ───
   int ay = fy + 56;"""

    new_fin_end = """   CreateRectLabel("SEP_2", x + 14, fy + 48, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);

   // ─── PROP FIRM & RISK CONTROL BAR ───
   int py = fy + 54;
   string propTitle = "PROP-FIRM RISK ENGINE: ";
   switch(PropFirmMode)
   {
      case PROP_FTMO:        propTitle += "FTMO CHALLENGE (5% Day / 10% DD)"; break;
      case PROP_MFF:         propTitle += "MYFOREXFUNDS (5% Day / 12% DD)"; break;
      case PROP_THE5ERS:     propTitle += "THE 5%ERS (5% Day / 10% DD)"; break;
      case PROP_EQUITY_EDGE: propTitle += "EQUITY EDGE (4% Day / 8% DD)"; break;
      case PROP_CUSTOM:      propTitle += "CUSTOM LIMITS (" + DoubleToString(PropMaxDailyLossPct, 1) + "% / " + DoubleToString(PropMaxTotalDDPct, 1) + "%)"; break;
      default:               propTitle += "UNRESTRICTED (Personal Account)"; break;
   }
   CreateLabel("LBL_PROP_TITLE", propTitle, x + 16, py, "Segoe UI Bold", 7, C'130,150,180');

   double dLoss = g_riskEngine.GetDailyLossPct();
   double tDD   = g_riskEngine.GetTotalDrawdownPct();
   color propColor = C'0,255,136';
   if(dLoss >= 3.5 || tDD >= 8.0) propColor = C'255,34,85';
   else if(dLoss >= 2.0 || tDD >= 5.0) propColor = C'255,200,0';

   string propStats = "Day Loss: " + DoubleToString(dLoss, 2) + "% | Max DD: " + DoubleToString(tDD, 2) + 
                      "% | Status: " + (g_propRuleBreached ? "🚨 BREACHED" : (g_riskEngine.IsCircuitBreakerActive() ? "🛑 CIRCUIT TRIPPED" : "🟢 ARMED"));
   CreateLabel("LBL_PROP_METRICS", propStats, x + 16, py + 14, "Consolas", 7, propColor);

   // Progress bar for daily loss
   int barW = panelW - 32;
   CreateRectLabel("PROP_BAR_BG", x + 16, py + 28, barW, 4, C'20,30,45', C'20,30,45', 1);
   int fillW = (int)MathMin(barW, MathMax(2, (dLoss / 5.0) * barW));
   CreateRectLabel("PROP_BAR_FILL", x + 16, py + 28, fillW, 4, propColor, propColor, 1);

   CreateRectLabel("SEP_PROP", x + 14, py + 38, panelW - 28, 1, C'30,42,65', C'30,42,65', 1);

   // ─── 4. MAIN SIGNAL + STAR RATING ───
   int ay = py + 46;"""

    if old_fin_end in content:
        content = content.replace(old_fin_end, new_fin_end)

    old_score = """   int maxExpected = EnableCandleAnalysis ? 9 : 8;
   string scoreText = "Score: " + DoubleToString(g_lastAnalysis.score, 3) +
                      " | " + IntegerToString(g_lastAnalysis.indicatorsAvailable) + "/" + IntegerToString(maxExpected) + " Ind" +
                      " | " + g_lastRegime + " | " + strength;
   CreateLabel("LBL_ANA_SCORE", scoreText, x + 16, ay + 36, "Segoe UI", 7, C'170,185,210');"""

    new_score = """   int maxExpected = EnableCandleAnalysis ? 9 : 8;
   string scoreText = "Score: " + DoubleToString(g_lastAnalysis.score, 3) +
                      " | " + IntegerToString(g_lastAnalysis.indicatorsAvailable) + "/" + IntegerToString(maxExpected) + " Ind" +
                      " | " + strength;
   CreateLabel("LBL_ANA_SCORE", scoreText, x + 16, ay + 36, "Segoe UI", 7, C'170,185,210');

   // Color-coded Market Regime Switcher Badge
   color regColor = C'170,185,210';
   if(g_currentHurst > HurstTrendThreshold) regColor = C'0,255,136';
   else if(g_currentHurst < HurstMeanRevThreshold) regColor = C'0,229,255';
   CreateLabel("LBL_REGIME_BADGE", "🌐 REGIME: " + g_regimeDetailed, x + 16, ay + 48, "Segoe UI Bold", 7, regColor);

   // News Guard Countdown & Status
   if(g_newsBlockActive)
   {
      CreateLabel("LBL_NEWS_LOCK", "⚠️ [LOCK] " + g_newsWarningText, x + 16, ay + 60, "Segoe UI Bold", 7, C'255,50,50');
   }
   else if(g_upcomingNewsCount > 0)
   {
      CreateLabel("LBL_NEWS_LOCK", "📰 " + g_upcomingNews[0].currency + ": " + g_upcomingNews[0].title + " in " + IntegerToString(g_upcomingNews[0].minutesUntil) + "m", x + 16, ay + 60, "Segoe UI", 7, C'150,175,205');
   }

   // Smart Money Concepts (SMC) Confluence Summary
   if(EnableSMC && g_smcData.isValid)
   {
      color smcCol = (g_smcData.bias == "BUY") ? C'0,255,136' : ((g_smcData.bias == "SELL") ? C'255,34,85' : C'255,200,0');
      string smcSummary = "🦅 SMC: " + g_smcData.summary + " | Zone: " + (g_smcData.premDiscVote > 0 ? "DISCOUNT (Buy Bias)" : "PREMIUM (Sell Bias)");
      CreateLabel("LBL_SMC_SUMMARY", smcSummary, x + 16, ay + 72, "Segoe UI Bold", 7, smcCol);
   }"""

    if old_score in content:
        content = content.replace(old_score, new_score)
        content = content.replace('x + 16, ay + 50', 'x + 16, ay + 86')
        content = content.replace('x + 14, ay + 64', 'x + 14, ay + 100')
        content = content.replace('int cndY = ay + 72;', 'int cndY = ay + 108;')

    with open(target, 'w', encoding='utf-8') as f:
        f.write(content)

    print("HUD enhanced successfully!")

if __name__ == "__main__":
    main()
