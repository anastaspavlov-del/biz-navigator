import streamlit as st
import math
from openai import OpenAI
import stripe
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

# Histats безплатен невидим брояч
st.markdown(
    '<a href="https://www.histats.com" target="_blank">'
    '<img src="https://sstatic1.histats.com/0.gif?5036919&101" alt="Histats" border="0" style="display:none;">'
    '</a>', 
    unsafe_allow_html=True
)

# API Keys Check от Secrets
api_key = st.secrets.get("OPENAI_API_KEY", "")
stripe.api_key = st.secrets.get("STRIPE_API_KEY", "")

# 📥 УЛАВЯНЕ НА ДИНАМИЧНИТЕ ДАННИ ОТ URL
session_id = st.query_params.get("session_id")
url_fixed_costs = st.query_params.get("fc")
url_price = st.query_params.get("pr")
url_cost = st.query_params.get("cs")
url_idea = st.query_params.get("idea", "")

# Помощна функция за безопасно конвертиране към число
def safe_int(value, default_val):
    if not value:
        return default_val
    try:
        # Изчистване на разстояния и символи за валута, ако има такива
        clean_val = str(value).strip().replace("€", "").replace("$", "")
        # Ако Stripe е върнал самия макрос като текст {URL_PARAM:...}, връщаме дефолт
        if "{" in clean_val or "URL_PARAM" in clean_val:
            return default_val
        return int(float(clean_val))
    except (ValueError, TypeError):
        return default_val

# Парсване на първоначалните стойности
init_fixed_costs = safe_int(url_fixed_costs, 1200)
init_price = safe_int(url_price, 50)
init_cost = safe_int(url_cost, 20)
init_idea = urllib.parse.unquote(url_idea) if url_idea and "{" not in url_idea else ""

# Инициализация на Session State (Пази въведеното от потребителя)
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = init_fixed_costs
if "price" not in st.session_state: st.session_state.price = init_price
if "cost" not in st.session_state: st.session_state.cost = init_cost
if "idea_text" not in st.session_state: st.session_state.idea_text = init_idea

# АКО ИМАМЕ ВЪРНАТИ ВАЛИДНИ ПАРАМЕТРИ ОТ URL, ОБНОВЯВАМЕ СЕСИЯТА ВЕДНАГА
if url_fixed_costs and "{" not in url_fixed_costs:
    st.session_state.fixed_costs = init_fixed_costs
    st.session_state.price = init_price
    st.session_state.cost = init_cost
    if init_idea:
        st.session_state.idea_text = init_idea

# Функция за сигурна проверка на плащането в Stripe
def verify_stripe_payment(sid):
    if not sid:
        return False
    try:
        session = stripe.checkout.Session.retrieve(sid)
        if session.payment_status == "paid":
            return True
    except Exception as e:
        st.error(f"Грешка при проверка на плащането в Stripe: {e}")
    return False

# Изпълнение на проверката при наличие на session_id
is_payment_valid = False
if session_id:
    with st.spinner("🔒 Проверка на статуса на плащането..."):
        is_payment_valid = verify_stripe_payment(session_id)

# Функция за генериране на Word (.docx) документ
def create_docx(business_idea, financials, report_text):
    doc = Document()
    doc.add_heading("БИЗНЕС НАВИГАТОР - ЕКСПЕРТЕН ДОКЛАД", level=0)
    doc.add_heading("Обща информация", level=1)
    doc.add_paragraph(f"Бизнес идея: {business_idea}")
    doc.add_paragraph(f"Финансови параметри:\n"
                      f"- Постоянни месечни разходи: {financials['fc']} евро\n"
                      f"- Продажна цена: {financials['pr']} евро\n"
                      f"- Себестойност: {financials['cs']} евро\n"
                      f"- Нужни продажби за нулата: {financials['be']} бр./месец")
    
    doc.add_paragraph("\n" + "="*40 + "\n")
    doc.add_heading("Подробен анализ и план за действие", level=1)
    
    for paragraph in report_text.split("\n"):
        if paragraph.strip():
            if paragraph.strip().startswith("###"):
                clean_title = paragraph.replace("###", "").strip()
                doc.add_heading(clean_title, level=2)
            else:
                doc.add_paragraph(paragraph.strip())
                
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

# UI Header
st.title("🚀 Бизнес Навигатор")
st.caption("Твоят дигитален стартъп ментор")

# 🔥 ГЕНЕРИРАНЕ НА ПЕРСОНАЛИЗИРАНИЯ ДОКЛАД СЛЕД ПЛАЩАНЕ
if is_payment_valid:
    st.balloons()
    st.success("🎉 Плащането е потвърдено успешно! Твоят персонализиран бизнес план се генерира...")
    
    current_idea = st.session_state.idea_text
    if not current_idea or len(current_idea) < 5:
        current_idea = "Бизнес модел на база финансови калкулации."

    if not api_key:
        st.error("🔑 Липсва OpenAI API ключ в настройките. Добавете го в Secrets.")
    else:
        with st.spinner("🤖 Експертният AI консултант анализира ТВОЯТА идея..."):
            try:
                client = OpenAI(api_key=api_key)
                margin = st.session_state.price - st.session_state.cost
                be_units = math.ceil(st.session_state.fixed_costs / margin) if margin > 0 else 0
                min_turnover = be_units * st.session_state.price
                
                paid_prompt = f"""
                Ти си топ бизнес консултант за стартиращи компании в България.
                Напиши изключително подробен, строго персонализиран бизнес анализ на български език.
                
                КОНКРЕТНА ИДЕЯ НА ПОТРЕБИТЕЛЯ: "{current_idea}"
                
                ВЪВЕДЕНИ ФИНАНСИ ОТ ПОТРЕБИТЕЛЯ:
                - Постоянни месечни разходи: {st.session_state.fixed_costs} евро
                - Продажна цена на бройка/час: {st.session_state.price} евро
                - Себестойност на бройка/минимален разход: {st.session_state.cost} euro
                - Точка на баланса (Break-even): Нужни са точно {be_units} продажби на месец за оборот от {min_turnover} евро.
                
                Докладът ТРЯБВА да е дълъг и да съдържа следните 3 големи раздела с тези точни заглавия:
                
                ### 📊 ЧАСТ 1: ПЕРСОНАЛИЗИРАН АНАЛИЗ
                - СИЛНИ СТРАНИ: Кои са 3-те най-големи стратегически предимства на този конкретен модел?
                - СКРИТИ РИСКОВЕ: Кои са 3-те най-големи опасности специално за този бизнес на българския пазар (данъци, скрита конкуренция, регулации) и как ТОЧНО да бъдат избегнати?
                
                ### 🗺️ ЧАСТ 2: ПЪТНА КАРТА ПО СТЪПКИ (ROADMAP)
                - Дай ясна хронологична пътна карта (Седмица 1: Проучване; Седмица 2: MVP Тестване; Месец 1: Първи клиенти), съобразена с тази бизнес идея.
                
                ### 📝 ЧАСТ 3: AI ЧЕК-ЛИСТ СЪС ЗАДАЧИ
                - Генерирай списък от точно 5 конкретни, практически задачи, специфични за неговия бизнес, които потребителят може да изпълни веднага.
                
                Бъди максимално конкретен, цитирай цифрите му и избягвай общи приказки.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": paid_prompt}],
                    temperature=0.7
                )
                
                full_report = response.choices[0].message.content
                
                st.markdown("## 📊 ТВОЯТ ПЕРСОНАЛИЗИРАН ЕКСПЕРТЕН БИЗНЕС ПЛАН")
                st.markdown(full_report)
                st.markdown("---")
                
                # Подготовка на данните за Word документ
                fin_data = {
                    "fc": st.session_state.fixed_costs,
                    "pr": st.session_state.price,
                    "cs": st.session_state.cost,
                    "be": be_units
                }
                
                docx_bytes = create_docx(current_idea, fin_data, full_report)
                
                st.download_button(
                    label="📥 Изтегли Бизнес плана в редактируем Word (.docx) формат",
                    data=docx_bytes,
                    file_name="Business_Plan_Report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Грешка при генериране на доклада: {e}")
elif session_id and not is_payment_valid:
    st.error("🛑 Предоставеният идентификатор на плащане е невалиден или не е преминал успешно.")

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
        
        st.markdown("#### **Резултат за твоя business:**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Нужни продажби", value=f"{be_units} бр./мес.")
        with col2:
            st.metric(label="Минимум оборот", value=f"{min_turnover} евро")

# TAB 2: AI Validation
with tab2:
    st.subheader("🤖 Запиши идеята си")
    
    text_idea = st.text_area(
        "Напиши или коригирай идеята си тук:", 
        value=st.session_state.idea_text,
        placeholder="Пример: Искам да отворя автомивка в Люлин..."
    )
    st.session_state.idea_text = text_idea
    
    if st.button("🚀 Анализирай моята идея", use_container_width=True):
        if not api_key:
            st.error("🔑 Липсва OpenAI API ключ в настройките.")
        elif len(text_idea) < 5:
            st.warning("⚠️ Моля, въведете описание на бизнес идеята си.")
        else:
            with st.spinner("AI Менторът изчислява финансовия риск..."):
                try:
                    client = OpenAI(api_key=api_key)
                    free_prompt = f"""
                    Ти си бизнес консултант. Направи КРАТЪК предварителен преглед (до 3 изречения) на тази бизнес идея: '{text_idea}'.
                    Дай само бърза оценка дали изглежда лесно или трудно. Бъди позитивен, но реалист.
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
                    
                    encoded_idea = urllib.parse.quote(text_idea)
                    
                    # Използваме базовия сигурен Stripe линк
                    stripe_link = "https://buy.stripe.com/test_6oU4gBdtE0D17sV8q4cjS00"
                    
                    # Динамичен адрес, предаващ параметрите напред към Stripe
                    dynamic_url = f"{stripe_link}?fc={st.session_state.fixed_costs}" \
                                  f"&pr={st.session_state.price}" \
                                  f"&cs={st.session_state.cost}" \
                                  f"&idea={encoded_idea}"
                    
                    st.write("Нашият AI ще състави подробна пътна карта и чек-лист специално за тези стойности.")
                    st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 евро", dynamic_url, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Грешка: {e}")
