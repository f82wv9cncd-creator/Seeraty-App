
import streamlit as st
import os
import time
import json
import base64
from datetime import datetime
from openai import OpenAI
import PyPDF2
from docx import Document
from pptx import Presentation
from PIL import Image
import pandas as pd

# ---------------------------------------------------------
# إعدادات الصفحة والهوية البصرية
# ---------------------------------------------------------
st.set_page_config(page_title="سيرتي | Seeraty", layout="wide", page_icon="📄")

# CSS: تصميم نظيف، احترافي، وخطوط عربية رسمية
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
html, body, [class*='css'] {font-family: 'Tajawal', sans-serif;}

/* العناوين */
.main-title {text-align: center; font-size: 48px; font-weight: 800; color: #0f172a; margin-bottom: 10px;}
.sub-title {text-align: center; font-size: 18px; color: #64748b; margin-bottom: 40px;}

/* الأزرار */
.stButton>button {
    width: 100%; border-radius: 10px; height: 3.5em; 
    background-color: #0f172a; color: white; font-weight: bold; border: none;
    transition: all 0.3s ease;
}
.stButton>button:hover {background-color: #334155; transform: scale(1.01);}

/* بطاقات النتائج */
/* بطاقات النتائج - تعديل لإصلاح الوضع الليلي */
.result-card {
    background-color: #ffffff; 
    padding: 25px; 
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border: 1px solid #e2e8f0; 
    margin-bottom: 20px;
    color: #000000 !important; /* 👈 هذا الأمر يخلي الخط أسود غصب */
}
}
.salary-box {
    background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #166534;
    padding: 20px; border-radius: 10px; text-align: center; font-size: 20px; font-weight: bold;
}
.error-message {
    background-color: #fef2f2; border: 1px solid #fecaca; color: #991b1b;
    padding: 15px; border-radius: 8px; text-align: center; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# الخدمات الخلفية (Backend Services)
# ---------------------------------------------------------
LOG_FILE = "admin_logs.json"
‏server_key ="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"

def log_data(file_type, status, notes=""):
    """تسجيل البيانات في لوحة التحكم المخفية"""
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_type": file_type,
        "status": status,
        "notes": notes
    }
    try:
        data = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: data = json.load(f)
        data.append(entry)
        with open(LOG_FILE, "w") as f: json.dump(data, f)
    except: pass

def extract_text(file):
    """استخراج النصوص بذكاء من جميع الامتدادات"""
    name = file.name.lower()
    text = ""
    img_b64 = None

    try:
        if name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif name.endswith(".docx"):
            doc = Document(file)
            for p in doc.paragraphs: text += p.text + "\n"
        elif name.endswith(".pptx"):
            prs = Presentation(file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"): text += shape.text + "\n"
        elif name.endswith(".txt"):
            text = file.read().decode("utf-8")
        elif name.endswith((".png", ".jpg", ".jpeg")):
            img_b64 = base64.b64encode(file.read()).decode("utf-8")
            text = "IMAGE_MODE"

        return text, img_b64
    except Exception as e:
        return None, None

# ---------------------------------------------------------
# الواجهة الرئيسية
# ---------------------------------------------------------

# لوحة التحكم المخفية
with st.sidebar:
    st.markdown("### 🔒 لوحة الإدارة")
    pwd = st.text_input("كلمة المرور", type="password", label_visibility="collapsed")
    if pwd == "Admin@123":
        st.success("تم الدخول: لوحة التحكم")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: logs = json.load(f)
            df = pd.DataFrame(logs)
            st.metric("إجمالي الملفات المرفوعة", len(df))
            st.dataframe(df)
        else:
            st.info("لا توجد بيانات مسجلة.")

# الرأس
st.markdown('<div class="main-title">سيرتي</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">نظام التحليل المهني وتطوير السيرة الذاتية</div>', unsafe_allow_html=True)

# منطقة الرفع
uploaded_file = st.file_uploader("قم برفع السيرة الذاتية (PDF, Word, صور) لبدء التحليل", type=["pdf", "docx", "pptx", "png", "jpg", "jpeg"])

# زر التشغيل
if st.button("🚀 ابدأ التحليل الاحترافي"):
    if not server_key:
        st.error("⚠️ خطأ في النظام: لم يتم العثور على مفتاح API.")
    elif not uploaded_file:
        st.warning("⚠️ الرجاء رفع ملف السيرة الذاتية أولاً.")
    else:
        # حاوية الحالة
        status_box = st.status("جاري معالجة الملف...", expanded=True)

        try:
            # 1. استخراج المحتوى
            status_box.write("📂 قراءة محتوى الملف...")
            content, img_data = extract_text(uploaded_file)

            if not content:
                status_box.update(label="فشل القراءة", state="error")
                st.markdown('<div class="error-message">عذراً، الملف تالف أو لا يمكن قراءته.</div>', unsafe_allow_html=True)
                log_data("Unknown", "Failed", "File Corrupt")
                st.stop()

            # إعداد العميل
            client = OpenAI(api_key=server_key)

            # 2. المرحلة الأولى: الفرز الصارم (Validation)
            status_box.write("🕵️‍♂️ التحقق من هوية الملف (فلتر الأمان)...")

            validation_prompt = """
            أنت خبير تدقيق وثائق. مهمتك الوحيدة هي تحديد نوع الملف بدقة متناهية.

            هل المحتوى المرفق هو "سيرة ذاتية" (Resume/CV) لشخص يبحث عن عمل؟
            يجب أن يحتوي على (معلومات اتصال، خبرات، تعليم، مهارات) بشكل واضح.

            إذا كان: عرض تقديمي، كتاب، مقال، فاتورة، صورة شخصية بدون نص، أو نص عشوائي -> ارفضه فوراً.

            الرد المطلوب (كلمة واحدة فقط):
            VALID (إذا كان سيرة ذاتية).
            INVALID (إذا كان أي شيء آخر).
            """

            # إرسال المحتوى (نص أو صورة) للفحص
            msgs = [{"role": "system", "content": validation_prompt}]
            if content == "IMAGE_MODE":
                msgs.append({"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}]})
            else:
                msgs.append({"role": "user", "content": content[:3000]})

            check_res = client.chat.completions.create(model="gpt-4o", messages=msgs)
            is_valid = check_res.choices[0].message.content.strip()

            if "INVALID" in is_valid:
                status_box.update(label="تم رفض الملف", state="error")
                st.markdown('<div class="error-message">🛑 عذراً، الملف المرفق لا يبدو كسيرة ذاتية صحيحة.<br>الرجاء رفع ملف CV يحتوي على بيانات واضحة.</div>', unsafe_allow_html=True)
                log_data(uploaded_file.type, "Rejected", "Not a CV")
                st.stop()

            # 3. المرحلة الثانية: التحليل الشامل (The Core Analysis)
            status_box.write("🧠 جاري تحليل المهارات وحساب الرواتب المتوقعة...")

            analysis_prompt = """
            تصرف كمستشار توظيف خبير في السوق السعودي والخليجي ومدير موارد بشرية.
            قم بتحليل هذه السيرة الذاتية تحليلاً دقيقاً ومفصلاً.

            المطلوب منك استخراج المعلومات التالية وترتيبها بدقة:

            1. **توقع الراتب (Salary Prediction):**
               - بناءً على المسمى الوظيفي، سنوات الخبرة، والمهارات في الملف.
               - حدد نطاق الراتب التقريبي بالريال السعودي (SAR) في السوق حالياً.

            2. **تقييم القوة (Score):**
               - اعط تقييماً من 100.
               - حدد مستوى المرشح (مبتدئ / متوسط / خبير).

            3. **الأخطاء والنواقص (Critical Gaps):**
               - اذكر الأخطاء الموجودة فعلياً في الملف (إملائية، تنسيقية، نقص في البيانات).
               - لا تخترع أخطاء غير موجودة.

            4. **الدورات والشهادات المقترحة (Recommendations):**
               - اقترح 3-5 شهادات مهنية أو دورات تقنية (مع أسمائها الإنجليزية) ترفع من راتب هذا الشخص في مجاله تحديداً.

            5. **نصيحة ذهبية:**
               - جملة واحدة مختصرة لتحسين القبول.

            تنسيق الرد: يجب أن يكون الرد باللغة العربية الفصحى، منسقاً بعناوين واضحة، وجاهزاً للعرض المباشر.
            """

            # إعادة إرسال المحتوى للتحليل العميق
            msgs[0]["content"] = analysis_prompt # تحديث النظام

            final_res = client.chat.completions.create(model="gpt-4o", messages=msgs, temperature=0.4)
            report = final_res.choices[0].message.content

            status_box.update(label="✅ تم اكتمال التحليل بنجاح!", state="complete", expanded=False)
            log_data(uploaded_file.type, "Success", "Analyzed")

            # 4. عرض النتائج
            st.markdown("---")

            # تقسيم التقرير للعرض
            st.markdown(f'<div class="result-card">{report}</div>', unsafe_allow_html=True)

            st.info("💡 ملاحظة: هذا التحليل يعتمد على الذكاء الاصطناعي وقد يختلف الواقع قليلاً حسب الشركة والمنطقة.")

        except Exception as e:
            status_box.update(label="حدث خطأ", state="error")
            st.error(f"حدث خطأ غير متوقع: {e}")
            log_data("Error", "Crash", str(e))
