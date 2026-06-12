import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="F&O Virtual Trader", layout="wide", initial_sidebar_state="expanded")

# Initialize Session States for Virtual Portfolio
if "balance" not in st.session_state:
    st.session_state.balance = 1000000.0  # ₹10 Lakhs Virtual Cash
if "positions" not in st.session_state:
    st.session_state.positions = []  # Open positions
if "order_log" not in st.session_state:
    st.session_state.order_log = []  # Past orders
if "nifty_spot" not in st.session_state:
    st.session_state.nifty_spot = 24200.0

# --- SIMULATED LIVE MARKET FEED ---
# Fluctuate the market spot price slightly on each rerun to simulate live feeds
price_fluctuation = np.random.uniform(-15.0, 15.0)
st.session_state.nifty_spot = round(st.session_state.nifty_spot + price_fluctuation, 2)
spot = st.session_state.nifty_spot

# Sidebar: User Account Summary
st.sidebar.title("💳 Virtual Wallet")
st.sidebar.metric(label="Available Cash", value=f"₹{st.session_state.balance:,.2f}")
if st.sidebar.button("Reset Wallet to ₹10 Lakhs"):
    st.session_state.balance = 1000000.0
    st.session_state.positions = []
    st.session_state.order_log = []
    st.rerun()

# Layout: Main Terminal Header
st.title("📈 Nifty 50 F&O Training Terminal")
st.subheader(f"NIFTY 50 Spot: ₹{spot:,} ⚡ (Live Simulated)")

# --- ORDER ENTRY PANEL ---
st.write("### 🛒 Order Placement Panel")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    instrument = st.selectbox("Instrument", ["NIFTY 50 Options", "NIFTY 50 Futures"])
with col2:
    if instrument == "NIFTY 50 Options":
        # Generate dynamic ATM/OTM strikes based on current spot
        atm_strike = int(round(spot / 50) * 50)
        strikes = [atm_strike + i for i in range(-200, 250, 50)]
        strike = st.selectbox("Strike Price", strikes, index=4)
    else:
        strike = "FUT-CURRENT"
with col3:
    opt_type = st.selectbox("Type", ["CE", "PE"]) if instrument == "NIFTY 50 Options" else "FUT"
with col4:
    action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
with col5:
    lots = st.number_input("Lots (1 Lot = 25 qty)", min_value=1, value=1, step=1)

qty = lots * 25

# Simple Options Pricing Engine (Intrinsic + basic time value model)
def calculate_premium(spot_price, strike_p, o_type):
    if strike_p == "FUT-CURRENT":
        return spot_price
    intrinsic = max(0, spot_price - strike_p) if o_type == "CE" else max(0, strike_p - spot_price)
    time_value = 45.0  # Static premium padding for educational simulation
    return round(intrinsic + time_value, 2)

current_premium = calculate_premium(spot, strike, opt_type)
total_order_value = current_premium * qty

# Margin & Premium Cost Logic
if action == "BUY":
    required_margin = total_order_value
    margin_label = "Premium Required"
else:
    required_margin = 110000.0 * lots  # standard ₹1.1L approximate margin per lot for shorting
    margin_label = "SPAN + Exposure Margin"

st.info(f"Current Market Premium/Price: **₹{current_premium}** | Estimated {margin_label}: **₹{required_margin:,.2f}**")

if st.button("Execute Virtual Order", use_container_width=True):
    if st.session_state.balance < required_margin:
        st.error("❌ Insufficient virtual funds to complete this transaction.")
    else:
        # Deduct or hold funds
        if action == "BUY":
            st.session_state.balance -= required_margin
        
        # Log transaction
        trade_details = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "instrument": f"{strike} {opt_type}" if instrument == "NIFTY 50 Options" else "NIFTY FUT",
            "action": action,
            "qty": qty,
            "entry_price": current_premium,
            "margin_blocked": required_margin if action == "SELL" else 0
        }
        st.session_state.positions.append(trade_details)
        st.session_state.order_log.append(trade_details)
        st.success(f"✔️ Order successful! {action} {qty} units at ₹{current_premium}")
        time.sleep(0.5)
        st.rerun()

# --- PORTFOLIO & LIVE POSITIONS ---
st.write("### 💼 Open Positions & Mark-to-Market (MTM)")
if not st.session_state.positions:
    st.write("_No open positions. Place an order above to start trading._")
else:
    pos_data = []
    total_live_mtm = 0.0
    
    for i, pos in enumerate(st.session_state.positions):
        live_price = calculate_premium(spot, int(pos["instrument"].split()[0]) if "FUT" not in pos["instrument"] else "FUT-CURRENT", pos["instrument"].split()[-1] if "FUT" not in pos["instrument"] else "FUT")
        
        # Calculate P&L based on direction
        if pos["action"] == "BUY":
            pnl = (live_price - pos["entry_price"]) * pos["qty"]
        else:
            pnl = (pos["entry_price"] - live_price) * pos["qty"]
            
        total_live_mtm += pnl
        
        pos_data.append({
            "ID": i,
            "Instrument": pos["instrument"],
            "Type": pos["action"],
            "Qty": pos["qty"],
            "Avg Entry Price": f"₹{pos['entry_price']}",
            "Current Price": f"₹{live_price}",
            "Unrealized P&L": round(pnl, 2)
        })
    
    df_pos = pd.DataFrame(pos_data)
    st.dataframe(df_pos.set_index("ID"), use_container_width=True)
    
    # Highlight overall running portfolio performance
    if total_live_mtm >= 0:
        st.success(f"Total Live MTM P&L: **+₹{total_live_mtm:,.2f}**")
    else:
        st.error(f"Total Live MTM P&L: **-₹{abs(total_live_mtm):,.2f}**")

# --- ORDER LEDGER LOGS ---
st.write("### 📜 Today's Order History Log")
if st.session_state.order_log:
    st.json(st.session_state.order_log)
else:
    st.caption("No history generated yet.")

# Auto-Refresh trigger layout helper
st.button("🔄 Refresh Live Feed Prices")
