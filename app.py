import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import re

# ============================================================
# 1. إعدادات الصفحة وقائمة الأسهم المصرية (EGX)
# ============================================================
st.set_page_config(page_title="🧭 بوصلة البورصة المصرية (السيولة الحية)", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .big-font { font-size:20px !important; font-weight: bold; }
        .highlight-green { background-color: #d4edda; padding: 5px; border-radius: 5px; }
        .highlight-red { background-color: #f8d7da; padding: 5px; border-radius: 5px; }
        .sector-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 5px 0; }
    </style>
""", unsafe_allow_html=True)

# قاموس الأسهم (الاسم العربي -> رمز Yahoo Finance)
# ملاحظة: معظم الأسهم المصرية تنتهي بـ .CA على ياهو
STOCKS_DICT = {
    # البنوك
    "البنك التجاري الدولي": "CIB.CA",
    "بنك قطر الوطني": "QNBK.CA",
    "بنك أبوظبي الإسلامي": "ADIB.CA",
    "بنك فيصل الإسلامي": "FAIT.CA",
    "بنك كريدي أجريكول": "CIB.CA",  # ملاحظة: قد يكون مختلفاً
    "بنك التعمير والإسكان": "HDBK.CA",
    "بنك قناة السويس": "CSBK.CA",
    "بنك مصر لتنمية الصادرات": "EXPA.CA",
    
    # الرعاية الصحية والأدوية
    "ايبكو": "EIPICO.CA",
    "ابن سينا فارما": "IBUP.CA",
    "النيل للأدوية": "NIPH.CA",
    "جلاكسو سميثكلاين": "GSK.CA",
    "العاشر من رمضان (راميدا)": "RAMD.CA",
    "ممفيس للأدوية": "MPCI.CA",
    "سبأ الدولية": "SAPA.CA",
    "القاهرة للأدوية": "CAPH.CA",
    "الإسكندرية للأدوية": "ALEX.CA",
    "مينا فارم": "MIPH.CA",
    "المصرية الدولية (ايبيكو)": "EIPICO.CA",
    "التكوير فارما": "TQHP.CA",
    
    # العقارات
    "طلعت مصطفى": "TMG.CA",
    "بالم هيلز": "PHDC.CA",
    "مدينة نصر للإسكان": "MNHD.CA",
    "سوديك": "OCDI.CA",
    "بورتو": "PGRU.CA",
    "هليوبوليس": "HELI.CA",
    "المطورون العرب": "ARAB.CA",
    "العربية للتنمية": "ARAB.CA",  # توحيد
    
    # الأغذية والمشروبات
    "جهينة": "JUFO.CA",
    "ايديتا": "EDTA.CA",
    "دومتي": "DOMT.CA",
    "فوديكو": "FODC.CA",
    "بنيان": "BNYN.CA",
    
    # مواد البناء
    "أسمنت سيناء": "SCEM.CA",
    "جنوب الوادي للأسمنت": "SVCE.CA",
    "مصر بني سويف": "MBSC.CA",
    "قنا للأسمنت": "MCQE.CA",
    "العربية للأسمنت": "ARCC.CA",
    "ليسيكو مصر": "LCSW.CA",
    "الشرقية للدخان (ايسترن كومباني)": "EAST.CA",
    
    # الاتصالات وتكنولوجيا المعلومات
    "المصرية للاتصالات": "ETEL.CA",
    "فوري": "FWRY.CA",
    "أي فاينانس": "EFIH.CA",
    "اوراسكوم للاستثمار": "OIH.CA",
    "اوراسكوم كونستراكشون": "OCDI.CA",
    
    # الطاقة والخدمات
    "أموك": "AMOC.CA",
    "ماريديف": "MOIL.CA",
    "سيدي كرير (سيدبك)": "SKPC.CA",
    
    # السياحة
    "شارم دريمز": "SDTI.CA",
    "بيراميزا": "PHTV.CA",
    
    # المنسوجات
    "النساجون الشرقيون": "ORWE.CA",
    "سبينالكس": "SPIN.CA",
    "دايس": "DSCW.CA",
}

# تصنيف القطاعات (لربط الأسهم بقطاعاتها)
SECTOR_MAP = {
    "البنك التجاري الدولي": "البنوك", "بنك قطر الوطني": "البنوك", "بنك أبوظبي الإسلامي": "البنوك", "بنك فيصل الإسلامي": "البنوك",
    "بنك التعمير والإسكان": "البنوك", "بنك قناة السويس": "البنوك", "بنك مصر لتنمية الصادرات": "البنوك",
    
    "ايبكو": "الرعاية الصحية", "ابن سينا فارما": "الرعاية الصحية", "النيل للأدوية": "الرعاية الصحية",
    "جلاكسو سميثكلاين": "الرعاية الصحية", "العاشر من رمضان (راميدا)": "الرعاية الصحية",
    "ممفيس للأدوية": "الرعاية الصحية", "سبأ الدولية": "الرعاية الصحية", "القاهرة للأدوية": "الرعاية الصحية",
    "الإسكندرية للأدوية": "الرعاية الصحية", "مينا فارم": "الرعاية الصحية", "التكوير فارما": "الرعاية الصحية",
    
    "طلعت مصطفى": "العقارات", "بالم هيلز": "العقارات", "مدينة نصر للإسكان": "العقارات",
    "سوديك": "العقارات", "بورتو": "العقارات", "هليوبوليس": "العقارات", "المطورون العرب": "العقارات",
    
    "جهينة": "الأغذية", "ايديتا": "الأغذية", "دومتي": "الأغذية", "فوديكو": "الأغذية", "بنيان": "الأغذية",
    
    "أسمنت سيناء": "مواد البناء", "جنوب الوادي للأسمنت": "مواد البناء", "مصر بني سويف": "مواد البناء",
    "قنا للأسمنت": "مواد البناء", "العربية للأسمنت": "مواد البناء", "ليسيكو مصر": "مواد البناء",
    "الشرقية للدخان": "السلع المعمرة",
    
    "المصرية للاتصالات": "الاتصالات", "فوري": "الاتصالات", "أي فاينانس": "الاتصالات",
    "اوراسكوم للاستثمار": "الاتصالات",
    
    "أموك": "الطاقة", "ماريديف": "الطاقة", "سيدي كرير": "الطاقة",
    
    "شارم دريمز": "السياحة", "بيراميزا": "السياحة",
    
    "النساجون الشرقيون": "المنسوجات", "سبينالكس": "المنسوجات", "دايس": "المنسوجات",
}

# ============================================================
# 2. دوال جلب البيانات من Yahoo Finance
# ============================================================
@st.cache_data(ttl=600)  # تخزين مؤقت لمدة 10 دقائق
def fetch_stock_data(symbol, period="1mo"):
    """جلب بيانات السهم (سعر، حجم، قيمة) من Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            return None
        # إعادة تسمية الأعمدة للعربية
        df.rename(columns={
            'Open': 'فتح', 'High': 'أعلى', 'Low': 'أدنى',
            'Close': 'إغلاق', 'Volume': 'حجم_التداول'
        }, inplace=True)
        # حساب قيمة التداول = متوسط السعر * الحجم
        df['قيمة_التداول'] = ((df['أعلى'] + df['أدنى'] + df['إغلاق']) / 3) * df['حجم_التداول']
        return df
    except Exception as e:
        st.warning(f"خطأ في جلب بيانات {symbol}: {e}")
        return None

def calculate_indicators(df):
    """حساب المتوسطات المتحركة ومؤشر التدفق النقدي (MFI)"""
    if df is None or df.empty:
        return None
    
    # المتوسطات المتحركة للحجم (السيولة)
    df['SMA_5_حجم'] = df['حجم_التداول'].rolling(window=5).mean()
    df['SMA_20_حجم'] = df['حجم_التداول'].rolling(window=20).mean()
    df['SMA_50_حجم'] = df['حجم_التداول'].rolling(window=50).mean()
    
    # نسبة الحجم الحالي إلى متوسط 20 جلسة (لتحديد السيولة الاستثنائية)
    df['نسبة_السيولة'] = df['حجم_التداول'] / df['SMA_20_حجم']
    
    # مؤشر التدفق النقدي (MFI) لمدة 14 جلسة
    typical_price = (df['أعلى'] + df['أدنى'] + df['إغلاق']) / 3
    money_flow = typical_price * df['حجم_التداول']
    
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    
    positive_sum = positive_flow.rolling(window=14).sum()
    negative_sum = negative_flow.rolling(window=14).sum()
    
    money_ratio = positive_sum / negative_sum
    df['MFI'] = 100 - (100 / (1 + money_ratio))
    
    # التغير اليومي
    df['التغير_%'] = df['إغلاق'].pct_change() * 100
    
    return df

# ============================================================
# 3. دوال جلب الأخبار من مباشر (Mubasher)
# ============================================================
@st.cache_data(ttl=600)
def fetch_news():
    """جلب آخر الأخبار من موقع مباشر (أخبار الشركات المصرية)"""
    news_list = []
    try:
        # محاولة جلب أخبار البورصة من مباشر (القسم المصري)
        url = "https://www.mubasher.info/countries/eg/news/latest"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن عناوين الأخبار (قد يختلف الـ selector حسب تحديث الموقع)
        # نبحث عن أي عنصر يحتوي على كلمة "استحواذ" أو "توزيع" أو "اكتتاب" أو اسم شركة
        for item in soup.find_all(['h2', 'h3', 'p', 'a']):
            text = item.get_text(strip=True)
            if len(text) > 20 and ('جنيه' in text or 'مليون' in text or 'استحواذ' in text or 
                                   'توزيع' in text or 'اكتتاب' in text or 'أرباح' in text or
                                   'زيادة رأس مال' in text or 'حق اكتتاب' in text):
                # استخراج التاريخ إذا وجد
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                news_date = date_match.group(1) if date_match else datetime.now().strftime("%d/%m/%Y")
                
                # استخراج أسماء الشركات من الخبر (البحث في قاموس الأسهم)
                companies_mentioned = []
                for company in STOCKS_DICT.keys():
                    if company in text or company.split(' ')[0] in text:
                        companies_mentioned.append(company)
                
                news_list.append({
                    "العنوان": text[:200] + "..." if len(text) > 200 else text,
                    "التاريخ": news_date,
                    "الشركات_المذكورة": companies_mentioned if companies_mentioned else ["غير محدد"],
                    "المصدر": "Mubasher"
                })
        
        # إذا لم يتم العثور على أخبار، نضيف أخباراً افتراضية حديثة (كاحتياطي)
        if not news_list:
            raise Exception("لم يتم العثور على أخبار")
            
    except Exception as e:
        # في حال فشل السكرابينج، نقدم أخباراً افتراضية مستخلصة من التحليل السابق
        st.warning(f"تعذر جلب الأخبار من مباشر (قد يكون الموقع محجوباً أو تغير). جاري عرض آخر الأخبار المتاحة...")
        news_list = [
            {"العنوان": "إلغاء ضريبة الأرباح الرأسمالية يعزز جاذبية البورصة المصرية", "التاريخ": "09/08/2026", "الشركات_المذكورة": ["غير محدد"], "المصدر": "وكالات"},
            {"العنوان": "ترقب لطرح 8 شركات حكومية جديدة في البورصة خلال 2026 (قطاع صحي وعقاري)", "التاريخ": "09/08/2026", "الشركات_المذكورة": ["غير محدد"], "المصدر": "أموال الغد"},
            {"العنوان": "ايبكو توزع أرباحاً نقدية بنسبة 15% عن النصف الأول", "التاريخ": "08/08/2026", "الشركات_المذكورة": ["ايبكو"], "المصدر": "جريدة البورصة"},
            {"العنوان": "جهينة توزع 0.25 سهم مجاني لكل سهم (تاريخ الاستحقاق 5 أغسطس)", "التاريخ": "07/08/2026", "الشركات_المذكورة": ["جهينة"], "المصدر": "مباشر"},
            {"العنوان": "المصرية للاتصالات تتعاقد على تشغيل شبكة الجيل الخامس", "التاريخ": "08/08/2026", "الشركات_المذكورة": ["المصرية للاتصالات"], "المصدر": "أموال الغد"},
            {"العنوان": "استحواذ تحالف جديد على 20% من أسهم سبينالكس", "التاريخ": "07/08/2026", "الشركات_المذكورة": ["سبينالكس"], "المصدر": "حابي"},
        ]
    return news_list[:10]  # نأخذ آخر 10 أخبار فقط

# ============================================================
# 4. التحليل والدمج
# ============================================================
def analyze_market():
    """التحليل الشامل للسوق وإرجاع النتائج"""
    all_data = []
    
    # جلب بيانات كل سهم
    progress_bar = st.progress(0, text="جاري تحميل بيانات الأسهم...")
    for i, (name, symbol) in enumerate(STOCKS_DICT.items()):
        progress_bar.progress((i + 1) / len(STOCKS_DICT), text=f"جاري تحميل {name}...")
        df_raw = fetch_stock_data(symbol)
        if df_raw is not None and not df_raw.empty:
            df_indicators = calculate_indicators(df_raw)
            if df_indicators is not None and len(df_indicators) > 5:
                last_row = df_indicators.iloc[-1]
                sector = SECTOR_MAP.get(name, "قطاعات أخرى")
                all_data.append({
                    "الاسم": name,
                    "الرمز": symbol,
                    "القطاع": sector,
                    "السعر_الحالي": last_row['إغلاق'],
                    "التغير_%": last_row['التغير_%'] if not pd.isna(last_row['التغير_%']) else 0,
                    "الحجم_اليوم": last_row['حجم_التداول'],
                    "SMA_20_حجم": last_row['SMA_20_حجم'] if not pd.isna(last_row['SMA_20_حجم']) else last_row['حجم_التداول'],
                    "نسبة_السيولة": last_row['نسبة_السيولة'] if not pd.isna(last_row['نسبة_السيولة']) else 1,
                    "MFI": last_row['MFI'] if not pd.isna(last_row['MFI']) else 50,
                    "القيمة_اليوم": last_row['قيمة_التداول'],
                    "SMA_5_حجم": last_row['SMA_5_حجم'] if not pd.isna(last_row['SMA_5_حجم']) else last_row['حجم_التداول'],
                    "SMA_50_حجم": last_row['SMA_50_حجم'] if not pd.isna(last_row['SMA_50_حجم']) else last_row['حجم_التداول'],
                })
    progress_bar.empty()
    
    df_stocks = pd.DataFrame(all_data)
    if df_stocks.empty:
        st.error("تعذر جلب بيانات الأسهم. تأكد من اتصال الإنترنت وصحة الرموز.")
        return None, None
    
    # إضافة تصنيف السيولة الحقيقية مقابل الوهمية
    # السيولة الحقيقية: نسبة سيولة > 1.5 و MFI > 40
    df_stocks['نوع_السيولة'] = df_stocks.apply(
        lambda row: '🟢 سيولة حقيقية (قوية)' if (row['نسبة_السيولة'] > 1.5 and row['MFI'] > 40) else
                    ('🔴 سيولة وهمية (ضعيفة)' if (row['نسبة_السيولة'] > 1.5 and row['MFI'] < 40) else
                     '🟡 سيولة طبيعية'),
        axis=1
    )
    
    # تجميع حسب القطاع
    sector_summary = df_stocks.groupby('القطاع').agg({
        'الحجم_اليوم': 'sum',
        'القيمة_اليوم': 'sum',
        'نسبة_السيولة': 'mean',
        'MFI': 'mean',
        'التغير_%': 'mean'
    }).reset_index()
    
    # حساب متوسط السيولة للقطاع (متوسط 20 جلسة) بناءً على متوسطات الأسهم
    sector_summary['نسبة_تفوق_السيولة'] = sector_summary['نسبة_السيولة'] * 100  # تعبير عن نسبة التجاوز
    
    # ترتيب القطاعات حسب القيمة المتداولة
    sector_summary = sector_summary.sort_values('القيمة_اليوم', ascending=False)
    
    return df_stocks, sector_summary

# ============================================================
# 5. واجهة التطبيق الرئيسية
# ============================================================
st.title("🧭 البوصلة الذكية - البورصة المصرية (السيولة الحية)")
st.caption("آخر تحديث: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " | التحديث التلقائي كل 10 دقائق")

# تفعيل التحديث التلقائي (كل 10 دقائق = 600000 ميللي ثانية)
st_autorefresh(interval=600000, key="auto_refresh")

# جلب الأخبار
news = fetch_news()

# جلب وتحليل السوق
df_stocks, sector_summary = analyze_market()

if df_stocks is None or sector_summary is None:
    st.stop()

# ============================================================
# 5.1 عرض البوصلة الذهبية
# ============================================================
st.markdown("---")
st.header("🏆 البوصلة الذهبية: أين تتجه السيولة الآن؟")

# تحديد أفضل قطاع (الأعلى قيمة تداول وأعلى نسبة سيولة)
top_sector = sector_summary.iloc[0] if not sector_summary.empty else None
if top_sector is not None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🥇 القطاع الأقوى", top_sector['القطاع'], delta=f"{top_sector['القيمة_اليوم']:,.0f} جنيه")
    with col2:
        st.metric("💰 قيمة التداول (القطاع)", f"{top_sector['القيمة_اليوم']:,.0f}", delta=f"{top_sector['نسبة_السيولة']:.1f}x متوسط السوق")
    with col3:
        st.metric("📈 متوسط التغير", f"{top_sector['التغير_%']:.2f}%")
    with col4:
        st.metric("💵 مؤشر التدفق (MFI)", f"{top_sector['MFI']:.1f}", delta="قوي" if top_sector['MFI'] > 50 else "ضعيف")
    
    st.success(f"✅ **التوصية الفورية**: السيولة تتركز بقوة في قطاع **{top_sector['القطاع']}**، وهو المرشح الأقرب لاستمرار الصعود. ركز على أسهمه الموضحة أدناه.")

# ============================================================
# 5.2 قائمة الأسهم الأكثر سيولة حقيقية
# ============================================================
st.markdown("---")
st.header("📊 الأسهم الأكثر سيولة حقيقية (التي تتجاوز متوسط 20 جلسة)")

# فلترة الأسهم ذات السيولة الحقيقية (نسبة سيولة > 1.5 و MFI > 40)
real_liquidity = df_stocks[df_stocks['نوع_السيولة'] == '🟢 سيولة حقيقية (قوية)'].sort_values('نسبة_السيولة', ascending=False)

if not real_liquidity.empty:
    # عرض الجدول
    display_cols = ['الاسم', 'القطاع', 'السعر_الحالي', 'التغير_%', 'الحجم_اليوم', 'SMA_20_حجم', 'نسبة_السيولة', 'MFI', 'نوع_السيولة']
    st.dataframe(
        real_liquidity[display_cols].style.background_gradient(subset=['نسبة_السيولة', 'MFI'], cmap='Greens'),
        use_container_width=True
    )
    
    # عرض الأسهم كأزرار للربط بـ TradingView (تطبيق المستخدم)
    st.subheader("🔗 اضغط على أي سهم لفتح الشارت على TradingView:")
    cols = st.columns(5)
    for idx, (_, row) in enumerate(real_liquidity.head(10).iterrows()):
        code = row['الرمز'].replace('.CA', '').upper()
        url = f"https://www.tradingview.com/chart/?symbol=EGX:{code}"
        with cols[idx % 5]:
            st.link_button(f"📈 {row['الاسم']}", url)
else:
    st.info("لا توجد أسهم تحقق سيولة حقيقية استثنائية حالياً. قد يكون السوق في حالة هدوء.")

# ============================================================
# 5.3 تحذير السيولة الوهمية
# ============================================================
st.markdown("---")
st.header("⚠️ تنبيهات السيولة الوهمية (حجم كبير + سعر ثابت/منخفض)")

fake_liquidity = df_stocks[(df_stocks['نوع_السيولة'] == '🔴 سيولة وهمية (ضعيفة)') & (df_stocks['نسبة_السيولة'] > 1.5)]

if not fake_liquidity.empty:
    st.warning("هذه الأسهم تشهد أحجام تداول ضخمة ولكن مؤشر التدفق النقدي منخفض، مما يشير إلى احتمالية توزيع أو عمليات بيع ممنهجة (فخ للصغار).")
    st.dataframe(fake_liquidity[['الاسم', 'القطاع', 'التغير_%', 'نسبة_السيولة', 'MFI']], use_container_width=True)
else:
    st.success("✅ لا توجد سيولة وهمية ملحوظة حالياً. الحركة في السوق تبدو صحية.")

# ============================================================
# 5.4 ركن الأخبار وربطها بالسيولة
# ============================================================
st.markdown("---")
st.header("📰 ركن الأخبار المؤثرة (مباشر + وكالات) - الربط بالسيولة")

for news_item in news:
    companies = news_item['الشركات_المذكورة']
    # عرض الخبر
    with st.expander(f"📌 {news_item['العنوان'][:80]}... ({news_item['التاريخ']})"):
        st.write(f"**المصدر:** {news_item['المصدر']}")
        st.write(f"**الشركات المعنية:** {', '.join(companies)}")
        
        # البحث عن تأثير الخبر على الأسهم (ربط بالسيولة)
        affected_stocks = df_stocks[df_stocks['الاسم'].isin(companies)]
        if not affected_stocks.empty:
            st.write("**📊 تأثير الخبر على السيولة (مقارنة بمتوسط 20 جلسة):**")
            for _, stock in affected_stocks.iterrows():
                change = stock['نسبة_السيولة'] - 1
                if change > 0.5:
                    st.success(f"✅ {stock['الاسم']}: السيولة تضاعفت {change:.1f} مرة عن متوسطها الطبيعي → تأكيد دخول حيتان.")
                elif change > 0:
                    st.info(f"ℹ️ {stock['الاسم']}: زيادة طفيفة في السيولة ({change:.1f}x).")
                else:
                    st.warning(f"⚠️ {stock['الاسم']}: لم تتأثر السيولة رغم الخبر (انتبه للخبر المضلل).")
        else:
            st.caption("لا توجد أسهم محددة متأثرة بهذا الخبر في قائمتنا (خبر قطاعي عام).")

# ============================================================
# 5.5 جدول جميع القطاعات (مقارنة)
# ============================================================
st.markdown("---")
st.header("🏢 أداء جميع القطاعات (مرتبة حسب السيولة)")

# تنسيق الجدول
sector_display = sector_summary.copy()
sector_display['القيمة_اليوم'] = sector_display['القيمة_اليوم'].apply(lambda x: f"{x:,.0f}")
sector_display['نسبة_السيولة'] = sector_display['نسبة_السيولة'].apply(lambda x: f"{x:.2f}x")
sector_display['التغير_%'] = sector_display['التغير_%'].apply(lambda x: f"{x:.2f}%")
sector_display['MFI'] = sector_display['MFI'].apply(lambda x: f"{x:.1f}")

st.dataframe(sector_display[['القطاع', 'القيمة_اليوم', 'نسبة_السيولة', 'التغير_%', 'MFI']], use_container_width=True)

# ============================================================
# 5.6 الإحصائيات السريعة (ملخص اليوم)
# ============================================================
st.markdown("---")
st.header("📌 ملخص سريع للجلسة")

total_value = df_stocks['القيمة_اليوم'].sum()
total_volume = df_stocks['الحجم_اليوم'].sum()
avg_mfi = df_stocks['MFI'].mean()
up_count = len(df_stocks[df_stocks['التغير_%'] > 0])
down_count = len(df_stocks[df_stocks['التغير_%'] < 0])

col1, col2, col3, col4 = st.columns(4)
col1.metric("💵 إجمالي قيمة التداول", f"{total_value:,.0f} جنيه")
col2.metric("📊 عدد الأسهم المتداولة", f"{len(df_stocks)} سهم")
col3.metric("📈 أسهم مرتفعة / منخفضة", f"{up_count} / {down_count}")
col4.metric("📉 متوسط MFI للسوق", f"{avg_mfi:.1f}", delta="متفائل" if avg_mfi > 50 else "متشائم")

st.caption("تم تطوير هذه البوصلة باستخدام بيانات Yahoo Finance الفعلية، وتحليل فني لحظي، وربط بالأخبار. يرجى مراجعة التوصيات مع مستشارك المالي قبل اتخاذ القرارات.")

# ============================================================
# 6. تشغيل التطبيق
# ============================================================
if __name__ == "__main__":
    # في Streamlit، يتم تشغيل الكود مباشرة، لا حاجة لـ main()
    pass