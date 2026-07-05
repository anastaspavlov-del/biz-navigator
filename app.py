import streamlit as st
import math
from openai import OpenAI
from fpdf import FPDF  # Библиотека за генериране на PDF

# 1. Page Configuration
st.set_page_config(
    page_title="Бизнес Навигатор", 
    page_icon="🚀", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Histats безплатен невидим брояч за трафик и градове
st.markdown(
    '<a href="https://www.histats.com" target="_blank">'
    '<img src="https://sstatic1.histats.com/0.gif?5036919&101" alt="Histats" border="0" style="display:none;">'
    '</a>', 
    unsafe_allow_html=True
)

# API Key Check
api_key = st.secrets.get("OPENAI_API_KEY", "")

# УЛАВЯНЕ НА СИГНАЛА ЗА ПЛАЩАНЕ ОТ STRIPE
is_paid = st.query_params.get("paid") == "true"

# Session State Initialization
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = 1200
if "price" not in st.session_state: st.session_state.price = 50
if "cost" not in st.session_state: st.session_state.cost = 20

# UI Header
st.title("🚀 Бизнес Навигатор")
st.caption("Твоят дигитален стартъп ментор")

# Функция за генериране на PDF документ
def create_pdf(business_idea, analysis_text):
    pdf = FPDF()
    pdf.add_page()
    # Използваме стандартен системен шрифт, поддържащ латиница. 
    # За пълна кирилица в PDF в бъдеще се вгражда допълнителен .ttf шрифт, 
    # но за тестови цели тук използваме стандартна структура.
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(40, 10, "BUSINESS NAVIGATOR REPORT", ln=1)
    pdf.ln(10)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, f"Business Concept: {business_idea}\n\n{analysis_text}")
    return pdf.output(dest='S')

# СЕКЦИЯ СЛЕД УСПЕШНО ПЛАЩАНЕ
if is_paid:
    st.balloons()
    st.success("🎉 Плащането е успешно! Твоят разширен експертен доклад се генерира...")
    
    if not api_key:
        st.error("🔑 Липсва OpenAI API ключ в настройките. Добавете го в Secrets.")
    else:
        with st.spinner("🤖 Експертният AI консултант съставя детайлния бизнес план, пътна карта и чек-лист..."):
            try:
                client = OpenAI(api_key=api_key)
                margin = st.session_state.price - st.session_state.cost
                be_units = math.ceil(st.session_state.fixed_costs / margin) if margin > 0 else 0
                min_turnover = be_units * st.session_state.price
                
                paid_prompt = f"""
                Ти си топ бизнес консултант за стартиращи компании в България.
                Напиши изключително подробен, персонализиран бизнес анализ на български език.
                
                Данни за бизнеса:
                - Финанси: Постоянни месечни разходи: {st.session_state.fixed_costs} евро, Цена на бройка/час: {st.session_state.price} евро, Себестойност: {st.session_state.cost} евро.
                - Финансова цел: Нужни продажби за точка на баланса: {be_units} бр. за минимален оборот от {min_turnover} евро.
                
                Докладът ТРЯБВА да съдържа следните 4 големи раздела, форматирани с ясни заглавия (Markdown):
                
                ### 📊 ЧАСТ 1: ПЕРСОНАЛИЗИРАН АНАЛИЗ
                - СИЛНИ СТРАНИ: Кои са 3-те най-големи предимства на този модел?
                - СКРИТИ РИСКОВЕ: Кои са 3-те най-големи опасности на българския пазар (данъци, конкуренция, регулации) и как точно да бъдат избегнати?
                
                ### 🗺️ ЧАСТ 2: ПЪТНА КАРТА ПО СТЪПКИ (ROADMAP)
                - Стъпка 1 (Седмица 1): Подготовка и проучване.
                - Стъпка 2 (Седмица 2): Тестване на пазара (MVP).
                - Стъпка 3 (Месец 1): Първи продажби и легализация.
                
                ### 📝 ЧАСТ 3: AI ЧЕК-ЛИСТ СЪС ЗАДАЧИ
                - Дай списък от точно 5 конкретни, практически задачи (например: "Направи анкета в 3 фейсбук групи за...", "Изчисли разхода за..."), специфични за неговия бизнес, които потребителят може да отметне.
                
                Бъди максимално конкретен и прагматичен. Избягвай общи фрази.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": paid_prompt}],
                    temperature=0.7
                )
                
                full_report = response.choices[0].message.content
                
                # Показване на резултатите на екрана по красив начин
                st.markdown("## 📊 ТВОЯТ ПЪЛЕН ЕКСПЕРТЕН БИЗНЕС ПЛАН")
                st.markdown(full_report)
                st.markdown("---")
                
                # СЪЗДАВАНЕ НА БУТОН ЗА СВАЛЯНЕ НА PDF ТУК
                try:
                    pdf_bytes = create_pdf("Бизнес Идея", full_report)
                    st.download_button(
                        label="📥 Свали Пълния Анализ и Чек-лист в PDF формат",
                        data=pdf_bytes,
                        file_name="Business_Plan_Navigator.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as pdf_error:
                    st.warning(f"Докладът е готов на екрана! (Опцията за изтегляне като PDF се конфигурира допълнително: {pdf_error})")
                
            except Exception as e:
                st.error(f"Грешка при генериране на доклада: {e}")
    st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📊 1. Сметни риск", "💡 2. AI Валидация"])

# TAB 1: Financial Simulator
with tab1:
    st.subheader("📱 Финансов симулатор")
    st.write("Нагласи слайдерите с пръст, за да видиш минимума за оцеляване:")
    
    st.session_state.fixed_costs = st.slider(
        "💼 Месечни постоянни разходи (наем, осигуровки)", 
        min_value=200, max_value=10000, value=st.session_state.fixed_costs, step=100
    )
    
    st.session_state.price = st.slider(
        "💰 Продажна цена за 1 бройка / час", 
        min_value=0, max_value=500, value=st.session_state.price, step=1
    )
    
    st.session_state.cost = st.slider(
        "📦 Себестойност на 1 бройка (материали/доставка)", 
        min_value=0, max_value=300, value=st.session_state.cost, step=1
    )
    
    st.markdown("---")
    
    if st.session_state.price <= st.session_state.cost:
        st.error("🛑 Цената трябва да е по-висока от себестойността!")
    else:
        margin = st.session_state.price - st.session_state.cost
        be_units = math.ceil(st.session_state.fixed_costs / margin)
        min_turnover = be_units * st.session_state.price
        
        st.markdown("#### **Резултат за твоя бизнес:**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Нужни продажби", value=f"{be_units} бр./мес.")
        with col2:
            st.metric(label="Минимум оборот", value=f"{min_turnover} евро")
            
        st.info(f"💡 Това означава средно по **{be_units/30:.1f} продажби на ден**, за да излезеш на нула.")

# TAB 2: AI Validation
with tab2:
    st.subheader("🤖 Запиши идеята си")
    st.write("🎙️ **Запиши гласово описание на бизнеса си или го напиши от клавиатурата:**")
    
    audio_file = st.audio_input("Запиши гласово описание")
    text_idea = st.text_area("Или напиши идеята тук:", placeholder="Пример: Искам да отворя автомивка в Люлин...")
    
    if st.button("🚀 Анализирай моята идея", use_container_width=True):
        if not api_key:
            st.error("🔑 Липсва OpenAI API ключ в настройките. Моля, добави го в Secrets.")
        else:
            final_concept = ""
            if audio_file is not None:
                with st.spinner("Преобразуване на гласа в текст..."):
                    try:
                        client = OpenAI(api_key=api_key)
                        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                        final_concept = transcript.text
                        st.success(f"🎙️ Разпознат текст: '{final_concept}'")
                    except Exception as e:
                        st.error(f"Грешка при аудиото: {e}")
            else:
                final_concept = text_idea
            
            if len(final_concept) > 5:
                with st.spinner("AI Менторът изчислява финансовия риск..."):
                    try:
                        client = OpenAI(api_key=api_key)
                        margin = st.session_state.price - st.session_state.cost
                        be_units = math.ceil(st.session_state.fixed_costs / margin) if margin > 0 else 0
                        
                        free_prompt = f"""
                        Ти си бизнес консултант. Направи КРАТЪК предварителен преглед (до 3 изречения) на тази бизнес идея: '{final_concept}'.
                        Финанси: Месечен разход {st.session_state.fixed_costs} евро Нужни продажби: {be_units} бр.
                        Дай само бърза оценка дали финансовата цел изглежда лесна или трудна за българския пазар. Бъди позитивен, но реалист.
                        """
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": free_prompt}],
                            temperature=0.7
                        )
                        
                        st.markdown("---")
                        st.markdown("### 🔓 Твоят безплатен предварителен анализ:")
                        st.info(response.choices[0].message.content)
                        
                        st.markdown("### 📊 Отключи Пълния Експертен Доклад")
                        st.write("Нашият AI е подготвил подробен дигитален бизнес план специално за твоята ниша, който съдържа:")
                        st.markdown("""
                        * ⚠️ **3-те най-големи скрити риска** за този бизнес в България.
                        * 💸 **Списък с пропуснати разходи** (разрешителни, патенти, софтуер).
                        * 🎯 **MVP План стъпка по стъпка:** Как да тестваш пазара безплатно още тази седмица.
                        * 📈 **Маркетингова стратегия:** Откъде да намериш първите си 10 клиенти.
                        """)
                        
                        stripe_link = "https://buy.stripe.com/6oU4gBdtE0D17sV8q4cjS00" 
                        st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 евро", stripe_link, use_container_width=True)
                        
                        st.caption("🔒 Сигурно плащане. Ще получиш доклада си веднага след трансакцията.")
                        
                    except Exception as e:
                        st.error(f"Грешка при връзката с AI: {e}")
            else:
                st.warning("⚠️ Моля, въведете текст или направете запис.")
