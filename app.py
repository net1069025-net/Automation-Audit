import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from io import BytesIO

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Multi-Platform Password Auditor", layout="wide")
st.title("🛡️ ระบบตรวจ Password Policy ทุก Platform ด้วย AI")

# ส่วนรับ API Key
api_key = st.sidebar.text_input("1. ใส่ Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

    # ส่วนรับนโยบายบริษัท
    st.subheader("2. นโยบายบริษัท (Master Policy)")
    company_policy = st.text_area(
        "ระบุนโยบายการตั้งรหัสผ่านที่นี่:",
        "เช่น: รหัสผ่านต้องยาวอย่างน้อย 12 ตัวอักษร, ต้องมีตัวอักษรใหญ่ เล็ก ตัวเลข และสัญลักษณ์, ต้องเปลี่ยนรหัสทุก 90 วัน และห้ามใช้รหัสซ้ำ 5 ครั้งล่าสุด"
    )

    # ส่วนอัปโหลดไฟล์ Config จากระบบต่างๆ
    st.subheader("3. ข้อมูลการตั้งค่าระบบ (System Configuration)")
    uploaded_files = st.file_uploader(
        "อัปโหลดไฟล์ที่ได้จากคำสั่งรันระบบ (TXT, LOG)", 
        type=['txt', 'log'], 
        accept_multiple_files=True
    )

    if st.button("🚀 เริ่มการตรวจสอบ (Start Audit)"):
        if not uploaded_files:
            st.warning("กรุณาอัปโหลดไฟล์ข้อมูลจากระบบก่อนครับ")
        else:
            all_results = []
            
            for uploaded_file in uploaded_files:
                file_content = uploaded_file.read().decode("utf-8")
                
                # สร้าง Prompt ที่ฉลาดพอจะแยกแยะ Platform เองได้
                prompt = f"""
                คุณคือผู้เชี่ยวชาญ IT Audit และ Cyber Security
                ภารกิจ: ตรวจสอบการตั้งค่ารหัสผ่านจากไฟล์ที่แนบมา ว่าตรงตามนโยบายบริษัทหรือไม่
                
                [นโยบายบริษัท]:
                {company_policy}
                
                [ข้อมูลการตั้งค่าในระบบ]:
                {file_content}
                
                คำสั่ง:
                1. วิเคราะห์ว่าไฟล์นี้มาจาก Platform อะไร (เช่น Windows, Linux, Cisco, SQL)
                2. เปรียบเทียบค่าต่อค่า (เช่น Min Password Length ในระบบ vs นโยบาย)
                3. ตอบกลับเป็น JSON List เท่านั้น ห้ามมีประโยคเกริ่นนำ:
                [
                  {{
                    "Platform": "ชื่อระบบ",
                    "Requirement": "ข้อกำหนดนโยบาย",
                    "System_Value": "ค่าที่ตั้งไว้จริงในระบบ",
                    "Status": "PASS หรือ FAIL",
                    "Recommendation": "สิ่งที่ต้องแก้ไข"
                  }}
                ]
                """
                
                with st.spinner(f'กำลังตรวจไฟล์ {uploaded_file.name}...'):
                    response = model.generate_content(prompt)
                    try:
                        # ลบ markdown ของ JSON ออกถ้ามี
                        clean_text = response.text.replace('```json', '').replace('```', '').strip()
                        data = json.loads(clean_text)
                        all_results.extend(data)
                    except:
                        st.error(f"ไฟล์ {uploaded_file.name} มีปัญหาในการประมวลผล")

            if all_results:
                df = pd.DataFrame(all_results)
                st.success("การตรวจสอบเสร็จสมบูรณ์!")
                
                # แสดงผลแบ่งตามสถานะ
                st.dataframe(df.style.applymap(
                    lambda x: 'background-color: #ffcccc' if x == 'FAIL' else ('background-color: #ccffcc' if x == 'PASS' else ''),
                    subset=['Status']
                ))

                # ฟีเจอร์ดาวน์โหลด Excel Report
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit_Summary')
                
                st.download_button(
                    label="📥 ดาวน์โหลดรายงานสรุปผล (Excel)",
                    data=output.getvalue(),
                    file_name="Password_Audit_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
else:
    st.info("กรุณาใส่ API Key ที่แถบด้านซ้าย เพื่อเปิดใช้งานโปรแกรม")