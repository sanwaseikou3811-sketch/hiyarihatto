import streamlit as st
from datetime import datetime
import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# ==========================================
# ⚙️ 設定項目
# ==========================================
SPREADSHEET_NAME = "ヒヤリハット報告データ"  # 作成したスプレッドシート名
DRIVE_FOLDER_ID = "1JFjrPHZ3bFJQpKl6XR7E4OJmsXj2gxik"  # ドライブのフォルダID
# ==========================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    # 1. Streamlit CloudのSecretsから読み込む（クラウド環境）
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    # 2. ローカルのcredentials.jsonファイルから読み込む（手元PC環境）
    elif os.path.exists("credentials.json"):
        return Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return None

st.set_page_config(page_title="ヒヤリハット報告フォーム", layout="centered")

st.title("⚠️ ヒヤリハット報告フォーム")
st.write("現場でのヒヤリハット事例を報告してください。（ログイン不要）")

with st.form("near_miss_form", clear_on_submit=True):
    # 1. 名前入力
    name = st.text_input("氏名（お名前）", placeholder="例：山田 太郎")
    
    # 2. 写真の状況説明
    description = st.text_area("写真・状況の簡単な説明", placeholder="例：作業台の足元にコードが引っかかりそうになっていた。")
    
    # 3. 写真撮影（任意に変更）
    st.write("---")
    st.subheader("📷 現場の写真（任意・省略可能）")
    camera_image = st.camera_input("タップして写真を撮影してください（※撮らなくても送信できます）")
    
    submitted = st.form_submit_button("報告を送信する")

# 送信ボタンが押された時の処理
if submitted:
    if not name.strip():
        st.error("氏名を入力してください。")
    elif not description.strip():
        st.error("状況説明を入力してください。")
    else:
        try:
            creds = get_credentials()
            if creds is None:
                st.error("認証情報（credentials.json または Secrets）が見つかりません。")
            else:
                with st.spinner("データを送信・保存しています..."):
                    # 日時とファイル名の作成
                    now = datetime.now()
                    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
                    file_timestamp = now.strftime("%Y%m%d_%H%M%S")
                    
                    image_filename = "画像なし"
                    drive_link = "なし"
                    
                    # 写真が撮影されている場合のみドライブにアップロードする処理を行う
                    if camera_image is not None:
                        safe_name = name.strip().replace(" ", "_").replace(" ", "_")
                        image_filename = f"{safe_name}_{file_timestamp}.jpg"
                        
                        drive_service = build('drive', 'v3', credentials=creds)
                        file_metadata = {
                            'name': image_filename,
                            'parents': [DRIVE_FOLDER_ID]
                        }
                        media = MediaIoBaseUpload(io.BytesIO(camera_image.getbuffer()), mimetype='image/jpeg', resumable=True)
                        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                        drive_link = uploaded_file.get('webViewLink')
                    
                    # Googleスプレッドシートへデータを追加
                    gc = gspread.authorize(creds)
                    sheet = gc.open(SPREADSHEET_NAME).sheet1
                    
                    row_data = [
                        timestamp_str,
                        name,
                        description,
                        image_filename,
                        drive_link
                    ]
                    sheet.append_row(row_data)
                
                st.success("ヒヤリハット報告が完了しました！ご協力ありがとうございます。")
                st.balloons()

        except Exception as e:
            st.error(f"保存中にエラーが発生しました: {e}")