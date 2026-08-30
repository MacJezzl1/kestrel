"""
Kestrel Quantum Trading Intelligence — Institutional PDF Generator
Generates a publication-grade multi-page investor & client PDF brochure.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Top gradient accent bar
        self.setFillColor(colors.HexColor('#00e5ff'))
        self.rect(36, letter[1] - 20, letter[0] - 72, 3, fill=1, stroke=0)
        
        # Header text
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor('#94a3b8'))
        self.drawString(36, letter[1] - 32, "KESTREL QUANTUM TRADING INTELLIGENCE")
        self.drawRightString(letter[0] - 36, letter[1] - 32, "OFFICIAL INSTITUTIONAL DECK 2026")

        # Footer line
        self.setStrokeColor(colors.HexColor('#1e293b'))
        self.setLineWidth(0.75)
        self.line(36, 35, letter[0] - 36, 35)

        # Footer text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawString(36, 24, "CONFIDENTIAL & PROPRIETARY | KESTREL SWARM AI ECOSYSTEM")
        self.drawRightString(letter[0] - 36, 24, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    COLOR_PRIMARY = colors.HexColor('#060a14')
    COLOR_CYAN = colors.HexColor('#00e5ff')
    COLOR_EMERALD = colors.HexColor('#00ff88')
    COLOR_GOLD = colors.HexColor('#f59e0b')
    COLOR_TEXT = colors.HexColor('#0f172a')
    COLOR_MUTED = colors.HexColor('#475569')
    COLOR_CARD_BG = colors.HexColor('#f8fafc')
    COLOR_BORDER = colors.HexColor('#cbd5e1')
    COLOR_DARK_BG = colors.HexColor('#0f172a')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=COLOR_PRIMARY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=COLOR_PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0f766e'),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=COLOR_TEXT,
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=COLOR_TEXT,
        alignment=1
    )

    table_cell_left = ParagraphStyle(
        'TableCellLeft',
        parent=table_cell_style,
        alignment=0
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # ==========================================
    # PAGE 1: TITLE, EXECUTIVE SUMMARY & PAMM TIERS
    # ==========================================
    story.append(Paragraph("KESTREL QUANTUM TRADING INTELLIGENCE", title_style))
    story.append(Paragraph("Autonomous 120-AI Swarm • Multi-Client PAMM Copy-Trading • Deriv Synthetic & Global Markets", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_CYAN, spaceBefore=0, spaceAfter=10))

    # Executive Overview
    overview_text = (
        "<b>Kestrel Quantum Trading Intelligence</b> is an institutional-grade algorithmic trading ecosystem engineered "
        "to trade Deriv Continuous & 1s Synthetic Indices (Crash, Boom, Volatility 10–250 1s, Step, Jump), Forex, "
        "Metals (Gold/Silver), Crypto, and Global Indices. Powered by a <b>120-AI Quantum Consensus Swarm</b> spanning 6 quant "
        "domains, Kestrel computes Bayesian market confluence in sub-millisecond cycles to execute high-conviction trades "
        "with automated capital preservation."
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 8))

    # Highlights Banner Table
    banner_data = [
        [
            Paragraph("<b>120 AI Models</b><br/><font size=7 color='#64748b'>6 Specialized Swarms</font>", table_cell_bold),
            Paragraph("<b>Sub-40ms Sync</b><br/><font size=7 color='#64748b'>Cloud Web to MT5 Bridge</font>", table_cell_bold),
            Paragraph("<b>100% Target Return</b><br/><font size=7 color='#64748b'>Monthly PAMM Target</font>", table_cell_bold),
            Paragraph("<b>Level 1 & 2 Shield</b><br/><font size=7 color='#64748b'>Auto-BE + 50% Partial TP</font>", table_cell_bold),
        ]
    ]
    banner_table = Table(banner_data, colWidths=[135, 135, 135, 135])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#86efac')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbf7d0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 12))

    # SECTION 1: PAMM MANAGED COPY-TRADING PLANS
    story.append(Paragraph("1. MANAGED COPY-TRADING & PAMM INVESTMENT PLANS", h1_style))
    story.append(Paragraph(
        "Our professional trading team manages client capital through our high-precision PAMM Multi-Client Copy-Trading "
        "engine. Client accounts start from <b>$110</b>, scaling to institutional sizes with proportional risk allocation.",
        body_style
    ))
    story.append(Spacer(1, 4))

    pamm_data = [
        [
            Paragraph("TIER / PLAN", table_header_style),
            Paragraph("MIN DEPOSIT", table_header_style),
            Paragraph("MONTHLY TARGET", table_header_style),
            Paragraph("PROFIT SPLIT", table_header_style),
            Paragraph("RISK PROFILE & FEATURES", table_header_style),
        ],
        [
            Paragraph("<b>Starter Alpha</b><br/><font color='#0284c7'>Entry Pilot</font>", table_cell_left),
            Paragraph("<b>$110</b>", table_cell_bold),
            Paragraph("<b>100%</b> / Month<br/><font size=6.5 color='#16a34a'>(Target Gain)</font>", table_cell_bold),
            Paragraph("70% Client<br/>30% Performance", table_cell_style),
            Paragraph("1.0x Dynamic ATR Risk • Auto Break-Even Lock at +1.5R • Full MT5 Automation", table_cell_left),
        ],
        [
            Paragraph("<b>Growth Apex</b><br/><font color='#0284c7'>Intermediate</font>", table_cell_left),
            Paragraph("<b>$500 – $2,500</b>", table_cell_bold),
            Paragraph("<b>100%</b> / Month<br/><font size=6.5 color='#16a34a'>(Target Gain)</font>", table_cell_bold),
            Paragraph("75% Client<br/>25% Performance", table_cell_style),
            Paragraph("Level 1 & 2 Smart Partial TP (50% closed at +300 pts) • Live Web Sync", table_cell_left),
        ],
        [
            Paragraph("<b>Pro PAMM</b><br/><font color='#0284c7'>Titanium Fund</font>", table_cell_left),
            Paragraph("<b>$5,000 – $15,000</b>", table_cell_bold),
            Paragraph("<b>100%</b> / Month<br/><font size=6.5 color='#16a34a'>(Target Gain)</font>", table_cell_bold),
            Paragraph("80% Client<br/>20% Performance", table_cell_style),
            Paragraph("Multi-Asset Diversification (Deriv Synthetics + Gold + NAS100) • Dedicated Audit", table_cell_left),
        ],
        [
            Paragraph("<b>Institutional VIP</b><br/><font color='#0284c7'>Zenith Sovereign</font>", table_cell_left),
            Paragraph("<b>$25,000+</b>", table_cell_bold),
            Paragraph("<b>100%+</b> / Month<br/><font size=6.5 color='#16a34a'>(High-Alpha)</font>", table_cell_bold),
            Paragraph("85% Client<br/>15% Performance", table_cell_style),
            Paragraph("Zero-Slippage Dedicated VPS Node • Custom Multiplier Matrix • Direct Master Copy", table_cell_left),
        ]
    ]

    pamm_table = Table(pamm_data, colWidths=[95, 80, 85, 85, 195])
    pamm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#334155')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(pamm_table)
    story.append(Spacer(1, 10))

    # SECTION 2: SOFTWARE LICENSE PRICING TABLE
    story.append(Paragraph("2. STANDALONE SOFTWARE & BOT LICENSE PRICING", h1_style))
    story.append(Paragraph(
        "For traders and funds who prefer running the autonomous EA and Web Terminal on their own MT5 terminals:",
        body_style
    ))
    story.append(Spacer(1, 4))

    lic_data = [
        [
            Paragraph("LICENSE PLAN", table_header_style),
            Paragraph("PRICE", table_header_style),
            Paragraph("BILLING", table_header_style),
            Paragraph("INCLUDED FEATURES & CAPABILITIES", table_header_style),
        ],
        [
            Paragraph("<b>Pro Trader</b>", table_cell_left),
            Paragraph("<b>$110</b>", table_cell_bold),
            Paragraph("Monthly", table_cell_style),
            Paragraph("120-AI Quantum Swarm Signals • MT5 EA v3.50 Bridge • All Deriv Synthetic Markets", table_cell_left),
        ],
        [
            Paragraph("<b>Enterprise VIP</b>", table_cell_left),
            Paragraph("<b>$149</b>", table_cell_bold),
            Paragraph("Monthly", table_cell_style),
            Paragraph("Unlimited Signals • Computer Vision Chart Scanner • Priority Cloud Command Queue", table_cell_left),
        ],
        [
            Paragraph("<b>Lifetime VIP</b><br/><font color='#d97706'>★ BEST VALUE</font>", table_cell_left),
            Paragraph("<b>$1,600</b>", table_cell_bold),
            Paragraph("One-Time Forever", table_cell_bold),
            Paragraph("Permanent Enterprise License • All Future Swarm & EA Upgrades Included Forever • VIP Priority Support", table_cell_left),
        ]
    ]

    lic_table = Table(lic_data, colWidths=[105, 75, 80, 280])
    lic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#334155')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fefce8') if True else colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(lic_table)

    story.append(PageBreak())

    # ==========================================
    # PAGE 2: 120-AI SWARM ARCHITECTURE & MARKETS
    # ==========================================
    story.append(Paragraph("3. 120-AI QUANTUM SWARM INTELLIGENCE ARCHITECTURE", h1_style))
    story.append(Paragraph(
        "Kestrel does not rely on a single lagging indicator. It orchestrates <b>120 specialized quantitative AI models</b> "
        "divided into 6 discrete intelligence categories (20 models each) running parallel Bayesian consensus:",
        body_style
    ))
    story.append(Spacer(1, 4))

    swarm_data = [
        [
            Paragraph("SWARM CATEGORY", table_header_style),
            Paragraph("MODELS", table_header_style),
            Paragraph("QUANTITATIVE METHODOLOGY & ROLE", table_header_style),
        ],
        [
            Paragraph("<b>1. SYNTHETIC DERIV QUANT</b>", table_cell_left),
            Paragraph("20 Models", table_cell_bold),
            Paragraph("Poisson Spike Arrival modeling, 1s Volatility Clustering, Step/Jump Inversion detection, Tick Entropy analytics, and GARCH Regime forecasting tailored for Deriv synthetics.", table_cell_left),
        ],
        [
            Paragraph("<b>2. PRICE ACTION & MICROSTRUCTURE</b>", table_cell_left),
            Paragraph("20 Models", table_cell_bold),
            Paragraph("Institutional Order Block detection, Fair Value Gap (FVG) heatmaps, Buy/Sell-side liquidity pool sweeps, and fractal structure shifts (BOS / CHoCH).", table_cell_left),
        ],
        [
            Paragraph("<b>3. STATISTICAL ARBITRAGE & QUANT</b>", table_cell_left),
            Paragraph("20 Models", table_cell_bold),
            Paragraph("Ornstein-Uhlenbeck mean-reversion, Kalman filter adaptive trends, Hurst exponent persistence testing, and Markov Regime transition probabilities.", table_cell_left),
        ],
        [
            Paragraph("<b>4. MOMENTUM & ORDER FLOW</b>", table_cell_left),
            Paragraph("20 Models", table_cell_bold),
            Paragraph("Volume-Weighted ATR expansion, ADX directional strength, VWAP deviation envelopes, and multi-timeframe RSI momentum vector congruence.", table_cell_left),
        ],
        [
            Paragraph("<b>5. MACROECONOMIC & LIQUIDITY</b>", table_cell_left),
            Paragraph("20 Models", table_cell_bold),
            Paragraph("Global yield curve spreads, DXY liquidity impulse, interest rate differentials, commodity correlation matrices, and central bank policy regime tracking.", table_cell_left),
        ],
        [
            Paragraph("<b>6. SENTIMENT & REASONING</b>", table_cell_left),
            Paragraph("20 Models", table_cell_bold),
            Paragraph("DeepSeek-R1 / Llama 3.3 Bayesian narrative analysis, economic calendar catalyst weighting, risk-on/risk-off sentiment contagion filters.", table_cell_left),
        ]
    ]

    swarm_table = Table(swarm_data, colWidths=[150, 65, 325])
    swarm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#334155')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(swarm_table)
    story.append(Spacer(1, 10))

    # SECTION 4: COMPLETE MARKET SUITE
    story.append(Paragraph("4. COMPLETE GLOBAL & SYNTHETIC ASSET SUITE", h1_style))
    story.append(Paragraph(
        "Kestrel operates continuously 24/7/365 across all global asset classes with asset-specific tick precision:",
        body_style
    ))
    story.append(Spacer(1, 4))

    market_data = [
        [
            Paragraph("ASSET CLASS", table_header_style),
            Paragraph("ACTIVE TRADING INSTRUMENTS", table_header_style),
            Paragraph("SCHEDULE", table_header_style),
        ],
        [
            Paragraph("<b>Deriv Continuous Volatility</b>", table_cell_left),
            Paragraph("Volatility 10 Index, Volatility 25 Index, Volatility 50 Index, Volatility 75 Index, Volatility 100 Index", table_cell_left),
            Paragraph("24/7/365", table_cell_bold),
        ],
        [
            Paragraph("<b>Deriv 1-Second (1s) High-Freq</b>", table_cell_left),
            Paragraph("Volatility 10 (1s), 25 (1s), 50 (1s), 75 (1s), 100 (1s), 150 (1s), 250 (1s)", table_cell_left),
            Paragraph("24/7/365", table_cell_bold),
        ],
        [
            Paragraph("<b>Crash & Boom Spike Hunter</b>", table_cell_left),
            Paragraph("Crash 300, 500, 600, 900, 1000 | Boom 300, 500, 600, 900, 1000 Index", table_cell_left),
            Paragraph("24/7/365", table_cell_bold),
        ],
        [
            Paragraph("<b>Step, Jump & DEX Synthetics</b>", table_cell_left),
            Paragraph("Step Index, Jump 10–100 Indices, DEX 600–1500 Indices", table_cell_left),
            Paragraph("24/7/365", table_cell_bold),
        ],
        [
            Paragraph("<b>Forex & Precious Metals</b>", table_cell_left),
            Paragraph("XAUUSD (Gold), XAGUSD (Silver), EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD", table_cell_left),
            Paragraph("24/5 (Mon–Fri)", table_cell_style),
        ],
        [
            Paragraph("<b>Cryptocurrencies & Indices</b>", table_cell_left),
            Paragraph("BTCUSD, ETHUSD, SOLUSD, XRPUSD | NAS100, US30, SPX500, GER40, UK100", table_cell_left),
            Paragraph("24/7 (Crypto) / 24/5 (Indices)", table_cell_style),
        ]
    ]

    market_table = Table(market_data, colWidths=[140, 320, 80])
    market_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#334155')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(market_table)

    story.append(PageBreak())

    # ==========================================
    # PAGE 3: METATRADER 5 EA V3.50 & SECURITY
    # ==========================================
    story.append(Paragraph("5. METATRADER 5 EA (v3.50) EXECUTION ENGINE", h1_style))
    story.append(Paragraph(
        "The MetaTrader 5 Expert Advisor (<b>KestrelEA v3.50</b>) connects directly to our cloud command queue and "
        "executes trades in sub-millisecond broker fill times with proprietary fail-safe mechanics:",
        body_style
    ))
    story.append(Spacer(1, 4))

    ea_features = [
        [
            Paragraph("FEATURE", table_header_style),
            Paragraph("TECHNICAL SPECIFICATION & BENEFIT", table_header_style),
        ],
        [
            Paragraph("<b>Fail-Safe 3-Pass Auto-Filling</b>", table_cell_left),
            Paragraph("Automatically evaluates and tries <code>ORDER_FILLING_IOC</code>, <code>ORDER_FILLING_FOK</code>, and <code>ORDER_FILLING_RETURN</code> per asset, achieving 100% order fill rates on Deriv without rejection.", table_cell_left),
        ],
        [
            Paragraph("<b>Level 1 Smart Break-Even Lock</b>", table_cell_left),
            Paragraph("When trade reaches +1.5R (+150 points), the EA automatically shifts Stop-Loss to entry +20 points, eliminating downside risk and locking in a risk-free trade.", table_cell_left),
        ],
        [
            Paragraph("<b>Level 2 50% Partial Take Profit</b>", table_cell_left),
            Paragraph("When profit reaches +2.4R (+300 points), the EA instantly secures 50% of the volume into balance and trails the remaining 50% using dynamic ATR bands.", table_cell_left),
        ],
        [
            Paragraph("<b>Multi-Client PAMM Copy-Receiver</b>", table_cell_left),
            Paragraph("Listens to master broadcast trades from the cloud and executes proportionally on client accounts with sub-40ms synchronization.", table_cell_left),
        ],
        [
            Paragraph("<b>On-Chart 3D Cyber HUD</b>", table_cell_left),
            Paragraph("Displays live balance, floating P/L, 120-AI Swarm vote breakdown, leader category, and 1-click execution and panic close buttons.", table_cell_left),
        ]
    ]

    ea_table = Table(ea_features, colWidths=[160, 380])
    ea_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#334155')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(ea_table)
    story.append(Spacer(1, 10))

    # SECTION 6: CLIENT ONBOARDING GUIDE
    story.append(Paragraph("6. CLIENT ONBOARDING & MT5 SETUP (4 SIMPLE STEPS)", h1_style))
    story.append(Paragraph(
        "Getting started with the Kestrel PAMM Managed Copy-Trader or Standalone EA takes under 2 minutes:",
        body_style
    ))
    story.append(Spacer(1, 4))

    steps_data = [
        [
            Paragraph("<b>STEP 1: ACCOUNT REGISTRATION</b><br/>Create your secure client account on the Kestrel Web Terminal and link your Deriv MT5 Login ID.", table_cell_left),
            Paragraph("<b>STEP 2: FUND YOUR MT5 ACCOUNT</b><br/>Fund your MT5 account with your chosen tier (from $110). Your funds stay in your personal broker account at all times.", table_cell_left),
        ],
        [
            Paragraph("<b>STEP 3: ATTACH KESTREL EA</b><br/>Copy <code>KestrelEA.ex5</code> to your MetaTrader 5 <code>MQL5\\Experts</code> folder and compile in MetaEditor.", table_cell_left),
            Paragraph("<b>STEP 4: ENABLE ALGO TRADING</b><br/>Ensure 'Algo Trading' is enabled in the MT5 top bar. The EA will immediately synchronize and trade autonomously.", table_cell_left),
        ]
    ]

    steps_table = Table(steps_data, colWidths=[265, 265])
    steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0f2fe')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(steps_table)
    story.append(Spacer(1, 14))

    # Disclaimer & Contact Box
    disclaimer_data = [
        [
            Paragraph(
                "<b>RISK WARNING & INSTITUTIONAL COMPLIANCE NOTICE</b><br/>"
                "<font size=7.5 color='#64748b'>"
                "Trading synthetic indices, forex, derivatives, and financial instruments involves substantial risk of loss and is not suitable for every investor. "
                "Targeted returns are projections based on historical 120-AI quantitative backtesting and forward live execution data. Past performance is not indicative of future results. "
                "Kestrel Quantum Trading Intelligence provides quantitative decision-support and automated execution tools. Clients retain 100% custody of their funds in their personal broker accounts.<br/>"
                "<b>Official Web Terminal:</b> https://frontend-delta-pied-96.vercel.app | <b>Support & Concierge:</b> support@kestreltrading.ai"
                "</font>",
                callout_style
            )
        ]
    ]
    disclaimer_table = Table(disclaimer_data, colWidths=[540])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(disclaimer_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Kestrel Institutional PDF generated successfully at: {output_path}")

if __name__ == "__main__":
    out_root = os.path.join(os.getcwd(), "Kestrel_Quantum_Trading_Intelligence.pdf")
    out_public = os.path.join(os.getcwd(), "frontend", "public", "Kestrel_Quantum_Trading_Intelligence.pdf")
    out_artifacts = r"C:\Users\Admin\.gemini\antigravity-ide\brain\7b96ce83-f8a9-46e6-8737-2aa4bf2f00b0\Kestrel_Quantum_Trading_Intelligence.pdf"
    
    generate_pdf(out_root)
    generate_pdf(out_public)
    try:
        generate_pdf(out_artifacts)
    except Exception:
        pass
