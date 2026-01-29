# debug_env.py - 用來檢查 Key 到底躲在哪裡
import os
from dotenv import load_dotenv, find_dotenv

print("🔍 開始偵測環境變數來源...\n")

# 1. 先檢查還沒載入 .env 之前，系統裡有沒有？
sys_key = os.environ.get("GEMINI_KEYS")
if sys_key:
    print(f"⚠️ 驚！在【系統環境變數】裡發現了 Key！")
    print("   -> 這代表 Key 被存到你的 Windows/Linux 系統設定裡了，跟 .env 無關。")
else:
    print("✅ 系統環境變數裡很乾淨，沒有發現 Key。")

# 2. 嘗試尋找 .env 檔案
env_file = find_dotenv()
if env_file:
    print(f"⚠️ 驚！發現殘留的 .env 檔案！")
    print(f"   -> 藏身處: {env_file}")
    load_dotenv(env_file)
else:
    print("✅ 掃描確認：目前目錄與上層目錄都找不到 .env 檔案。")

# 3. 最終確認
final_key = os.getenv("GEMINI_KEYS")
print("-" * 30)
if final_key:
    print(f"👻 結論：程式依然能讀到 Key (前4碼: {final_key[:4]}...)")
    print("   -> 如果上方顯示找不到 .env，那就是 VS Code 終端機快取的問題。")
    print("   -> 請按終端機右上角的『垃圾桶』圖示，開一個新的再試一次。")
else:
    print("🎉 結論：程式讀不到 Key 了！(這才是正常的)")
    print("   -> 現在你可以放心地把 .env 檔案放回去了。")