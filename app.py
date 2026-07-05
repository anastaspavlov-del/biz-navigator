import streamlit as st
import math
from openai import OpenAI
import urllib.parse
from docx import Document
from io import BytesIO

# 1. Page Configuration
st.set_page_config(
    page_title="Бизнес Навигатор", 
    page_icon="🚀", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# 🎨 СТИЛИЗИРАНЕ (CSS) ПО ДИЗАЙНА ОТ design_biz_nav.jpg
st.html("""
<style>
    /* Главен фон на приложението - Тъмно червен градиент */
    .stApp {
        background: linear-gradient(135deg, #1a0003 0%, #0d0001 100%) !important;
        color: #f5f5f5 !important;
    }
    
    /* Стилизиране на табовете, за да приличат на бутони */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a0826 !important; /* Лилаво/тъмен фон за таб */
        border-radius: 12px !important;
        padding: 10px 20px !important;
        color: #a3a3a3 !important;
        border: none !important;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab"]:nth-child(3) {
        background-color: #0b5327 !important; /* Зелен таб като на картинката */
        color: white !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        border: 2px solid #00cc44 !important;
        color: white !important;
    }

    /* Заоблени тъмни карти за контейнерите */
    div[data-testid="stVerticalBlock"] > div {
        background-color: rgba(30, 5, 8, 0.6);
        border-radius: 16px;
        padding: 5px;
    }

    /* Слайдери - зелени акценти */
    .stSlider [data-testid="stMarker"] {
        color: #00cc44 !important;
    }
    div[data-baseweb="slider"] > div {
        background: #00cc44 !important;
    }
    
    /* Зелени кутийки със стойности (показващи евро) */
    .value-box {
        background-color: #0d0203;
        border: 2px solid #00cc44;
        color: #00cc44;
        font-weight: bold;
        padding: 6px 12px;
        border-radius: 8px;
        text-align: center;
        font-size: 1.1rem;
        float: right;
    }
    
    /* Резултатни карти (Долния блок) */
    .result-container {
        background-color: #1a0204;
        border: 1px solid #3d080e;
        border-radius: 16px;
        padding: 20px;
        margin-top: 20px;
    }
    .result-card {
        background-color: #260307;
        border: 1px solid #4a0d14;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }
    .result-val-green {
        color: #00cc44;
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* Светеща лампа съвет */
    .tip-box {
        background-color: #151a05;
        border: 1px solid #526610;
        border-radius: 12px;
        padding: 15px;
        color: #a6cc33;
        margin-top: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Основният голям зелен бутон най-отдолу */
    .stButton > button {
        background: #11a638 !important;
        color: white !important;
        border-radius: 14px !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 1.2rem !important;
        padding: 14px !important;
        box-shadow: 0px 4px 15px rgba(17, 166, 56, 0.4);
        transition: 0.3s;
    }
    .stButton > button:hover {
        background: #15c743 !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Histats безплатен невидим брояч
st.markdown(
    '<a href="https://www.histats.com" target="_blank">'
    '<img src="https://sstatic1.histats.com/0.gif?5036919&101" alt="Histats" border="0" style="display:none;">'
    '</a>', 
    unsafe_allow_html=True
)

# API Key Check
api_key = st.secrets.get("OPENAI_API_KEY", "")

# УЛАВЯНЕ НА ДИНАМИЧНИТЕ ДАННИ ОТ URL
is_paid = st.query_params.get("paid") == "true"
url_fixed_costs = st.query_params.get("fc")
url_price = st.query_params.get("pr")
url_cost = st.query_params.get("cs")
url_idea = st.query_params.get("idea", "")

# Стойности по подразбиране, точно като в референцията от снимката
init_fixed_costs = int(url_fixed_costs) if url_fixed_costs else 2000
init_price = int(url_price) if url_price else 50
init_cost = int(url_cost) if url_cost else 15
init_idea = urllib.parse.unquote(url_idea) if url_idea else ""

# Session State
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = init_fixed_costs
if "price" not in st.session_state: st.session_state.price = init_price
if "cost" not in st.session_state: st.session_state.cost = init_cost
if "idea_text" not in st.session_state: st.session_state.idea_text = init_idea

def create_docx(business_idea, financials, report_text):
    doc = Document()
    doc.add_heading("БИЗНЕС НАВИГАТОР - ЕКСПЕРТЕН ДОКЛАД", level=0)
    doc.add_heading("Обща информация", level=1)
    doc.add_paragraph(f"Бизнес идея: {business_idea}")
    doc.add_paragraph(f"Финансови параметри:\n- Постоянни разходи: {financials['fc']}€\n- Цена: {financials['pr']}€\n- Себестойност: {financials['cs']}€\n- Баланс: {financials['be']} бр.")
    doc.add_heading("Подробен анализ", level=1)
    for paragraph in report_text.split("\n"):
        if paragraph.strip():
            if paragraph.strip().startswith("###"):
                doc.add_heading(paragraph.replace("###", "").strip(), level=2)
            else:
                doc.add_paragraph(paragraph.strip())
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

# UI Шапка с икона ракета (същата като в горния ляв ъгъл на телефона)
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("<h1 style='margin:0; padding:0;'>🚀</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h2 style='margin:0; padding:0; color:white;'>Бизнес Навигатор</h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; color:#b3b3b3; font-size:0.9rem;'>Твоят дигитален стартъп ментор</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# СЕКЦИЯ ПЛАТЕН ДОКЛАД (Изскача най-отгоре при успешно плащане)
if is_paid:
    st.balloons()
    st.success("🎉 Плащането е успешно! Твоят персонализиран бизнес план се генерира...")
    current_idea = init_idea if init_idea else st.session_state.idea_text
    if not current_idea: current_idea = "Бизнес модел на база финансови калкулации."

    if not api_key:
        st.error("🔑 Липсва OpenAI API ключ в настройките.")
    else:
        with st.spinner("🤖 Експертният AI консултант анализира Вашата идея..."):
            try:
                client = OpenAI(api_key=api_key)
                margin = st.session_state.price - st.session_state.cost
                be_units = math.ceil(st.session_state.fixed_costs / margin) if margin > 0 else 0
                min_turnover = be_units * st.session_state.price
                
                paid_prompt = f"Напиши детайлен бизнес анализ на български за идеята '{current_idea}'. Месечни разходи: {st.session_state.fixed_costs} евро, Цена: {st.session_state.price} евро, Себестойност: {st.session_state.cost} евро. Нужни продажби: {be_units}."
                response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": paid_prompt}], temperature=0.7)
                full_report = response.choices[0].message.content
                
                st.markdown("## 📊 ТВОЯТ ПЕРСОНАЛИЗИРАН ЕКСПЕРТЕН БИЗНЕС ПЛАН")
                st.markdown(full_report)
                
                fin_data = {"fc": st.session_state.fixed_costs, "pr": st.session_state.price, "cs": st.session_state.cost, "be": be_units}
                docx_bytes = create_docx(current_idea, fin_data, full_report)
                st.download_button(label="📥 Изтегли Бизнес плана в Word (.docx)", data=docx_bytes, file_name="Business_Plan_Report.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            except Exception as e:
                st.error(f"Грешка: {e}")

# СЪЗДАВАНЕ НА ТАБОВЕТЕ О Т СНИМКАТА design_biz_nav.jpg
tab1, tab2, tab3 = st.tabs(["📊 1. Сметни риск", "💡 2. AI Валидация", "📱 Финансов симулатор"])

with tab3:
    st.markdown("### 📱 Финансов симулатор")
    st.markdown("<p style='color:#b3b3b3;'>Нагласи слайдерите с пръст, за да видиш минимума за оцеляване:</p>", unsafe_allow_html=True)
    
    # Слайдер 1
    col_lbl1, col_val1 = st.columns([3, 1])
    with col_lbl1: st.write("💼 Месечни постоянни разходи\n(наем, осигуровки)")
    with col_val2: st.markdown(f"<div class='value-box'>{st.session_state.fixed_costs} €</div>", unsafe_allow_html=True)
    st.session_state.fixed_costs = st.slider("fc_slider", 200, 10000, st.session_state.fixed_costs, 100, label_visibility="collapsed")
    
    # Слайдер 2
    col_lbl2, col_val2 = st.columns([3, 1])
    with col_lbl2: st.write("💰 Продажна цена за 1 бройка / час")
    with col_val2: st.markdown(f"<div class='value-box'>{st.session_state.price} €</div>", unsafe_allow_html=True)
    st.session_state.price = st.slider("pr_slider", 5, 500, st.session_state.price, 1, label_visibility="collapsed")
    
    # Слайдер 3
    col_lbl3, col_val3 = st.columns([3, 1])
    with col_lbl3: st.write("📦 Себестойност на 1 бройка\n(материали/доставка)")
    with col_val3: st.markdown(f"<div class='value-box'>{st.session_state.cost} €</div>", unsafe_allow_html=True)
    st.session_state.cost = st.slider("cs_slider", 0, 300, st.session_state.cost, 1, label_visibility="collapsed")

    # ИЗЧИСЛЕНИЯ И ИЗВЕЖДАНЕ НА РЕЗУЛТАТИТЕ
    margin = st.session_state.price - st.session_state.cost
    if margin <= 0:
        st.error("🛑 Цената трябва да е по-висока от себестойността!")
    else:
        be_units = math.ceil(st.session_state.fixed_costs / margin)
        min_turnover = be_units * st.session_state.price
        daily_sales = be_units / 30
        
        # Резултатен блок от долната част на екрана в design_biz_nav.jpg
        st.markdown(f"""
        <div class='result-container'>
            <p style='font-weight:bold; font-size:1.1rem; margin-bottom:15px;'>Резултат за твоя бизнес:</p>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
                <div class='result-card'>
                    <p style='color:#b3b3b3; font-size:0.85rem; margin:0;'>Нужни продажби</p>
                    <p class='result-val-green' style='color:#11a638;'>{be_units}</p>
                    <p style='color:#b3b3b3; font-size:0.85rem; margin:0;'>бр./мес.</p>
                </div>
                <div class='result-card'>
                    <p style='color:#b3b3b3; font-size:0.85rem; margin:0;'>Минимум оборот</p>
                    <p class='result-val-green'>{min_turnover} €</p>
                </div>
            </div>
            <div class='tip-box'>
                <span>💡</span>
                <span>Това означава средно по <b>{daily_sales:.1f} продажби на ден</b>, за да излезеш на нула.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("🤖 Запиши идеята си")
    text_idea = st.text_area("Напиши концепцията си тук:", value=st.session_state.idea_text, placeholder="Пример: Онлайн магазин за...")
    st.session_state.idea_text = text_idea

st.markdown("<br>", unsafe_allow_html=True)

# Големият долен зелен бутон "Анализирай моята идея"
if st.button("🧠 Анализирай моята идея", use_container_width=True):
    if len(st.session_state.idea_text) < 5:
        st.warning("⚠️ Моля, въведете първо описание на вашата бизнес идея в Таб '2. AI Валидация'.")
    else:
        encoded_idea = urllib.parse.quote(st.session_state.idea_text)
        dynamic_url = f"https://biz-navigator.streamlit.app/?paid=true&fc={st.session_state.fixed_costs}&pr={st.session_state.price}&cs={st.session_state.cost}&idea={encoded_idea}"
        st.markdown(f"<a href='{dynamic_url}' target='_self'><button style='width:100%; background-color:#11a638; color:white; border:none; padding:15px; border-radius:14px; font-weight:bold; font-size:1.2rem; cursor:pointer;'>💳 Отключи Пълния Бизнес Доклад</button></a>", unsafe_allow_html=True)
