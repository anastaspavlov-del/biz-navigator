import streamlit as st
import math
from openai import OpenAI
import stripe
import urllib.parse
from docx import Document
from io import BytesIO
import requests

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

# 📥 УЛАВЯНЕ НА ДАННИТЕ ОТ URL СЛЕД ПЛАЩАНЕ
session_id = st.query_params.get("session_id")

# Стойности по подразбиране
init_fixed_costs = 1200
init_price = 50
init_cost = 20
init_idea = ""

# 🔒 ДЕКОДИРАНЕ НА ДАННИТЕ ОТ STRIPE СЕСИЯТА
is_payment_valid = False
if session_id:
    with st.spinner("🔒 Проверка на плащането и възстановяване на данните..."):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                is_payment_valid = True
                
                # Вземаме скритите данни от client_reference_id
                ref_id = session.client_reference_id
                if ref_id and "|" in ref_id:
                    parts = ref_id.split("|", 3)
                    if len(parts) == 4:
                        init_fixed_costs = int(parts[0])
                        init_price = int(parts[1])
                        init_cost = int(parts[2])
                        init_idea = urllib.parse.unquote(parts[3])
                        
                        # Записваме ги веднага в сесията
                        st.session_state.fixed_costs = init_fixed_costs
                        st.session_state.price = init_price
                        st.session_state.cost = init_cost
                        st.session_state.idea_text = init_idea
        except Exception as e:
            st.error(f"Грешка при проверка на Stripe сесията: {e}")

# Ако потребителят сега отваря сайта за първи път, задаваме базовите стойности
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = init_fixed_costs
if "price" not in st.session_state: st.session_state.price = init_price
if "cost" not in st.session_state: st.session_state.cost = init_cost
if "idea_text" not in st.session_state: st.session_state.idea_text = init_idea

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

# 🔥 ГЕНЕРИРАНЕ НА ДОКЛАДА САМО ПРИ ДОКАЗАНО ПЛАЩАНЕ
if is_payment_valid:
    st.balloons()
    st.success("🎉 Плащането е потвърдено успешно! Твоят персонализиран бизнес план се генерира...")
    
    current_idea = st.session_state.idea_text
    if not current_idea or len(current_idea) < 5:
        current_idea = "Бизнес модел на база финансови калкулации."

    if not api_key:
        st.error("🔑 Липсва OpenAI API ключ в настройките.")
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
                """
                
                response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": paid_prompt}], temperature=0.7)
                full_report = response.choices[0].message.content
                
                st.markdown("## 📊 ТВОЯТ ПЕРСОНАЛИЗИРАН ЕКСПЕРТЕН БИЗНЕС ПЛАН")
                st.markdown(full_report)
                st.markdown("---")
                
                fin_data = {"fc": st.session_state.fixed_costs, "pr": st.session_state.price, "cs": st.session_state.cost, "be": be_units}
                docx_bytes = create_docx(current_idea, fin_data, full_report)
                
                st.download_button(label="📥 Изтегли Бизнес плана в редактируем Word (.docx) формат", data=docx_bytes, file_name="Business_Plan_Report.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Секция за финансиране
                st.info("### 💰 Нуждаеш ли се от финансиране за тази идея?")
                st.write("Ние си партнираме с сертифицирани кредитни консултанти, банкови институции и частни ангели-инвеститори. Изпрати концепцията си директно към тях:")
                
                with st.form("funding_form"):
                    user_name = st.text_input("Твоите Имена *")
                    user_phone = st.text_input("Телефон за връзка *")
                    user_email = st.text_input("Имейл адрес *")
                    requested_amount = st.number_input("Необходим стартиращ капитал (в евро)", min_value=1000, max_value=1000000, value=10000, step=500)
                    funding_type = st.selectbox("Предпочитан тип финансиране:", ["Банков кредит / Финансиране при ниска лихва", "Частен инвеститор срещу дял от бизнеса", "Съдействие от кредитен консултант за субсидия/програма"])
                    agree_terms = st.checkbox("Съгласен съм данните ми и финансовите калкулации да бъдат споделени с финансови институции и партньори.")
                    
                    submit_lead = st.form_submit_button("🚀 Изпрати проекта за одобрение", use_container_width=True)
                    if submit_lead:
                        if not user_name or not user_phone or not user_email or not agree_terms:
                            st.warning("⚠️ Моля, попълнете всички полета и се съгласете с условията.")
                        else:
                            st.success("🎯 Успешно изпратено! Партньорите ни ще се свържат с Вас до 48 часа.")
            except Exception as e:
                st.error(f"Грешка при генериране на доклада: {e}")
elif session_id and not is_payment_valid:
    st.error("🛑 Предоставеният идентификатор на плащане е невалиден.")

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📊 1. Сметни риск", "💡 2. AI Валидация"])

with tab1:
    st.subheader("📱 Финансов симулатор")
    st.write("Нагласи слайдерите с пръст, за да видиш минимума за оцеляване:")
    st.session_state.fixed_costs = st.slider("💼 Месечни постоянни разходи", min_value=200, max_value=10000, value=st.session_state.fixed_costs, step=100)
    st.session_state.price = st.slider("💰 Продажна цена за 1 бройка / час", min_value=0, max_value=500, value=st.session_state.price, step=1)
    st.session_state.cost = st.slider("📦 Себестойност на 1 бройка", min_value=0, max_value=300, value=st.session_state.cost, step=1)
    
    if st.session_state.price <= st.session_state.cost:
        st.error("🛑 Цената трябва да е по-висока от себестойността!")
    else:
        margin = st.session_state.price - st.session_state.cost
        be_units = math.ceil(st.session_state.fixed_costs / margin)
        min_turnover = be_units * st.session_state.price
        st.markdown("#### **Резултат за твоя business:**")
        col1, col2 = st.columns(2)
        with col1: st.metric(label="Нужни продажби", value=f"{be_units} бр./мес.")
        with col2: st.metric(label="Минимум оборот", value=f"{min_turnover} евро")

with tab2:
    st.subheader("🤖 Запиши идеята си")
    text_idea = st.text_area("Напиши или коригирай идеята си тук:", value=st.session_state.idea_text, placeholder="Пример: Искам да отворя автомивка...")
    st.session_state.idea_text = text_idea
    
    if st.button("🚀 Анализирай моята идея", use_container_width=True):
        if not api_key: st.error("🔑 Липсва OpenAI API ключ.")
        elif len(text_idea) < 5: st.warning("⚠️ Моля, въведете описание.")
        else:
            with st.spinner("AI Менторът изчислява финансовия риск..."):
                try:
                    client = OpenAI(api_key=api_key)
                    free_prompt = f"Ти си бизнес консултант. Направи КРАТЪК предварителен преглед (до 3 изречения) на тази бизнес идея: '{text_idea}'."
                    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": free_prompt}], temperature=0.7)
                    
                    st.markdown("---")
                    st.markdown("### 🔓 Твоят безплатен предварителен анализ:")
                    st.info(response.choices[0].message.content)
                    
                    st.markdown("### 📊 Отключи Пълния Експертен Доклад")
                    
                    # 🔐 КОДИРАНЕ НА ДАННИТЕ ЗА STRIPE ПО НАПЪЛНО СИГУРЕН НАЧИН
                    encoded_idea = urllib.parse.quote(text_idea)
                    # Сглобяваме всичко в един "пакет" данни, разделен с |
                    secret_payload = f"{st.session_state.fixed_costs}|{st.session_state.price}|{st.session_state.cost}|{encoded_idea}"
                    
                    # Използваме базовия Stripe линк, но закачаме данните към вградения параметър client_reference_id
                    stripe_link = "https://buy.stripe.com/6oU4gBdtE0D17sV8q4cjS00"
                    dynamic_url = f"{stripe_link}?client_reference_id={secret_payload}"
                    
                    st.write("Нашият AI ще състави подробна пътна карта, чек-лист и ще те свърже с партньори за финансиране.")
                    st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 евро", dynamic_url, use_container_width=True)
                except Exception as e:
                    st.error(f"Грешка: {e}")
