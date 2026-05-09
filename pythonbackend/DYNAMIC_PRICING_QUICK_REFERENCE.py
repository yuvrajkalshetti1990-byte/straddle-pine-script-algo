"""
QUICK REFERENCE: Dynamic Pricing API Response Format

This guide shows what to expect from the API and how to use it
"""

# ============================================================
# API RESPONSE STRUCTURE
# ============================================================

API_RESPONSE_EXAMPLE = {
    "status": "success",
    "connected": True,
    "data": [
        {
            # Basic Strike Information
            "strike": 24100,
            "straddle_open": 250.50,
            "straddle_close": 251.75,
            "straddle_high": 254.00,
            "straddle_low": 249.50,
            "straddle_ltp": 251.75,
            "change": 1.25,
            
            # Component Prices
            "ce_ltp": 152.50,  # Call (CE) Last Traded Price
            "pe_ltp": 99.25,   # Put (PE) Last Traded Price
            
            # Technical Indicators
            "indicators": {
                "roc": -10.2,      # Rate of Change (%)
                "rsi": 22.8,       # Relative Strength Index (0-100)
                "di_plus": 11.1,   # Plus Directional Indicator
                "di_minus": 59.6,  # Minus Directional Indicator
                "adx": 33.6,       # Average Directional Index
                "chop": 21.4,      # Choppiness Index (0-100)
            },
            
            # ★ NEW: DYNAMIC PRICING INFORMATION ★
            "dynamic_pricing": {
                # Core Prices
                "base_premium": 251.75,          # CE + PE (static)
                "dynamic_premium": 255.87,       # Adjusted price
                
                # Adjustment Details
                "adjustment_factor": 1.0164,     # 1.0 = no change, >1.0 = premium increased
                "premium_adjustment_points": 4.12,    # Points added to base price
                "premium_adjustment_percent": 1.64,   # Percentage change
                
                # Individual Indicator Factors
                "adjustments": {
                    "roc_factor": 1.0291,        # ROC contributed +2.91%
                    "rsi_factor": 1.0544,        # RSI contributed +5.44%
                    "di_factor": 1.0485,         # DI contributed +4.85%
                    "adx_factor": 1.0000,        # ADX contributed 0% (moderate trend)
                    "chop_factor": 0.9590,       # CHOP contributed -4.10%
                }
            }
        },
        # ... more strikes
    ]
}

# ============================================================
# FIELD DESCRIPTIONS
# ============================================================

FIELD_DEFINITIONS = {
    # Base Premium (Static)
    "base_premium": {
        "value": "ce_ltp + pe_ltp",
        "meaning": "Simple sum of call and put prices",
        "when_to_use": "For reference or reverting to static pricing",
    },
    
    # Dynamic Premium (Recommended)
    "dynamic_premium": {
        "value": "base_premium × adjustment_factor",
        "meaning": "Indicator-adjusted entry price",
        "when_to_use": "PRIMARY entry price for all trades",
    },
    
    # Adjustment Factor
    "adjustment_factor": {
        "example": 1.0164,
        "meaning": "1.0 = no adjustment, 1.0164 = +1.64% premium increase",
        "interpretation": {
            "< 0.95": "Strong confidence in trend (reduce buffer)",
            "0.95-0.99": "High confidence",
            "0.99-1.01": "Neutral/uncertain market",
            "1.01-1.05": "Lower confidence (increase buffer)",
            "> 1.05": "Very uncertain market",
        },
    },
    
    # Premium Adjustment in Points
    "premium_adjustment_points": {
        "example": 4.12,
        "meaning": "Actual points added or removed from base price",
        "calculation": "dynamic_premium - base_premium",
        "positive": "Premium increased (add buffer)",
        "negative": "Premium decreased (reduce buffer)",
    },
    
    # Premium Adjustment Percentage
    "premium_adjustment_percent": {
        "example": 1.64,
        "meaning": "Percentage change from base premium",
        "calculation": "(adjustment_points / base_premium) × 100",
        "use": "For risk management and position sizing",
    },
}

# ============================================================
# INDICATOR FACTOR INTERPRETATION
# ============================================================

INDICATOR_FACTORS_GUIDE = {
    "roc_factor": {
        "name": "Rate of Change",
        "range": [0.85, 1.15],
        "meaning": "Momentum adjustment",
        "interpretation": {
            0.85: "Very strong positive momentum (+50% ROC)",
            0.95: "Moderate positive momentum (+20% ROC)",
            1.00: "No momentum (ROC ≈ 0%)",
            1.05: "Moderate negative momentum (-15% ROC)",
            1.15: "Very strong negative momentum (-50% ROC)",
        },
    },
    
    "rsi_factor": {
        "name": "Relative Strength Index",
        "range": [0.90, 1.10],
        "meaning": "Trend strength adjustment",
        "interpretation": {
            0.95: "Overbought (RSI > 70) - reduce premium",
            1.00: "Neutral (RSI ≈ 50)",
            1.05: "Oversold (RSI < 30) - increase premium",
        },
    },
    
    "di_factor": {
        "name": "Directional Index",
        "range": [0.95, 1.05],
        "meaning": "Directional trend adjustment",
        "interpretation": {
            0.98: "Strong uptrend (+DI >> -DI)",
            1.00: "Neutral trend (+DI ≈ -DI)",
            1.02: "Strong downtrend (-DI >> +DI)",
        },
    },
    
    "adx_factor": {
        "name": "Average Directional Index",
        "range": [0.95, 1.10],
        "meaning": "Trend confirmation adjustment",
        "interpretation": {
            1.05: "Weak trend (ADX < 20) - add safety buffer",
            1.00: "Moderate trend (ADX 20-40)",
            0.99: "Strong trend (ADX > 40) - reduce buffer",
        },
    },
    
    "chop_factor": {
        "name": "Choppiness Index",
        "range": [0.93, 1.10],
        "meaning": "Volatility/consolidation adjustment",
        "interpretation": {
            0.98: "Strong trending (CHOP < 38) - reduce buffer",
            1.00: "Neutral (CHOP 38-62)",
            1.05: "Choppy/uncertain (CHOP > 62) - add buffer",
        },
    },
}

# ============================================================
# USAGE PATTERNS IN FRONTEND CODE
# ============================================================

# React/TypeScript Example

"""
import { useEffect, useState } from 'react';

export function StrikeCard({ strike }) {
  const pricing = strike.dynamic_pricing;
  
  // Determine color based on adjustment
  const getAdjustmentColor = (factor) => {
    if (factor < 0.97) return '#00FF00'; // Green - High confidence
    if (factor < 0.99) return '#00AA00'; // Light green - Good
    if (factor < 1.01) return '#FFAA00'; // Orange - Neutral
    if (factor < 1.03) return '#FF6600'; // Dark orange - Low confidence
    return '#FF0000'; // Red - Very uncertain
  };
  
  return (
    <div className="strike-card">
      {/* Price Display */}
      <div className="prices">
        <div className="price-row">
          <span className="label">Base</span>
          <span className="value">{pricing.base_premium.toFixed(2)}</span>
        </div>
        <div className="price-row highlight">
          <span className="label">Dynamic</span>
          <span className="value" style={{color: getAdjustmentColor(pricing.adjustment_factor)}}>
            {pricing.dynamic_premium.toFixed(2)}
          </span>
          <span className="change">
            {pricing.premium_adjustment_percent > 0 ? '+' : ''}
            {pricing.premium_adjustment_percent.toFixed(2)}%
          </span>
        </div>
      </div>
      
      {/* Indicator Breakdown */}
      <div className="indicators">
        <div className="indicator">
          <span className="name">ROC</span>
          <span className="value">{strike.indicators.roc?.toFixed(1)}%</span>
          <span className="factor">({(pricing.adjustments.roc_factor * 100 - 100).toFixed(1)}%)</span>
        </div>
        <div className="indicator">
          <span className="name">RSI</span>
          <span className="value">{strike.indicators.rsi?.toFixed(0)}</span>
          <span className="factor">({(pricing.adjustments.rsi_factor * 100 - 100).toFixed(1)}%)</span>
        </div>
        <div className="indicator">
          <span className="name">ADX</span>
          <span className="value">{strike.indicators.adx?.toFixed(0)}</span>
          <span className="factor">({(pricing.adjustments.adx_factor * 100 - 100).toFixed(1)}%)</span>
        </div>
        <div className="indicator">
          <span className="name">CHOP</span>
          <span className="value">{strike.indicators.chop?.toFixed(0)}</span>
          <span className="factor">({(pricing.adjustments.chop_factor * 100 - 100).toFixed(1)}%)</span>
        </div>
      </div>
      
      {/* Trade Button */}
      <button 
        className="trade-btn"
        onClick={() => executeTrade(strike)}
        style={{
          opacity: pricing.adjustment_factor < 1.02 ? 1.0 : 0.6,
          cursor: pricing.adjustment_factor < 1.02 ? 'pointer' : 'not-allowed'
        }}
      >
        {pricing.adjustment_factor < 0.97 ? '⭐ Trade Now' : 'Trade'}
      </button>
    </div>
  );
}

// Fetch with dynamic pricing
async function fetchStrikes() {
  const response = await fetch('/api/v1/market/strikes/translate', {
    method: 'POST',
    body: JSON.stringify(strikePayload)
  });
  const data = await response.json();
  return data.data; // Array of strikes with dynamic_pricing
}
"""

# ============================================================
# TRADING DECISION LOGIC
# ============================================================

DECISION_MATRIX = {
    "HIGH_CONFIDENCE": {
        "adjustment_factor": "< 0.97",
        "interpretation": "Strong trend with clear direction",
        "actions": {
            "position_size": "NORMAL or AGGRESSIVE",
            "stop_loss": "TIGHT (20-30 points)",
            "entry": "dynamic_premium (preferred)",
            "frequency": "TRADE FREQUENTLY",
        },
    },
    
    "GOOD": {
        "adjustment_factor": "0.97-0.99",
        "interpretation": "Confident direction with some uncertainty",
        "actions": {
            "position_size": "NORMAL",
            "stop_loss": "MODERATE (30-50 points)",
            "entry": "dynamic_premium",
            "frequency": "TRADE REGULARLY",
        },
    },
    
    "NEUTRAL": {
        "adjustment_factor": "0.99-1.01",
        "interpretation": "Uncertain market, no clear direction",
        "actions": {
            "position_size": "SMALL",
            "stop_loss": "WIDE (50-75 points)",
            "entry": "base_premium or skip",
            "frequency": "TRADE OCCASIONALLY",
        },
    },
    
    "LOW_CONFIDENCE": {
        "adjustment_factor": "1.01-1.05",
        "interpretation": "Very uncertain, choppy market",
        "actions": {
            "position_size": "VERY SMALL or SKIP",
            "stop_loss": "VERY WIDE (75-100 points)",
            "entry": "base_premium only if trading",
            "frequency": "RARELY TRADE",
        },
    },
    
    "VERY_LOW_CONFIDENCE": {
        "adjustment_factor": "> 1.05",
        "interpretation": "Extreme uncertainty, avoid",
        "actions": {
            "position_size": "AVOID TRADING",
            "stop_loss": "N/A",
            "entry": "DO NOT TRADE",
            "frequency": "DO NOT TRADE",
        },
    },
}

# ============================================================
# SUMMARY TABLE FOR QUICK REFERENCE
# ============================================================

"""
┌────────────────────────────────────────────────────────────────────────────┐
│ DYNAMIC PRICING QUICK REFERENCE                                            │
├─────────────────┬──────────────┬────────────┬───────────────────────────────┤
│ Adjustment      │ Factor Range │ Market     │ Recommended Action            │
│ Factor          │              │ Condition  │                               │
├─────────────────┼──────────────┼────────────┼───────────────────────────────┤
│ Very High Conf  │ < 0.95       │ Strong     │ ⭐ AGGRESSIVE - Use tight SL  │
│ High Confidence │ 0.95-0.99    │ Confident  │ ✓ NORMAL - Regular trading    │
│ Neutral         │ 0.99-1.01    │ Uncertain  │ ≈ CAUTIOUS - Wider SL        │
│ Low Confidence  │ 1.01-1.05    │ Choppy     │ ⚠ DEFENSIVE - Small size      │
│ Very Low Conf   │ > 1.05       │ Extreme    │ ✗ AVOID - Do not trade        │
└─────────────────┴──────────────┴────────────┴───────────────────────────────┘

Premium Adjustment Guide:
- Negative adjustment (<1.0): Premium decreased → Market trending → Confident
- Positive adjustment (>1.0): Premium increased → Market choppy → Cautious
- Neutral adjustment (~1.0): No adjustment → Market balanced → Neutral
"""

# ============================================================
# BEST PRACTICES
# ============================================================

BEST_PRACTICES = [
    "✓ ALWAYS use 'dynamic_premium' as your entry price",
    "✓ Use 'adjustment_factor' to determine position size and SL",
    "✓ Monitor 'adjustment_percent' to understand market confidence",
    "✓ Check CHOP and ADX for trend confirmation",
    "✓ Avoid trading when adjustment_factor > 1.05",
    "✓ Be aggressive when adjustment_factor < 0.95",
    "✓ Combine multiple indicators for better decisions",
    "✓ Track adjustment changes over time for patterns",
    "",
    "✗ DON'T use base_premium for entry decisions",
    "✗ DON'T ignore adjustment_factor in risk management",
    "✗ DON'T trade choppy markets (CHOP > 65 + ADX < 20)",
    "✗ DON'T override indicators based on intuition",
]

print("DYNAMIC PRICING QUICK REFERENCE")
print("=" * 80)
for practice in BEST_PRACTICES:
    print(practice)
