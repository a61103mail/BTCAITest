# B.py - AI 大腦 (V45: 全面硬體化版)
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
    # 🔥 V45 終極硬體防火牆 (The Great Wall)
    # ==========================================
    # 這裡的邏輯由 Python 強制執行，AI 無權插手
    
    rsi = row['RSI']
    adx = row['ADX']
    rvol = row['RVOL']
    ema_dist = row['EMA_DIST']
    
    # 1. 嚴格的 RSI 安全區 (35 ~ 65)
    if rsi > 65: 
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: RSI {rsi:.1f} 過熱 (>65)，風險過高"}
    if rsi < 35: 
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: RSI {rsi:.1f} 過冷 (<35)，風險過高"}

    # 2. 升級版 ADX 門檻 (25)
    # 之前的 20 太低，容易遇到死魚盤。現在只做 ADX > 25 的強趨勢。
    if adx < 25:
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: ADX {adx:.1f} 不足 25，趨勢不明顯"}
    
    # 3. 升級版 RVOL 門檻 (1.0)
    # 之前的 0.8 太寬鬆，AI 甚至會放行 0.73。現在強制要求 RVOL > 1.0 (至少要比平常量大)。
    if rvol < 1.0:
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: RVOL {rvol:.2f} 縮量 (<1.0)，缺乏動能"}
    
    # 4. 乖離率保護
    if abs(ema_dist) > 2.0:
        return {"action": "WAIT", "reason": f"🛑 硬體攔截: 乖離率 {ema_dist:.1f}% 過大，等待回歸"}

    # ==========================================
    # 通過防火牆的菁英單，才交給 AI 審核
    # ==========================================
    rotate_key()
    
    if adx > 50: market_state = "⚠️ 極度過熱"
    elif adx > 25: market_state = "🚀 強烈趨勢"
    else: market_state = "⚖️ 普通震盪" # 其實這邊已經不會出現了，因為上面擋掉了
    
    vol_state = "🔥 爆量" if rvol > 1.2 else "📈 放量"

    score_bull = row['SCORE_BULL']
    score_bear = row['SCORE_BEAR']
    
    prompt = f"""
    你是 V45 頂尖交易員。我們已經通過了最嚴格的【V45 防火牆】(RSI安全區, ADX>25 強趨勢, RVOL>1.0 放量)。
    現在每一筆單都是「有量有趨勢」的精華，請你進行最後的【結構確認】。
    
    【市場數據】
    1. 趨勢 (ADX): {adx:.1f} ({market_state})
    2. 動能 (RVOL): {rvol:.2f} ({vol_state})
    3. RSI: {rsi:.1f} (安全區)
    4. 乖離率: {ema_dist:.2f}% (安全區)
    
    【智能評分】
    多頭: {score_bull:.1f} / 空頭: {score_bear:.1f}
    
    【決策任務】
    請檢查最後一哩路：
    1. **分數確認**：多空分數差距是否 > 15？(這是凱利公式的基礎)
    2. **趨勢一致性**：如果是做多，價格是否在 EMA200 之上？做空是否在之下？
    
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