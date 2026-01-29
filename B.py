# B.py - AI 大腦 (V47: 黃金復刻版 - Back to Basics)
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
    # 🔥 V47 黃金復刻防火牆 (Classic Hard Filters)
    # ==========================================
    # 回歸 V41 的獲利邏輯，配合標準風控
    
    rsi = row['RSI']
    adx = row['ADX']
    rvol = row['RVOL']
    ema_dist = row['EMA_DIST']
    
    # 1. RSI 標準安全區 (30 ~ 70)
    # 不再使用動態區間，回歸最穩定的教科書標準。
    # 拒絕 RSI > 70 的追高，拒絕 RSI < 30 的殺低。
    if rsi > 70: 
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: RSI {rsi:.1f} 進入超買區 (>70)，拒絕追高"}
    if rsi < 30: 
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: RSI {rsi:.1f} 進入超賣區 (<30)，拒絕殺低"}

    # 2. ADX 強趨勢門檻 (25)
    # 回歸 V40/V41 的標準。23 太低容易遇到假突破，25 才是真行情的開始。
    if adx < 25:
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: ADX {adx:.1f} 不足 25，趨勢不明顯"}
    
    # 3. RVOL 有效量能 (0.8)
    # 0.8 代表至少有平常 80% 的量，避免在無人交易的時段進場。
    if rvol < 0.8:
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: RVOL {rvol:.2f} 縮量，缺乏動能"}
    
    # 4. 乖離率保護
    # 避免價格已經飛太遠時進場接刀
    if abs(ema_dist) > 2.0:
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: 乖離率 {ema_dist:.1f}% 過大，等待回歸"}

    # ==========================================
    # 讓 AI 專注於結構分析
    # ==========================================
    rotate_key()
    
    if adx > 50: market_state = "⚠️ 過熱趨勢" # 提醒 AI 注意
    else: market_state = "🚀 健康趨勢"
    
    vol_state = "🔥 爆量" if rvol > 1.2 else "📈 放量"

    score_bull = row['SCORE_BULL']
    score_bear = row['SCORE_BEAR']
    
    prompt = f"""
    你是 V47 頂尖交易員。我們回歸了【V41 的獲利架構】：只做趨勢明確 (ADX>25) 且量能足夠 (RVOL>0.8) 的單。
    
    【市場數據】
    1. 趨勢 (ADX): {adx:.1f} ({market_state})
    2. 動能 (RVOL): {rvol:.2f} ({vol_state})
    3. RSI: {rsi:.1f} (已確認在 30-70 安全區)
    4. 乖離率: {ema_dist:.2f}%
    
    【智能評分】
    多頭: {score_bull:.1f} / 空頭: {score_bear:.1f}
    
    【決策任務】
    請進行最後確認 (這也是 V41 的核心邏輯)：
    1. **分數確認**：多空分數差距必須 > 15 (凱利過濾)。
    2. **趨勢一致**：做多時價格應在 EMA200 上方，做空應在下方。
    3. **避免背離**：雖然 RSI 在安全區，但如果價格創新高而 RSI 沒創新高 (背離)，請謹慎。
    
    回傳 JSON: {{"action": "BUY" | "SELL" | "WAIT", "reason": "分析原因"}}
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