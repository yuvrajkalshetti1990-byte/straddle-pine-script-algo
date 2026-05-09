"""
Test suite for dynamic price calculator
Tests various indicator combinations and their effect on premium pricing
"""

from app.models.price_calculator import (
    calculate_dynamic_premium,
    calculate_roc_adjustment,
    calculate_rsi_adjustment,
    calculate_di_adjustment,
    calculate_adx_adjustment,
    calculate_chop_adjustment,
)


def test_roc_adjustment():
    """Test ROC adjustment factor"""
    print("\n" + "="*60)
    print("TEST: ROC Adjustment Factor")
    print("="*60)
    
    test_cases = [
        (50, "Strong positive momentum"),
        (0, "No momentum"),
        (-50, "Strong negative momentum"),
    ]
    
    for roc, desc in test_cases:
        factor = calculate_roc_adjustment(roc)
        print(f"ROC {roc:+3.0f}% → Factor {factor:.4f} ({(factor-1)*100:+.2f}%) — {desc}")


def test_rsi_adjustment():
    """Test RSI adjustment factor"""
    print("\n" + "="*60)
    print("TEST: RSI Adjustment Factor")
    print("="*60)
    
    test_cases = [
        (25, "Oversold"),
        (50, "Neutral"),
        (75, "Overbought"),
    ]
    
    for rsi, desc in test_cases:
        factor = calculate_rsi_adjustment(rsi)
        print(f"RSI {rsi:2.0f} → Factor {factor:.4f} ({(factor-1)*100:+.2f}%) — {desc}")


def test_di_adjustment():
    """Test DI adjustment factor"""
    print("\n" + "="*60)
    print("TEST: DI (Directional Index) Adjustment Factor")
    print("="*60)
    
    test_cases = [
        (30, 10, "Strong uptrend"),
        (20, 20, "Neutral trend"),
        (10, 30, "Strong downtrend"),
    ]
    
    for plus_di, minus_di, desc in test_cases:
        factor = calculate_di_adjustment(plus_di, minus_di)
        print(f"+DI {plus_di} vs -DI {minus_di} → Factor {factor:.4f} ({(factor-1)*100:+.2f}%) — {desc}")


def test_adx_adjustment():
    """Test ADX adjustment factor"""
    print("\n" + "="*60)
    print("TEST: ADX (Trend Strength) Adjustment Factor")
    print("="*60)
    
    test_cases = [
        (15, "Weak trend - add buffer"),
        (30, "Moderate trend - neutral"),
        (50, "Strong trend - reduce buffer"),
    ]
    
    for adx, desc in test_cases:
        factor = calculate_adx_adjustment(adx)
        print(f"ADX {adx:2.0f} → Factor {factor:.4f} ({(factor-1)*100:+.2f}%) — {desc}")


def test_chop_adjustment():
    """Test CHOP adjustment factor"""
    print("\n" + "="*60)
    print("TEST: CHOP (Volatility) Adjustment Factor")
    print("="*60)
    
    test_cases = [
        (30, "Strong trending - reduce buffer"),
        (50, "Neutral - balanced"),
        (70, "Choppy market - add buffer"),
    ]
    
    for chop, desc in test_cases:
        factor = calculate_chop_adjustment(chop)
        print(f"CHOP {chop:2.0f} → Factor {factor:.4f} ({(factor-1)*100:+.2f}%) — {desc}")


def test_dynamic_premium_scenarios():
    """Test complete dynamic premium calculation for realistic scenarios"""
    print("\n" + "="*60)
    print("TEST: Dynamic Premium Calculation Scenarios")
    print("="*60)
    
    # Scenario 1: Bullish trend
    print("\n[SCENARIO 1] Strong Bullish Trend")
    print("-" * 50)
    result = calculate_dynamic_premium(
        ce_close=150,
        pe_close=100,
        roc=35,          # Positive momentum
        rsi=72,          # Overbought
        plus_di=28,      # Strong uptrend
        minus_di=12,
        adx=45,          # Strong trend
        chop=35,         # Trending
    )
    print(f"CE Close: {result['ce_close']} | PE Close: {result['pe_close']}")
    print(f"Base Premium: {result['base_premium']}")
    print(f"Dynamic Premium: {result['dynamic_premium']}")
    print(f"Adjustment Factor: {result['adjustment_factor']}")
    print(f"Premium Change: {result['premium_adjustment_points']:+.2f} points ({result['premium_adjustment_percent']:+.2f}%)")
    
    # Scenario 2: Bearish trend
    print("\n[SCENARIO 2] Strong Bearish Trend")
    print("-" * 50)
    result = calculate_dynamic_premium(
        ce_close=80,
        pe_close=140,
        roc=-25,         # Negative momentum
        rsi=28,          # Oversold
        plus_di=12,      # Weak uptrend
        minus_di=28,     # Strong downtrend
        adx=45,          # Strong trend
        chop=35,         # Trending
    )
    print(f"CE Close: {result['ce_close']} | PE Close: {result['pe_close']}")
    print(f"Base Premium: {result['base_premium']}")
    print(f"Dynamic Premium: {result['dynamic_premium']}")
    print(f"Adjustment Factor: {result['adjustment_factor']}")
    print(f"Premium Change: {result['premium_adjustment_points']:+.2f} points ({result['premium_adjustment_percent']:+.2f}%)")
    
    # Scenario 3: Choppy/Uncertain market
    print("\n[SCENARIO 3] Choppy Market - High Uncertainty")
    print("-" * 50)
    result = calculate_dynamic_premium(
        ce_close=115,
        pe_close=115,
        roc=5,           # Minimal momentum
        rsi=50,          # Neutral
        plus_di=18,      # Weak trend
        minus_di=18,
        adx=18,          # Weak trend
        chop=68,         # Very choppy
    )
    print(f"CE Close: {result['ce_close']} | PE Close: {result['pe_close']}")
    print(f"Base Premium: {result['base_premium']}")
    print(f"Dynamic Premium: {result['dynamic_premium']}")
    print(f"Adjustment Factor: {result['adjustment_factor']}")
    print(f"Premium Change: {result['premium_adjustment_points']:+.2f} points ({result['premium_adjustment_percent']:+.2f}%)")
    
    # Scenario 4: Neutral market with weak trend
    print("\n[SCENARIO 4] Neutral Market - Weak Trend")
    print("-" * 50)
    result = calculate_dynamic_premium(
        ce_close=120,
        pe_close=120,
        roc=0,
        rsi=50,
        plus_di=18,
        minus_di=18,
        adx=25,          # Moderate trend
        chop=50,         # Neutral
    )
    print(f"CE Close: {result['ce_close']} | PE Close: {result['pe_close']}")
    print(f"Base Premium: {result['base_premium']}")
    print(f"Dynamic Premium: {result['dynamic_premium']}")
    print(f"Adjustment Factor: {result['adjustment_factor']}")
    print(f"Premium Change: {result['premium_adjustment_points']:+.2f} points ({result['premium_adjustment_percent']:+.2f}%)")


def test_real_world_scenario():
    """Test with values from dashboard screenshot"""
    print("\n" + "="*60)
    print("TEST: Real World Scenario (from dashboard)")
    print("="*60)
    print("\nUsing indicators from trading dashboard:")
    print("ROC: -10.2, RSI: 22.8, DI: 59.6, +DI: 11.1, ADX: 33.6, CHOP: 21.4")
    print("-" * 50)
    
    result = calculate_dynamic_premium(
        ce_close=200,
        pe_close=180,
        roc=-10.2,
        rsi=22.8,
        plus_di=11.1,
        minus_di=59.6,
        adx=33.6,
        chop=21.4,
    )
    
    print(f"\nInput CE/PE: {result['ce_close']} / {result['pe_close']}")
    print(f"Base Premium (Static): {result['base_premium']}")
    print(f"Dynamic Premium: {result['dynamic_premium']}")
    print(f"Final Adjustment Factor: {result['adjustment_factor']:.4f}")
    print(f"\nPremium Adjustment: {result['premium_adjustment_points']:+.2f} points")
    print(f"Percentage Change: {result['premium_adjustment_percent']:+.2f}%")
    
    print(f"\nIndividual Adjustment Factors:")
    for key, value in result['adjustments'].items():
        pct = (value - 1) * 100
        print(f"  {key:15s}: {value:.4f} ({pct:+.2f}%)")


if __name__ == "__main__":
    test_roc_adjustment()
    test_rsi_adjustment()
    test_di_adjustment()
    test_adx_adjustment()
    test_chop_adjustment()
    test_dynamic_premium_scenarios()
    test_real_world_scenario()
    
    print("\n" + "="*60)
    print("✓ All tests completed successfully!")
    print("="*60)
