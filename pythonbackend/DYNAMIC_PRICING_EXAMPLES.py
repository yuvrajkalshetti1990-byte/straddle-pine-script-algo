"""
Example: How to use Dynamic Pricing in your trading application
"""

# ============================================================
# 1. FRONTEND INTEGRATION - React/TypeScript
# ============================================================

# In your trading dashboard component (e.g., TradingPanel.tsx):

"""
const calculatePriceDisplay = (strike) => {
  // Use dynamic premium instead of straddle_close for entry
  const entryPrice = strike.dynamic_pricing?.dynamic_premium 
    || strike.straddle_ltp;
  
  const adjustmentPercent = strike.dynamic_pricing?.premium_adjustment_percent || 0;
  
  return {
    basePrice: strike.straddle_ltp,
    dynamicPrice: entryPrice,
    adjustment: {
      points: strike.dynamic_pricing?.premium_adjustment_points,
      percent: adjustmentPercent,
    },
    factors: strike.dynamic_pricing?.adjustments || {},
  };
};

// Display dynamic price with indicator breakdown
const renderDynamicPrice = (strike) => {
  const pricing = calculatePriceDisplay(strike);
  
  return (
    <div className="price-card">
      <div className="price-display">
        <span className="label">Base Price</span>
        <span className="value">{pricing.basePrice}</span>
      </div>
      
      <div className="price-display dynamic">
        <span className="label">Dynamic Price</span>
        <span className={`value ${pricing.adjustment.percent > 0 ? 'premium' : 'discount'}`}>
          {pricing.dynamicPrice}
        </span>
        <span className="adjustment">
          {pricing.adjustment.percent > 0 ? '+' : ''}{pricing.adjustment.percent.toFixed(2)}%
        </span>
      </div>
      
      <div className="indicators-breakdown">
        <h4>Adjustment Factors</h4>
        <ul>
          <li>ROC: {(pricing.factors.roc_factor * 100 - 100).toFixed(2)}%</li>
          <li>RSI: {(pricing.factors.rsi_factor * 100 - 100).toFixed(2)}%</li>
          <li>DI: {(pricing.factors.di_factor * 100 - 100).toFixed(2)}%</li>
          <li>ADX: {(pricing.factors.adx_factor * 100 - 100).toFixed(2)}%</li>
          <li>CHOP: {(pricing.factors.chop_factor * 100 - 100).toFixed(2)}%</li>
        </ul>
      </div>
    </div>
  );
};
"""

# ============================================================
# 2. TRADE EXECUTION - Python Backend
# ============================================================

from app.models.price_calculator import calculate_dynamic_premium
from app.models.indicator_model import translate_strike_payload


async def execute_trade_with_dynamic_pricing(strike_data, quantity, side):
    """
    Execute trade using dynamic prices instead of static LTP
    
    Args:
        strike_data: Strike information with indicators
        quantity: Number of units to trade
        side: "BUY" or "SELL"
    """
    
    # Get dynamic pricing
    pricing_info = strike_data.get("dynamic_pricing", {})
    
    # Use dynamic premium as entry price
    entry_price = pricing_info.get("dynamic_premium") or strike_data.get("straddle_ltp")
    
    # Calculate position details
    position_value = entry_price * quantity
    
    # Get adjustment factor for risk management
    adjustment_factor = pricing_info.get("adjustment_factor", 1.0)
    
    # Risk-adjusted stop loss and target
    if adjustment_factor < 1.0:  # Premium was reduced (confident trend)
        sl_buffer = 0.5  # Tighter stop loss
        tp_buffer = 1.5  # Higher target
    elif adjustment_factor > 1.02:  # Premium was increased (uncertain)
        sl_buffer = 1.0  # Wider stop loss
        tp_buffer = 0.8  # Lower target
    else:
        sl_buffer = 0.75
        tp_buffer = 1.0
    
    # Set stop loss and target
    stop_loss = entry_price - sl_buffer
    target_price = entry_price + tp_buffer
    
    trade_params = {
        "strike": strike_data.get("strike"),
        "entry_price": round(entry_price, 2),
        "base_price": strike_data.get("straddle_ltp"),
        "quantity": quantity,
        "side": side,
        "position_value": round(position_value, 2),
        "stop_loss": round(stop_loss, 2),
        "target_price": round(target_price, 2),
        "adjustment_factor": adjustment_factor,
        "premium_adjustment_pct": pricing_info.get("premium_adjustment_percent", 0),
        "confidence_level": "HIGH" if adjustment_factor < 0.97 else "MEDIUM" if adjustment_factor > 1.02 else "NEUTRAL",
    }
    
    return trade_params


# ============================================================
# 3. STRIKE SELECTION - Choose best strike based on adjustment
# ============================================================

def rank_strikes_by_dynamic_pricing(strikes_data):
    """
    Rank strikes by confidence level based on dynamic pricing adjustments
    
    Lower adjustment factor = Higher confidence in trend direction
    Strategies to adjust based on confidence:
    - HIGH confidence: Use smaller stop loss, larger position size
    - MEDIUM confidence: Normal risk management
    - LOW confidence: Use wider stop loss, smaller position size
    """
    
    ranked = []
    
    for strike in strikes_data:
        pricing = strike.get("dynamic_pricing", {})
        factor = pricing.get("adjustment_factor", 1.0)
        change_pct = pricing.get("premium_adjustment_percent", 0)
        
        # Calculate confidence score
        if factor < 0.97:
            confidence = "VERY_HIGH"
            score = 5
        elif factor < 0.99:
            confidence = "HIGH"
            score = 4
        elif factor < 1.01:
            confidence = "NEUTRAL"
            score = 3
        elif factor < 1.03:
            confidence = "LOW"
            score = 2
        else:
            confidence = "VERY_LOW"
            score = 1
        
        ranked.append({
            "strike": strike.get("strike"),
            "entry_price": pricing.get("dynamic_premium"),
            "adjustment_factor": factor,
            "confidence": confidence,
            "score": score,
            "indicators": strike.get("indicators", {}),
            "premium_adjustment": change_pct,
        })
    
    # Sort by confidence score (descending)
    return sorted(ranked, key=lambda x: x["score"], reverse=True)


# ============================================================
# 4. STRATEGY PARAMETER ADJUSTMENT
# ============================================================

def adjust_strategy_parameters(adjustment_factor):
    """
    Adjust strategy parameters based on premium adjustment factor
    
    Factor Interpretation:
    - < 0.95: Very confident in trend (tight range prediction)
    - 0.95-0.99: Confident in direction (normal parameters)
    - 0.99-1.01: Uncertain market (cautious parameters)
    - 1.01-1.05: Low confidence (defensive parameters)
    - > 1.05: Very uncertain (very defensive)
    """
    
    if adjustment_factor < 0.95:
        return {
            "max_lot_size": 2,  # Can take larger position
            "stop_loss_points": 20,  # Tight stop
            "target_multiple": 2.0,  # 2x profit target
            "position_sizing": "AGGRESSIVE",
        }
    elif adjustment_factor < 0.99:
        return {
            "max_lot_size": 1,
            "stop_loss_points": 30,
            "target_multiple": 1.5,
            "position_sizing": "NORMAL",
        }
    elif adjustment_factor < 1.01:
        return {
            "max_lot_size": 1,
            "stop_loss_points": 50,
            "target_multiple": 1.0,
            "position_sizing": "CAUTIOUS",
        }
    elif adjustment_factor < 1.05:
        return {
            "max_lot_size": 0.5,
            "stop_loss_points": 75,
            "target_multiple": 0.75,
            "position_sizing": "DEFENSIVE",
        }
    else:
        return {
            "max_lot_size": 0.25,
            "stop_loss_points": 100,
            "target_multiple": 0.5,
            "position_sizing": "VERY_DEFENSIVE",
        }


# ============================================================
# 5. INDICATOR-BASED FILTERS
# ============================================================

def should_trade(strike_data):
    """
    Determine if we should trade this strike based on dynamic pricing indicators
    
    Returns: (should_trade: bool, reason: str, confidence_score: float)
    """
    
    pricing = strike_data.get("dynamic_pricing", {})
    indicators = strike_data.get("indicators", {})
    
    # Get individual factors
    factors = pricing.get("adjustments", {})
    
    # Strong trend signals
    roc = indicators.get("roc", 0)
    rsi = indicators.get("rsi", 50)
    adx = indicators.get("adx", 20)
    chop = indicators.get("chop", 50)
    
    confidence_score = 0
    reason = ""
    
    # Check for optimal conditions
    if abs(roc) > 20:
        confidence_score += 1
        reason += "Strong momentum. "
    
    if rsi > 60 or rsi < 40:
        confidence_score += 1
        reason += "RSI extremes. "
    
    if adx > 35:
        confidence_score += 1
        reason += "Strong trend (ADX). "
    
    if chop < 40:
        confidence_score += 1
        reason += "Trending market (CHOP < 40). "
    
    # Avoid trading conditions
    if chop > 65:
        confidence_score -= 2
        reason += "Choppy market - AVOID. "
    
    if adx < 15:
        confidence_score -= 1
        reason += "Weak trend. "
    
    should_trade = confidence_score >= 2
    
    return (should_trade, reason.strip(), confidence_score)


# ============================================================
# 6. USAGE EXAMPLE - Main Trading Loop
# ============================================================

async def main_trading_loop():
    """
    Main trading loop integrating dynamic pricing
    """
    
    # Fetch strike data with dynamic pricing
    strike_data = await fetch_market_strikes()  # Your API call
    
    # Translate to get dynamic pricing
    payload = {"strikes": strike_data}
    translated = translate_strike_payload(payload)
    
    # Rank strikes by confidence
    ranked_strikes = rank_strikes_by_dynamic_pricing(translated)
    
    for strike in ranked_strikes[:3]:  # Consider top 3 strikes
        
        # Check if we should trade
        should_trade, reason, confidence = should_trade(strike)
        
        if not should_trade:
            print(f"Skip {strike['strike']}: {reason}")
            continue
        
        # Get adjusted parameters
        params = adjust_strategy_parameters(strike["adjustment_factor"])
        
        # Prepare trade
        trade_plan = await execute_trade_with_dynamic_pricing(
            strike,
            quantity=params["max_lot_size"],
            side="BUY" if strike["indicators"]["rsi"] < 40 else "SELL"
        )
        
        print(f"Trading {strike['strike']}")
        print(f"  Entry Price: {trade_plan['entry_price']}")
        print(f"  SL: {trade_plan['stop_loss']} | Target: {trade_plan['target_price']}")
        print(f"  Confidence: {trade_plan['confidence_level']}")
        print(f"  Adjustment: {trade_plan['premium_adjustment_pct']:.2f}%")
        
        # Execute trade with dynamic pricing
        # await execute_order(trade_plan)


# ============================================================
# 7. DASHBOARD DISPLAY - Metrics to show
# ============================================================

def prepare_dashboard_display(strikes_data):
    """
    Prepare data for dashboard showing dynamic pricing effects
    """
    
    dashboard_data = {
        "strikes": [],
        "summary": {
            "avg_adjustment_percent": 0,
            "high_confidence_count": 0,
            "trend_direction": "NEUTRAL",
            "market_confidence": "MEDIUM",
        }
    }
    
    adjustments = []
    
    for strike in strikes_data:
        pricing = strike.get("dynamic_pricing", {})
        indicators = strike.get("indicators", {})
        
        # Calculate confidence
        factor = pricing.get("adjustment_factor", 1.0)
        if factor < 0.97:
            confidence = "VERY_HIGH"
        elif factor < 0.99:
            confidence = "HIGH"
        else:
            confidence = "MEDIUM"
        
        # Prepare display
        display = {
            "strike": strike.get("strike"),
            "basePrice": strike.get("straddle_ltp"),
            "dynamicPrice": pricing.get("dynamic_premium"),
            "adjustmentPoints": pricing.get("premium_adjustment_points"),
            "adjustmentPercent": pricing.get("premium_adjustment_percent"),
            "confidence": confidence,
            "roc": indicators.get("roc"),
            "rsi": indicators.get("rsi"),
            "adx": indicators.get("adx"),
            "chop": indicators.get("chop"),
        }
        
        dashboard_data["strikes"].append(display)
        adjustments.append(pricing.get("premium_adjustment_percent", 0))
    
    # Calculate summary
    if adjustments:
        dashboard_data["summary"]["avg_adjustment_percent"] = sum(adjustments) / len(adjustments)
    
    dashboard_data["summary"]["high_confidence_count"] = sum(
        1 for s in dashboard_data["strikes"] if s["confidence"] in ["HIGH", "VERY_HIGH"]
    )
    
    # Determine trend direction from ROC
    roc_values = [s.get("roc", 0) for s in dashboard_data["strikes"]]
    avg_roc = sum(roc_values) / len(roc_values) if roc_values else 0
    dashboard_data["summary"]["trend_direction"] = "UP" if avg_roc > 5 else "DOWN" if avg_roc < -5 else "NEUTRAL"
    
    return dashboard_data


if __name__ == "__main__":
    # Example usage
    print("Dynamic Pricing Integration Examples Created")
    print("See functions above for usage patterns")
