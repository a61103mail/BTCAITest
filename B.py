# B.py - AI 大腦 (V48: 智能解鎖版 - 找回 V41 的獲利爆發力)
import google.generativeai as genai
import json
import warnings
import time
import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

keys_str = os.getenv("GEMINI_KEYS")
if not keys_str: raise ValueError("找不到 GEMINI_KEYS")
API_KEYS = [k.strip() for k in keys_str.split(',') if k.strip()]

warnings.filterwarnings("ignore")
current_key_index = 0
model = None

def get_best_model_for_key(api_key):
    genai.configure(api_key=api_key)
    try:
        valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in valid_models if 'flash' in m), None)
        target = target or next((m for m in valid_models if 'pro' in m), valid_models[0] if valid_models else None)
        return genai.GenerativeModel(target.replace("models/", "")) if target else None
    except: return None

def rotate_key():
    global current_key_index, model
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    model = get_best_model_for_key(API_KEYS[current_key_index])

rotate_key()

def ask_ai_for_signal(row, trend):
    global model
    
    # ==========================================
    # 🔥 V48 底線防火牆 (Baseline Filters)
    # ==========================================
    # 我們只保留「過濾垃圾」的底線，拆除「限制獲利」的上限
    
    rsi = row['RSI']
    adx = row['ADX']
    rvol = row['RVOL']
    ema_dist = row['EMA_DIST']
    
    # 1. 保留趨勢底線 (ADX > 25)
    # 這是過濾盤整盤最有效的工具，必須保留。
    if adx < 25:
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: ADX {adx:.1f} 不足 25，趨勢不明顯"}
    
    # 2. 保留量能底線 (RVOL > 0.8)
    # 這是過濾假突破的工具，必須保留。
    if rvol < 0.8:
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: RVOL {rvol:.2f} 縮量，缺乏動能"}
    
    # 3. 乖離率保護 (防止極端追高)
    if abs(ema_dist) > 3.0: # 放寬到 3%，給大行情一點空間
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: 乖離率 {ema_dist:.1f}% 過極端，等待回歸"}

    # ❌ 刪除了 RSI > 70 / < 30 的硬體攔截
    # 讓 AI 決定是「過熱」還是「強勢噴發」

    # ==========================================
    # 交給 AI 進行「強勢區」判斷
    # ==========================================
    rotate_key()
    
    if adx > 50: market_state = "⚠️ 極度強勢 (注意反轉)"
    else: market_state = "🚀 健康趨勢"
    
    vol_state = "🔥 爆量" if rvol > 1.2 else "📈 放量"

    # RSI 狀態描述
    if rsi > 70: rsi_state = "🔥 超買鈍化區 (強勢)"
    elif rsi < 30: rsi_state = "❄️ 超賣鈍化區 (弱勢)"
    else: rsi_state = "✅ 安全操作區"

    score_bull = row['SCORE_BULL']
    score_bear = row['SCORE_BEAR']
    
    prompt = f"""
    你是 V48 頂尖交易員。我們移除了 RSI 的硬體限制，因為我們要抓到【主升段】的暴利。
    請根據數據判斷現在是「強勢噴發」還是「頂部背離」。
    
    【市場數據】
    1. 趨勢 (ADX): {adx:.1f} ({market_state})
    2. 動能 (RVOL): {rvol:.2f} ({vol_state})
    3. RSI: {rsi:.1f} ({rsi_state})
    4. 乖離率: {ema_dist:.2f}%
    
    【智能評分】
    多頭: {score_bull:.1f} / 空頭: {score_bear:.1f}
    
    【決策邏輯】
    1. **凱利過濾**：多空分數差距必須 > 15。
    2. **超買區操作 (RSI > 70)**：
       - 只有當 RVOL > 1.5 (爆量) 且 ADX 持續上升時，才允許追多 (視為強勢鈍化)。
       - 否則視為過熱，回傳 WAIT。
    3. **超賣區操作 (RSI < 30)**：
       - 只有當 RVOL > 1.5 (爆量) 且 ADX 持續上升時，才允許追空 (視為崩盤)。
       - 否則視為過冷，回傳 WAIT。
    4. **安全區操作 (30-70)**：
       - 正常依照分數與趨勢進場。
    
    回傳 JSON: {{"action": "BUY" | "SELL" | "WAIT", "reason": "分析原因 (針對 RSI 位置與量能配合)"}}
    """

    max_retries = len(API_KEYS)
    for _ in range(max_retries):
        if model is None: rotate_key(); continue
        try:
            response = model.generate_content(prompt)
            text = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except:
            rotate_key()
            continue

    return {"action": "WAIT", "reason": "All Keys Failed"}