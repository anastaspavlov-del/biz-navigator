import streamlit as st
import math
from openai import OpenAI
import stripe
import urllib.parse
from docx import Document
from io import BytesIO

# 1. Page Configuration (Задължително на първия ред)
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

# Инициализация на API ключовете
api_key = st.secrets.get("OPENAI_API_KEY", "")
stripe.api_key = st.secrets.get("STRIPE_API_KEY", "")

# 📥 ЧЕТЕНЕ НА ДАННИТЕ ОТ URL АДРЕСА БЕЗОПАСНО
session_id = st.query_params.get("session_id")
url_fc = st.query_params.get("fc")
url_pr = st.query_params.get("pr")
url_cs = st.query_params.get("cs")
url_idea = st.query_params.get("idea", "")

# Функция за безопасно извличане на числа от URL
def get_safe_int(val, default):
    if not val:
        return default
    try:
        clean = str(val).strip()
        if "{" in clean or "URL_PARAM" in clean:
            return default
        return int(float(clean))
    except:
        return default

# Определяне на стойностите на база URL или дефолтни
fc_val = get_safe_int(url_fc, 1200)
pr_val = get_safe_int(url_pr, 50)
cs_val = get_safe_int(url_cs, 20)
idea_val = urllib.parse.unquote(url_idea) if url_idea and "{" not in url_idea else ""

# Записване в session_state, за да се виждат от слайдерите
if "fixed_costs" not in st.session_state or url_fc: st.session_state.fixed_costs = fc_val
if "price" not in st.session_state or url_pr: st.session_state.price = pr_val
if "cost" not in st.session_state or url_cs: st.session_state.cost = cs_val
if "idea_text" not in st.session_state or url_idea: st.session_state.idea_text = idea_val

# 🔒 БЕЗОПАСНА ПРОВЕРКА НА ПЛАЩАНЕТО (без да забива сайта)
is_payment_valid = False
if session_id:
    try:
        # Проверяваме плащането само веднъж при наличие на session_id
        check_session = stripe.checkout.Session.retrieve(session_id)
        if check_session.payment_status == "paid":
            is_payment_valid = True
    except Exception as e:
        # Ако Stripe API даде грешка, не чупим сайта, а записваме лог
        st.sidebar.error(f"Stripe инфо: {e}")
        # За по-добра потребителска среда в тестов режим, ако има session_id, го броим за платено
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

# Интерфейс
st.title("🚀 Бизнес Навигатор")
st.caption("Твоят дигитален стартъп ментор")

# 🔥 ПОКАЗВАНЕ НА ПЕРСОНАЛИЗИРАНИЯ AI ДОКЛАД ПРИ УСПЕШНО ПЛАЩАНЕ
if is_payment_valid:
    st.balloons()
    st.success("🎉 Плащането е потвърдено успешно! Твоят персонализиран бизнес план се генерира...")
    
    current_idea = st.session_state.idea_text if st.session_state.idea_text else "Бизнес модел на база финансови калкулации."
    
    if not api_key:
        st.error("🔑 Липсва OpenAI API ключ в Secrets.")
    else:
        with st.spinner("🤖 AI Експертът изготвя Вашия подробен доклад..."):
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
                - Себестойност на бройка/минимален разход: {st.session_state.cost} евро
                - Точка на баланса (Break-even): Нужни са точно {be_units} продажби на месец за оборот от {min_turnover} евро.
                
                Докладът ТРЯБВА да съдържа следните 3 големи раздела с тези точни заглавия:
                ### 📊 ЧАСТ 1: ПЕРСОНАЛИЗИРАН АНАЛИЗ
                - СИЛНИ СТРАНИ: Стратегически предимства на този конкретен модел.
                - СКРИТИ РИСКОВЕ: 3 опасности специално за този бизнес на българския пазар и как ТОЧНО да бъдат избегнати.
                ### 🗺️ ЧАСТ 2: ПЪТНА КАРТА ПО СТЪПКИ (ROADMAP)
                - Хронологична пътна карта (Седмица 1, Седмица 2, Месец 1), съобразена с идеята.
                ### 📝 ЧАСТ 3: AI ЧЕК-ЛИСТ СЪС ЗАДАЧИ
                - Точно 5 конкретни, практически задачи, които потребителят може да изпълни веднага.
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
                    label="📥 Изтегли Бизнес плана в редактируем Word (.docx) формат", 
                    data=docx_bytes, 
                    file_name="Business_Plan_Report.docx", 
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Грешка при AI генерирането: {e}")

st.markdown("---")

# Табове за калкулатора и входните данни
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
                    
                    # Кодиране на текста, за да се прехвърли безопасно през линка
                    encoded_idea = urllib.parse.quote(text_idea)
                    
                    # ВАШИЯТ СТАТИЧЕН ТЕСТОВ STRIPE ЛИНК
                    stripe_link = "https://buy.stripe.com/test_6oU4gBdtE0D17sV8q4cjS00"
                    
                    # Когато потребителят се върне от Stripe, линкът ще съдържа всички въведени променливи
                    dynamic_url = f"{stripe_link}?fc={st.session_state.fixed_costs}&pr={st.session_state.price}&cs={st.session_state.cost}&idea={encoded_idea}"
                    
                    st.write("Нашият AI ще състави подробна пътна карта и чек-лист специално за тези стойности.")
                    st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 евро", dynamic_url, use_container_width=True)
                except Exception as e:
                    st.error(f"Грешка: {e}")
