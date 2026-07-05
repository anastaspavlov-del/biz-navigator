import streamlit as st
import math
from openai import OpenAI
import urllib.parse  # За правилно кодиране на текста в линка

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

# API Key Check
api_key = st.secrets.get("OPENAI_API_KEY", "")

# 📥 УЛАВЯНЕ НА ДИНАМИЧНИТЕ ДАННИ ОТ URL СЛЕД ПЛАЩАНЕ
is_paid = st.query_params.get("paid") == "true"
url_fixed_costs = st.query_params.get("fc")
url_price = st.query_params.get("pr")
url_cost = st.query_params.get("cs")
url_idea = st.query_params.get("idea", "")

# Ако потребителят е платил и има данни в URL, взимаме тях. Ако липсват, слагаме дефолтни.
init_fixed_costs = int(url_fixed_costs) if url_fixed_costs else 1200
init_price = int(url_price) if url_price else 50
init_cost = int(url_cost) if url_cost else 20
init_idea = urllib.parse.unquote(url_idea) if url_idea else ""

# Session State Initialization
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = init_fixed_costs
if "price" not in st.session_state: st.session_state.price = init_price
if "cost" not in st.session_state: st.session_state.cost = init_cost
if "idea_text" not in st.session_state: st.session_state.idea_text = init_idea

# UI Header
st.title("🚀 Бизнес Навигатор")
st.caption("Твоят дигитален стартъп ментор")

# 🔥 ГЕНЕРИРАНЕ НА ДОКЛАДА С РЕАЛНИТЕ ДАННИ
if is_paid:
    st.balloons()
    st.success("🎉 Плащането е успешно! Твоят персонализиран бизнес план се генерира...")
    
    # Използваме изпратената през URL идея или тази от сесията
    current_idea = init_idea if init_idea else st.session_state.idea_text
    
    if not current_idea or len(current_idea) < 5:
        st.warning("⚠️ Не намерихме запазено текстово описание на идеята. Използваме финансовите параметри за анализ.")
        current_idea = "Бизнес модел на база финансови калкулации."

    if not api_key:
        st.error("🔑 Липсва OpenAI API ключ в настройките. Добавете го в Secrets.")
    else:
        with st.spinner("🤖 Експертният AI консултант анализира ТВОЯТА идея... (може да отнеме до 30 сек)"):
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
                
                Докладът ТРЯБВА да е дълъг и да съдържа следните 4 големи раздела, форматирани с ясни заглавия (Markdown):
                
                ### 📊 ЧАСТ 1: ПЕРСОНАЛИЗИРАН АНАЛИЗ ЗА "{current_idea}"
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
                
                # 📥 СВАЛЯНЕ КАТО ПЪЛЕН ДОКУМЕНТ (ПЕРФЕКТНА КИРИЛИЦА)
                file_content = f"БИЗНЕС НАВИГАТОР - ЕКСПЕРТЕН ДОКЛАД\n" \
                               f"Идея: {current_idea}\n" \
                               f"Финанси: Разходи {st.session_state.fixed_costs}€, Цена {st.session_state.price}€\n" \
                               f"=========================================\n\n" \
                               f"{full_report}"
                
                st.download_button(
                    label="📥 Изтегли Бизнес плана + Чек-листа (.txt формат)",
                    data=file_content.encode('utf-8'),
                    file_name="Business_Plan_Report.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
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
                    margin = st.session_state.price - st.session_state.cost
                    be_units = math.ceil(st.session_state.fixed_costs / margin) if margin > 0 else 0
                    
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
                    
                    # 🔗 СГЛОБЯВАНЕ НА ДИНАМИЧНИЯ ЛИНК С ДАННИТЕ НА ПОТРЕБИТЕЛЯ
                    encoded_idea = urllib.parse.quote(text_idea)
                    
                    # В реалния Stripe променяте линка тук, но за вашия тест:
                    dynamic_url = f"https://biz-navigator.streamlit.app/?paid=true" \
                                  f"&fc={st.session_state.fixed_costs}" \
                                  f"&pr={st.session_state.price}" \
                                  f"&cs={st.session_state.cost}" \
                                  f"&idea={encoded_idea}"
                    
                    st.write("Нашият AI ще състави подробна пътна карта и чек-лист специално за тези стойности.")
                    
                    # Бутон, който симулира/пренасочва с реалните данни
                    st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 евро", dynamic_url, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Грешка: {e}")
