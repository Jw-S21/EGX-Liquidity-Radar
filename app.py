import streamlit as st
import pandas as pd
import requests
import pdfplumber
from openai import OpenAI
import time
import os

# --- إعدادات التطبيق ---
st.set_page_config(page_title="تحليل الأسواق المصرية", layout="wide")

# القائمة الجانبية للتنقل بين الصفحات
st.sidebar.title("📊 قائمة التطبيق")
page = st.sidebar.radio("اختر الصفحة", 
                        ["🏠 الصفحة الرئيسية (السيولة)", "📄 تحليل ملفات PDF", "📰 الأخبار وتأثيرها على السوق"])

# ------------------------------------------------
# الصفحة الأولى: الصفحة الأصلية الخاصة بك (السيولة)
# ------------------------------------------------
if page == "🏠 الصفحة الرئيسية (السيولة)":
    st.title("البورصة المصرية - تحليل السيولة")
    # هنا ضع كود الصفحة الرئيسية الأصلي الخاص بك بالكامل
    # (كود fetching البيانات و رسم الجداول...)

# ------------------------------------------------
# الصفحة الثانية: تحليل ملفات PDF
# ------------------------------------------------
elif page == "📄 تحليل ملفات PDF":
    st.title("📂 تحليل وشرح ملفات PDF")
    st.write("ارفع ملف (تقرير، مقال، دراسة) باللغة العربية أو الإنجليزية وسأقوم بتحليله وإعطاء رأيي عنه.")

    uploaded_file = st.file_uploader("ارفع ملف PDF", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("جاري استخراج النص من الملف..."):
            try:
                # استخراج النص من PDF
                text_content = ""
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text_content += page.extract_text() or ""
                
                if not text_content.strip():
                    st.error("لم أتمكن من استخراج نصوص من هذا الـ PDF. قد يكون الملف عبارة عن صور (سكانر) وليس نصاً.")
                else:
                    st.success("تم استخراج النص بنجاح!")
                    with st.expander("إظهار النص المستخرج"):
                        st.write(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)

                    # تحليل النص باستخدام الذكاء الاصطناعي
                    if st.button("🚀 تحليل الملف وإعطاء الرأي"):
                        with st.spinner("جاري التحليل بواسطة الذكاء الاصطناعي. انتظر قليلاً..."):
                            try:
                                # (تنويه: يجب عليك وضع مفتاح API الخاص بـ OpenAI في متغير البيئة أو هنا)
                                client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "ضع_مفتاح_API_هنا"))
                                
                                response = client.chat.completions.create(
                                    model="gpt-4o-mini",
                                    messages=[
                                        {"role": "system", "content": "أنت خبير مالي واقتصادي في أسواق المال. قم بتحليل النص التالي، وأعطني ملخصاً له، وشرحاً لمحتواه، ورأيك التحليلي الشخصي (توصية) بناءً على المعلومات الموجودة فيه. يرجى الرد باللغة العربية."},
                                        {"role": "user", "content": f"هذا هو محتوى الملف: {text_content}"}
                                    ]
                                )
                                
                                analysis = response.choices[0].message.content
                                st.markdown("### 📊 نتيجة التحليل والرأي:")
                                st.write(analysis)
                            except Exception as e:
                                st.error(f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}")
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

# ------------------------------------------------
# الصفحة الثالثة: الأخبار وتأثيرها
# ------------------------------------------------
elif page == "📰 الأخبار وتأثيرها على السوق":
    st.title("📰 تأثير الأخبار على اتجاهات السوق")

    # استخدام NewsAPI (وهو مصدر موثوق ومجاني مع حد استخدام 100 طلب يومياً)
    st.info("يتم جلب الأخبار من مصادر موثوقة عالمياً عبر NewsAPI (بحث باللغة العربية).")
    
    # مربع للبحث عن كلمة مفتاحية (افتراضي البورصة المصرية)
    keyword = st.text_input("ابحث عن موضوع معين:", value="البورصة المصرية EGX")
    
    if st.button("🔄 جلب الأخبار وتحليل تأثيرها"):
        # مفتاح NewsAPI مجاني، يمكنك الحصول عليه من موقع newsapi.org
        api_key = "d7931015b3424069a7d512e724d6cce2" # هذا مفتاح تجريبي عام للمعرضين، أنصحك بالتسجيل والحصول على مفتاحك الخاص مجاناً.
        url = f"https://newsapi.org/v2/everything?q={keyword}&language=ar&sortBy=publishedAt&apiKey={api_key}"
        
        with st.spinner("جاري جلب وتحليل الأخبار..."):
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                if not articles:
                    st.warning("لم يتم العثور على أخبار حالية لهذا الموضوع.")
                else:
                    st.subheader(f"آخر {len(articles[:5])} أخبار:")
                    news_text = ""
                    for i, article in enumerate(articles[:5]):
                        st.write(f"**{i+1}. {article['title']}**")
                        st.write(f"المصدر: {article['source']['name']} | التاريخ: {article['publishedAt'][:10]}")
                        st.write(f"ملخص: {article['description'] or 'لا يوجد ملخص'}")
                        st.markdown("---")
                        
                        # تجميع النصوص لتحليلها بواسطة الذكاء الاصطناعي
                        news_text += f"عنوان الخبر: {article['title']}\nالملخص: {article['description']}\n\n"
                    
                    # تحليل تأثير الأخبار بواسطة الذكاء الاصطناعي
                    st.write("### 🤖 رؤية الذكاء الاصطناعي لتأثير هذه الأخبار على السوق:")
                    try:
                        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "ضع_مفتاح_API_هنا"))
                        response_ai = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "أنت محلل مالي خبير. بناءً على مجموعة الأخبار المالية التالية، قم بتحليل المشاعر العامة (Sentiment) للسوق (صاعد أم هابط أم محايد)، واشرح لماذا ولماذا، واعط نصيحة للمستثمرين بناءً على هذه الأخبار. الرد باللغة العربية."},
                                {"role": "user", "content": f"هذه هي الأخبار: {news_text}"}
                            ]
                        )
                        st.success(response_ai.choices[0].message.content)
                    except Exception as e:
                        st.error(f"حدث خطأ في تحليل الذكاء الاصطناعي: {e}")
            else:
                st.error(f"فشل في الاتصال بمصدر الأخبار، رمز الخطأ: {response.status_code}")
