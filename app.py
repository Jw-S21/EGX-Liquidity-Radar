import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pdfplumber
import feedparser
import urllib.parse
import google.generativeai as genai
import time
import os

# ==========================================
# إعدادات الصفحة الأساسية
# ==========================================
st.set_page_config(page_title="تحليل الأسواق المصرية", layout="wide")

# قائمة التنقل الجانبية
st.sidebar.title("📊 قائمة التطبيق")
page = st.sidebar.radio("اختر الصفحة", 
                        ["🏠 الصفحة الرئيسية (السيولة)", "📄 تحليل ملفات PDF", "📰 الأخبار وتأثيرها على السوق"])

# ==========================================
# الصفحة 1: كود السيولة الأصلي الخاص بك
# ==========================================
if page == "🏠 الصفحة الرئيسية (السيولة)":
    st.title("البورصة المصرية - تحليل السيولة")
    
    # ==========================================
    # ⚠️ هام جداً: ضع كود التطبيق الأصلي الخاص بك هنا!
    # ==========================================
    # مثال توضيحي لما يوجد عندك (استبدل هذا بـ كود yfinance وبياناتك الفعلية):
    st.info("🚨 يرجى حذف هذا النص واستبداله بكود الصفحة الرئيسية الذي كنت تستخدمه مسبقاً لتحليل السيولة.")
    
    # كود تجريبي وهمي للتوضيح (يجب حذفه)
    data = {'الشركة': ['EGX30', 'EGX70', 'السيولة الكلية'], 'القيمة': [29500, 1800, 739589815]}
    df = pd.DataFrame(data)
    st.dataframe(df)
    # ==========================================

# ==========================================
# الصفحة 2: تحليل ملفات PDF (بدون أخطاء)
# ==========================================
elif page == "📄 تحليل ملفات PDF":
    st.title("📂 تحليل وشرح ملفات PDF")
    st.info("لتحليل الملفات، أحتاج لمفتاح API من Google Gemini (مجاني). اشترك في Google AI Studio (https://aistudio.google.com/app/apikey) وانشئ مفتاح.")

    # حقل لإدخال مفتاح API (آمن ولا يتم حفظه)
    user_api_key = st.text_input("أدخل مفتاح API الخاص بـ Gemini:", type="password")

    uploaded_file = st.file_uploader("ارفع ملف PDF", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("جاري استخراج النص من الملف..."):
            try:
                text_content = ""
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text_content += extracted
                
                if not text_content.strip():
                    st.error("الملف عبارة عن صور (سكانر) ولا يحتوي على نصوص قابلة للاستخراج.")
                else:
                    st.success("تم استخراج النص بنجاح!")
                    with st.expander("إظهار النص المستخرج"):
                        st.write(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)

                    if st.button("🚀 تحليل الملف وإعطاء الرأي"):
                        if not user_api_key:
                            st.warning("الرجاء إدخال مفتاح API من Google Gemini أولاً.")
                        else:
                            with st.spinner("جاري التحليل بواسطة الذكاء الاصطناعي (Gemini)..."):
                                try:
                                    genai.configure(api_key=user_api_key)
                                    # استخدام الإصدار الأحدث والأكثر استقراراً
                                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                                    
                                    prompt = f"أنت خبير مالي واقتصادي في أسواق المال. قم بتحليل النص التالي، وأعطني ملخصاً له، وشرحاً لمحتواه، ورأيك التحليلي الشخصي (توصية) بناءً على المعلومات الموجودة فيه. يرجى الرد باللغة العربية. النص: {text_content[:30000]}" # تحديد طول النص لتجنب تجاوز حد الـ API
                                    
                                    response = model.generate_content(prompt)
                                    st.markdown("### 📊 نتيجة التحليل والرأي:")
                                    st.write(response.text)
                                except Exception as e:
                                    st.error(f"حدث خطأ في مفتاح API أو الاتصال: {e}")
            except Exception as e:
                st.error(f"خطأ في قراءة الملف: {e}")

# ==========================================
# الصفحة 3: الأخبار وتأثيرها (مع إصلاح رابط RSS)
# ==========================================
elif page == "📰 الأخبار وتأثيرها على السوق":
    st.title("📰 تأثير الأخبار على اتجاهات السوق")
    st.success("يتم جلب الأخبار مباشرة من خدمة Google News RSS (مجانية تماماً وبدون مفتاح).")
    
    keyword = st.text_input("ابحث عن موضوع معين:", value="البورصة المصرية")
    
    if st.button("🔄 جلب الأخبار وتحليل تأثيرها"):
        with st.spinner("جاري جلب الأخبار..."):
            try:
                # الخطوة الذهبية: تشفير الكلمات العربية والمسافات لتصبح صالحة للرابط
                encoded_keyword = urllib.parse.quote(keyword)
                rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ar&gl=EG&ceid=EG:ar"
                
                # جلب البيانات
                response = requests.get(rss_url)
                
                if response.status_code == 200:
                    # تحليل محتوى الـ RSS
                    feed = feedparser.parse(response.content)
                    
                    if not feed.entries:
                        st.warning("لم يتم العثور على أخبار حالية لهذا الموضوع.")
                    else:
                        st.subheader(f"آخر 5 أخبار من Google News:")
                        news_text = ""
                        
                        for i, entry in enumerate(feed.entries[:5]):
                            # تنظيف النص من أكواد HTML
                            summary_text = entry.summary.replace('<font color=\"#6f6f6f\">', '').replace('</font>', '')
                            summary_text = summary_text.replace('<b>', '').replace('</b>', '')
                            
                            st.write(f"**{i+1}. {entry.title}**")
                            st.write(f"المصدر: {entry.source.title if hasattr(entry, 'source') else 'مصدر غير معروف'} | التاريخ: {entry.published[:10] if hasattr(entry, 'published') else 'تاريخ غير معروف'}")
                            st.write(f"ملخص: {summary_text}")
                            st.markdown("---")
                            
                            news_text += f"عنوان الخبر: {entry.title}\nالملخص: {summary_text}\n\n"
                        
                        st.divider()
                        st.write("### 🤖 رؤية الذكاء الاصطناعي لتأثير هذه الأخبار:")
                        
                        # التحليل بواسطة الذكاء الاصطناعي
                        user_api_key = st.text_input("أدخل مفتاح Gemini هنا لتحليل توصية السوق:", type="password", key="news_key")
                        
                        if user_api_key:
                            with st.spinner("جاري تحليل التأثير..."):
                                try:
                                    genai.configure(api_key=user_api_key)
                                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                                    
                                    prompt = f"أنت محلل مالي خبير. بناءً على مجموعة الأخبار المالية التالية، قم بتحليل المشاعر العامة (Sentiment) للسوق (صاعد أم هابط أم محايد)، واشرح لماذا، واعط نصيحة للمستثمرين بناءً على هذه الأخبار. الرد باللغة العربية. الأخبار: {news_text}"
                                    
                                    response_ai = model.generate_content(prompt)
                                    st.success(response_ai.text)
                                except Exception as e:
                                    st.warning(f"حدث خطأ في التحليل: {e}. تأكد من أن مفتاح Gemini صحيح.")
                        else:
                            st.info("لتحليل تأثير الأخبار، يرجى كتابة مفتاح Google Gemini الخاص بك في الحقل أعلاه.")
                else:
                    st.error(f"فشل الاتصال بخدمة Google News، رمز الخطأ: {response.status_code}")
            except Exception as e:
                st.error(f"حدث خطأ تقني أثناء جلب الأخبار: {e}")
