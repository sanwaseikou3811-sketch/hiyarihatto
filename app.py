import streamlit as st
from datetime import datetime
import base64
import requests
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# ⚙️ 設定項目
# ==========================================
SPREADSHEET_NAME = "ヒヤリハット報告データ"  # スプレッドシート名
IMGBB_API_KEY = "ここに取得したImgBBのAPIキーを入力"  # ← ★取得したAPIキーを設定
# ==========================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

def get_credentials():
    # Streamlit Cloudの Secrets から認証情報を読み込む場合
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    return None

st.set_page_config(page_title="ヒヤリハット報告フォーム", layout="centered")

st.title("⚠️ ヒヤリハット報告フォーム")
st.write("現場でのヒヤリハット事例を報告してください。（ログイン不要）")

with st.form("near_miss_form", clear_on_submit=True):
    name = st.text_input("氏名（お名前）", placeholder="例：山田 太郎")
    description = st.text_area("状況の簡単な説明", placeholder="例：作業台の足元にコードが引っかかりそうになっていた。")
    
    st.write("---")
    st.subheader("📷 現場の写真（任意）")
    camera_image = st.camera_input("タップして写真を撮影してください")
    
    submitted = st.form_submit_button("報告を送信する")

if submitted:
    if not name.strip():
        st.error("氏名を入力してください。")
    elif not description.strip():
        st.error("状況説明を入力してください。")
    else:
        try:
            creds = get_credentials()
            if creds is None:
                st.error("認証情報（Secrets）が設定されていません。")
            else:
                with st.spinner("データを送信しています..."):
                    now = datetime.now()
                    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
                    
                    image_url = "画像なし"
                    
                    # 1. 写真がある場合、ImgBBにアップロードして公開URLを取得
                    if camera_image is not None:
                        bytes_data = camera_image.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                        
                        url = "https://api.imgbb.com/1/upload"
                        payload = {
                            "key": IMGBB_API_KEY,
                            "image": base64_image,
                        }
                        
                        response = requests.post(url, data=payload)
                        result = response.json()
                        
                        if result.get("success"):
                            # アップロードされた画像の閲覧用URLを取得
                            image_url = result["data"]["url"]
                        else:
                            st.warning("画像のアップロードに失敗しましたが、テキストのみ記録します。")
                    
                    # 2. スプレッドシートにテキストと画像のURLを記録
                    gc = gspread.authorize(creds)
                    sheet = gc.open(SPREADSHEET_NAME).sheet1
                    
                    row_data = [
                        timestamp_str,
                        name,
                        description,
                        image_url
                    ]
                    sheet.append_row(row_data)
                
                st.success("ヒヤリハット報告が完了しました！ご協力ありがとうございます。")
                st.balloons()

        except Exception as e:
            st.error(f"保存中にエラーが発生しました: {e}")