import streamlit as st
import math
from openai import OpenAI

# 1. Оптимизация за мобилни устройства
st.set_page_config(
    page_title="Бизнес Навигатор", 
    page_icon="🚀", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Инициализация на данните в сесията
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = 1200
if "price" not in st.session_state: st.session_state.price = 50
if "cost" not in st.session_state: st.session_state.cost = 20

# Заглавие на приложението
st.title("🚀 Бизнес Навигатор")
st.caption("Твоят дигитален стартъп ментор")

# Създаване на табовете
tab1, tab2 = st.tabs(["📊 1. Сметни риск", "💡 2. AI Валидация"])

# ==========================================
# ТАБ 1: ФИНАНСОВ СИМУЛАТОР
# ==========================================
with tab1:
    st.subheader("📱 Финансов симулатор")
    st.write("Нагласи слайдерите с пръст, за да видиш минимума за оцеляване:")
    
    st.session_state.fixed_costs = st.slider(
        "💼 Месечни постоянни разходи (наем, осигуровки)", 
        min_value=200, max_value=10000, value=st.session_state.fixed_costs, step=100
    )
    
    st.session_state.price = st.slider(
        "💰 Продажна цена за 1 бройка / час", 
        min_value=5, max_value=500, value=st.session_state.price, step=5
    )
    
    st.session_state.cost = st.slider(
        "📦 Себестойност на 1 бройка (материали/доставка)", 
        min_value=0, max_value=300, value=st.session_state.cost, step=5
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
            st.metric(label="Минимум оборот", value=f"{min_turnover} лв.")
            
        st.info(f"💡 Това означава средно по **{be_units/30:.1f} продажби на ден**, за да излезеш на нула.")

# ==========================================
# ТАБ 2: AI ВАЛИДАЦИЯ (МОДЕЛ С ПЛАЩАНЕ ЗА ДОКЛАД)
# ==========================================
with tab2:
    st.subheader("🤖 Запиши идеята си")
    st.write("Въведи твоя OpenAI API ключ в полето, за да активираш учения ментор:")
    
    api_key = st.text_input("Въведи OpenAI API Key:", type="password")
    
    st.markdown("---")
    st.write("🎙️ **Запиши гласово описание на бизнеса си или го напиши от клавиатурата:**")
    
    audio_file = st.audio_input("Запиши гласово описание")
    text_idea = st.text_area("Или напиши идеята тук:", placeholder="Пример: Искам да отворя автомивка в Люлин...")
    
    if st.button("🚀 Анализирай моята идея", use_container_width=True):
        if not api_key:
            st.error("🔑 Моля, постави твоя OpenAI API ключ в полето горе.")
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
                        Финанси: Месечен разход {st.session_state.fixed_costs} лв. Нужни продажби: {be_units} бр.
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
                        
                        stripe_link = "https://buy.stripe.com/your_custom_payment_link" 
                        st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 лв.", stripe_link, use_container_width=True)
                        
                        st.caption("🔒 Сигурно плащане. Ще получиш доклада си веднага след трансакцията.")
                        
                    except Exception as e:
                        st.error(f"Грешка при връзката с AI: {e}")
            else:
                st.warning("⚠️ Моля, въведете текст или направете запис.")

