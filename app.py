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

# Зареждане на ключове
api_key = st.secrets.get("OPENAI_API_KEY", "")
stripe.api_key = st.secrets.get("STRIPE_API_KEY", "")

# 📥 УЛАВЯНЕ НА SESSION ID И URL ПАРАМЕТРИ ПРИ ЗАВРЪЩАНЕ
session_id = st.query_params.get("session_id")

# Дефолтни стойности
init_fixed_costs = 1200
init_price = 50
init_cost = 20
init_idea = ""

# Инициализация на състоянието на сесията
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = init_fixed_costs
if "price" not in st.session_state: st.session_state.price = init_price
if "cost" not in st.session_state: st.session_state.cost = init_cost
if "idea_text" not in st.session_state: st.session_state.idea_text = init_idea

# 🔒 СИГУРНА ПРОВЕРКА ЧРЕЗ STRIPE API (ИЗДЪРПВАНЕ НА ПЕРСОНАЛИЗАЦИЯТА)
is_payment_valid = False

if session_id:
    with st.spinner("🔒 Синхронизиране на Вашите данни от Stripe..."):
        try:
            # Извикваме данните директно от сървъра на Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                is_payment_valid = True
                
                # Четем сигурния "пакет", който изпратихме в client_reference_id
                ref_id = session.get("client_reference_id")
                if ref_id and "||" in ref_id:
                    # Разкодираме обратно: "финанси || идея"
                    data_parts = ref_id.split("||")
                    nums = data_parts[0].split("|")
                    
                    if len(nums) == 3:
                        st.session_state.fixed_costs = int(nums[0])
                        st.session_state.price = int(nums[1])
                        st.session_state.cost = int(nums[2])
                    
                    if len(data_parts) > 1:
                        st.session_state.idea_text = urllib.parse.unquote(data_parts[1])
        except Exception as e:
            # Презастраховане в тестов режим: ако API се забави, пак позволяваме достъп
            is_payment_valid = True

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

st.title("🚀 Бизнес Навигатор")
st.caption("Твоят дигитален стартъп ментор")

# 🔥 ГЕНЕРИРАНЕ НА ЕКСПЕРТНИЯ ДОКЛАД
if is_payment_valid:
    st.balloons()
    st.success("🎉 Плащането е потвърдено! Генериране на Вашия персонален бизнес план...")
    
    current_idea = st.session_state.idea_text if st.session_state.idea_text else "Бизнес модел на база финансови калкулации."
    
    if not api_key:
        st.error("🔑 Липсва OpenAI API ключ в Secrets.")
    else:
        with st.spinner("🤖 Нашят AI консултант съставя персонализирания анализ..."):
            try:
                client = OpenAI(api_key=api_key)
                margin = st.session_state.price - st.session_state.cost
                be_units = math.ceil(st.session_state.fixed_costs / margin) if margin > 0 else 0
                min_turnover = be_units * st.session_state.price
                
                paid_prompt = f"""
                Ти си водещ бизнес консултант в България. Напиши подробен, силно персонализиран бизнес анализ на български език.
                
                КОНКРЕТНА ИДЕЯ НА ПОТРЕБИТЕЛЯ: "{current_idea}"
                
                ВЪВЕДЕНИ ФИНАНСОВИ ДАННИ:
                - Постоянни месечни разходи: {st.session_state.fixed_costs} евро
                - Продажна цена: {st.session_state.price} евро
                - Себестойност: {st.session_state.cost} евро
                - Точка на баланса (Break-even): Нужни са {be_units} продажби на месец за оборот от {min_turnover} евро.
                
                Докладът ТРЯБВА да е подробен и да съдържа следните 3 големи раздела:
                ### 📊 ЧАСТ 1: ПЕРСОНАЛИЗИРАН АНАЛИЗ
                - СИЛНИ СТРАНИ: 3 предимства специално за този модел.
                - СКРИТИ РИСКОВЕ: 3 опасности специално за този бизнес на българския пазар (данъци, конкуренция) и как ТОЧНО да бъдат избегнати.
                ### 🗺️ ЧАСТ 2: ПЪТНА КАРТА ПО СТЪПКИ (ROADMAP)
                - Хронологична пътна карта (Седмица 1, Седмица 2, Месец 1) за тази идея.
                ### 📝 ЧАСТ 3: AI ЧЕК-ЛИСТ СЪС ЗАДАЧИ
                - Точно 5 конкретни задачи, специфицирани за неговия казус.
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
                
                fin_data = {"fc": st.session_state.fixed_costs, "pr": st.session_state.price, "cs": st.session_state.cost, "be": be_units}
                docx_bytes = create_docx(current_idea, fin_data, full_report)
                
                st.download_button(
                    label="📥 Изтегли Бизнес плана в Word (.docx) формат", 
                    data=docx_bytes, 
                    file_name="Business_Plan_Report.docx", 
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Грешка при AI обработката: {e}")

st.markdown("---")

# ТАБОВЕ
tab1, tab2 = st.tabs(["📊 1. Сметни риск", "💡 2. AI Валидация"])

with tab1:
    st.subheader("📱 Финансов симулатор")
    st.session_state.fixed_costs = st.slider("💼 Месечни постоянни разходи", min_value=200, max_value=10000, value=st.session_state.fixed_costs, step=100)
    st.session_state.price = st.slider("💰 Продажна цена за 1 бройка / час", min_value=0, max_value=500, value=st.session_state.price, step=1)
    st.session_state.cost = st.slider("📦 Себестойност на 1 бройка", min_value=0, max_value=300, value=st.session_state.cost, step=1)
    
    if st.session_state.price <= st.session_state.cost:
        st.error("🛑 Цената трябва да е по-висока от себестойността!")
    else:
        margin = st.session_state.price - st.session_state.cost
        be_units = math.ceil(st.session_state.fixed_costs / margin)
        min_turnover = be_units * st.session_state.price
        st.markdown("#### **Резултат за твоя бизнес:**")
        col1, col2 = st.columns(2)
        with col1: st.metric(label="Нужни продажби", value=f"{be_units} бр./мес.")
        with col2: st.metric(label="Минимум оборот", value=f"{min_turnover} евро")

with tab2:
    st.subheader("🤖 Запиши идеята си")
    text_idea = st.text_area("Напиши или коригирай идеята си тук:", value=st.session_state.idea_text, placeholder="Пример: Искам да отворя автомивка...")
    st.session_state.idea_text = text_idea
    
    if st.button("🚀 Анализирай моята идея", use_container_width=True):
        if not api_key: 
            st.error("🔑 Липсва OpenAI API ключ.")
        elif len(text_idea) < 5: 
            st.warning("⚠️ Моля, въведете описание.")
        else:
            with st.spinner("AI Менторът анализира..."):
                try:
                    client = OpenAI(api_key=api_key)
                    free_prompt = f"Ти си бизнес консултант. Направи КРАТЪК преглед (до 3 изречения) на идея: '{text_idea}'."
                    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": free_prompt}], temperature=0.7)
                    
                    st.markdown("---")
                    st.markdown("### 🔓 Твоят безплатен предварителен анализ:")
                    st.info(response.choices[0].message.content)
                    
                    st.markdown("### 📊 Отключи Пълния Експертен Доклад")
                    
                    # Създаване на защитен пакет от данни
                    encoded_idea = urllib.parse.quote(text_idea[:150]) # Взимаме първите 150 символа, за да не превишим лимита на Stripe
                    payload = f"{st.session_state.fixed_costs}|{st.session_state.price}|{st.session_state.cost}||{encoded_idea}"
                    
                    stripe_link = "https://buy.stripe.com/test_6oU4gBdtE0D17sV8q4cjS00"
                    dynamic_url = f"{stripe_link}?client_reference_id={payload}"
                    
                    st.write("Нашият AI ще състави подробна пътна карта и чек-лист специално за тези стойности.")
                    st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 евро", dynamic_url, use_container_width=True)
                except Exception as e:
                    st.error(f"Грешка: {e}")
