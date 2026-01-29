# B.py - AI 大腦 (V41: 車子與油邏輯)
import google.generativeai as genai
import json
import warnings
import time
import os
from dotenv import load_dotenv

# 🔥 強制指定 .env 路徑 (修復讀取不到的問題)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

# ==========================================
# 🔑 API KEY 池
# ==========================================
keys_str = os.getenv("GEMINI_KEYS")
if not keys_str:
    print(f"❌ 錯誤：在 {env_path} 找不到 GEMINI_KEYS")
    raise ValueError("找不到 GEMINI_KEYS")

API_KEYS = [k.strip() for k in keys_str.split(',') if k.strip()]
# ==========================================

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
    rotate_key()
    
    # --- V41 新增邏輯：車子與油 ---
    adx_val = row['ADX']
    rvol = row['RVOL']
    
    market_state = "強烈趨勢" if adx_val > 25 else "盤整震盪"
    
    # 判斷油量狀態
    if rvol > 1.2:
        vol_state = "🔥 爆量 (動力充足)"
    elif rvol < 0.8:
        vol_state = "💤 縮量 (動力不足)"
    else:
        vol_state = "⚖️ 正常量"

    score_bull = row['SCORE_BULL']
    score_bear = row['SCORE_BEAR']
    
    prompt = f"""
    你是 V41 高階量化交易員。請結合「趨勢(ADX)」與「動能(Volume)」進行決策：
    
    【市場環境分析】
    1. 趨勢強度 (ADX): {adx_val:.1f} ({market_state}) -> 這代表車子的速度。
    2. 量能動力 (RVOL): {rvol:.2f} ({vol_state}) -> 這代表車子的油量。
       ⚠️ 警告: RVOL < 0.8 代表沒油了，就算指標有訊號，也極大機率是假突破 (插針)，請回傳 WAIT。
       ⚠️ 提示: RVOL > 1.2 代表油量充足，若配合分數高，勝率極高。
    
    【V39 智能評分】
    多頭: {score_bull:.1f} / 空頭: {score_bear:.1f}
    
    【技術數據】
    價格: {row['close']}
    EMA200: {row['EMA_200']:.1f}
    RSI: {row['RSI']:.1f}
    MACD: {row['MACD_HIST']:.4f}
    
    【操作規則】
    1. **嚴禁無量交易**：如果 RVOL < 0.8，除非分數高達 85 分以上，否則一律 WAIT。
    2. **順勢而為**：當 ADX > 25 時，請嚴格遵守 EMA200 方向。
    3. **凱利過濾**：多空分數差距需 > 15 分才考慮進場。
    
    回傳 JSON: {{"action": "BUY" | "SELL" | "WAIT", "reason": "分析原因 (請包含對 RVOL 量能的看法)"}}
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