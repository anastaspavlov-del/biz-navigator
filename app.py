import streamlit as st
import math
import json
import re
import base64
from openai import OpenAI
import stripe
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

# 📥 УЛАВЯНЕ НА ДАННИТЕ ОТ URL
session_id = st.query_params.get("session_id")

# Базови стойности по подразбиране в session_state
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = 1200
if "price" not in st.session_state: st.session_state.price = 50
if "cost" not in st.session_state: st.session_state.cost = 20
if "idea_text" not in st.session_state: st.session_state.idea_text = ""
if "verified_sessions" not in st.session_state: st.session_state.verified_sessions = {}
if "generated_reports" not in st.session_state: st.session_state.generated_reports = {}

CLIENT_REF_MAX_LEN = 200  # твърд лимит на Stripe за client_reference_id

# 🌟 ПРЕНАСЯНЕ НА ФИНАНСИ + ИДЕЯ ПРЕЗ STRIPE ПЛАЩАНЕТО (client_reference_id)
#
# Stripe приема в client_reference_id САМО alphanumeric, "-" и "_" (до 200
# символа) - всичко останало "тихо" се изтрива. Затова:
#   1. Не ползваме "|" като разделител (невалиден символ -> цялото поле пада).
#   2. Не ползваме localStorage/components.html - той тече в iframe, чийто
#      произход спрямо главната страница не е гарантирано same-origin, така
#      че не е надежден начин да се пренесат данни през пълен redirect.
#   3. Кодираме финансите И идеята заедно в JSON -> base64url (без padding),
#      чиято азбука (A-Za-z0-9-_) съвпада точно с разрешените от Stripe знаци.
def encode_client_ref(fixed_costs, price, cost, idea, max_len=CLIENT_REF_MAX_LEN):
    def build(idea_text):
        payload = json.dumps(
            {"c": fixed_costs, "p": price, "s": cost, "i": idea_text},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")

    encoded = build(idea)
    idea_bytes = idea.encode("utf-8")
    # Ако кодирането излезе над лимита (напр. дълга идея), режем побайтово,
    # без да чупим многобайтови UTF-8 символи по средата.
    while len(encoded) > max_len and idea_bytes:
        idea_bytes = idea_bytes[:-1]
        idea = idea_bytes.decode("utf-8", errors="ignore")
        idea_bytes = idea.encode("utf-8")
        encoded = build(idea)
    return encoded


def decode_client_ref(ref):
    if not ref:
        return None
    try:
        padded = ref + "=" * (-len(ref) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        return {
            "fixed_costs": int(data["c"]),
            "price": int(data["p"]),
            "cost": int(data["s"]),
            "idea": str(data.get("i", "")),
        }
    except Exception as e:
        print(f"[client_reference_id] Неуспешно декодиране '{ref}': {e}")
        return None


# Функция за сигурна проверка на плащането в Stripe (винаги през реалното Stripe API)
def get_stripe_session(sid):
    if not sid:
        return None
    try:
        return stripe.checkout.Session.retrieve(sid)
    except Exception as e:
        # Не показваме суровата грешка на потребителя - само в сървърния лог.
        print(f"[Stripe] Грешка при извличане на сесия {sid}: {e}")
        return None

stripe_session = None
is_payment_valid = False

if session_id:
    if session_id in st.session_state.verified_sessions:
        stripe_session = st.session_state.verified_sessions[session_id]
    else:
        with st.spinner("🔒 Проверка на статуса на плащането..."):
            stripe_session = get_stripe_session(session_id)
        st.session_state.verified_sessions[session_id] = stripe_session

    if stripe_session is not None:
        is_payment_valid = stripe_session.payment_status == "paid"
    else:
        st.sidebar.warning("⚠️ Неуспешна проверка на плащането. Презаредете страницата или се свържете с поддръжка.")

# Прилагаме платените финанси + идея (декодирани от client_reference_id) точно веднъж на сесия.
if is_payment_valid and st.session_state.get("applied_payment_session") != session_id:
    decoded = decode_client_ref(stripe_session.client_reference_id if stripe_session else None)
    if decoded:
        st.session_state.fixed_costs = decoded["fixed_costs"]
        st.session_state.price = decoded["price"]
        st.session_state.cost = decoded["cost"]
        st.session_state.idea_text = decoded["idea"]
    st.session_state.applied_payment_session = session_id

# Функция за добавяне на параграф с поддръжка на **bold** маркиране
def add_formatted_paragraph(doc, text):
    p = doc.add_paragraph()
    parts = re.split(r"(\*\*.+?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = p.add_run(part[2:-2])
            run.bold = True
        else:
            p.add_run(part)
    return p

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
                add_formatted_paragraph(doc, paragraph.strip())

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

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
        st.error("🔑 Липсва OpenAI API ключ в настройките.")
    else:
        margin = st.session_state.price - st.session_state.cost
        be_units = math.ceil(st.session_state.fixed_costs / margin) if margin > 0 else 0
        min_turnover = be_units * st.session_state.price

        if session_id in st.session_state.generated_reports:
            full_report = st.session_state.generated_reports[session_id]
        else:
            full_report = None
            with st.spinner("🤖 Експертният AI консултант анализира ТВОЯТА идея..."):
                try:
                    client = OpenAI(api_key=api_key)

                    paid_prompt = f"""
                    Ти си топ бизнес консултант за стартиращи компании в България.
                    Напиши изключително подробен, строго персонализиран бизнес анализ на български език.

                    КОНКРЕТНА ИДЕЯ НА ПОТРЕБИТЕЛЯ: "{current_idea}"

                    ВЪВЕДЕНИ ФИНАНСИ ОТ ПОТРЕБИТЕЛЯ:
                    - Постоянни месечни разходи: {st.session_state.fixed_costs} евро
                    - Продажна цена на бройка/час: {st.session_state.price} евро
                    - Себестойност на бройка/минимален разход: {st.session_state.cost} евро
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
                    st.session_state.generated_reports[session_id] = full_report

                except Exception as e:
                    print(f"[OpenAI] Грешка при генериране на доклад за сесия {session_id}: {e}")
                    st.error("⚠️ Възникна временен проблем при генерирането на доклада. Моля, презаредете страницата.")

        if full_report:
            st.markdown("## 📊 ТВОЯТ ПЕРСОНАЛИЗИРАН ЕКСПЕРТЕН БИЗНЕС ПЛАН")
            st.markdown(full_report)
            st.markdown("---")

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

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["📊 1. Сметни риск", "💡 2. AI Валидация"])

# TAB 1: Financial Simulator
with tab1:
    st.subheader("📱 Финансов симулатор")
    st.slider("💼 Месечни постоянни разходи", min_value=200, max_value=10000, step=100, key="fixed_costs")
    st.slider("💰 Продажна цена за 1 бройка / час", min_value=0, max_value=500, step=1, key="price")
    st.slider("📦 Себестойност на 1 бройка", min_value=0, max_value=300, step=1, key="cost")

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

# TAB 2: AI Validation
with tab2:
    st.subheader("🤖 Запиши идеята си")
    text_idea = st.text_area(
        "Напиши или коригирай идеята си тук (кратко описание в едно-две изречения):",
        placeholder="Пример: Искам да отворя автомивка с 4 бокса в центъра на София...",
        key="idea_text",
        max_chars=200,
        help="Дръж описанието кратко - ако е твърде дълго, при плащането ще видиш бележка, че за пълния доклад се ползва само началото на текста.",
    )

    if st.button("🚀 Анализирай моята идея", use_container_width=True):
        if not api_key:
            st.error("🔑 Липсва OpenAI API ключ.")
        elif len(text_idea) < 5:
            st.warning("⚠️ Моля, въведете описание.")
        else:
            with st.spinner("AI Менторът изчислява финансовия риск..."):
                try:
                    client = OpenAI(api_key=api_key)
                    free_prompt = f"Ти си бизнес консултант. Направи КРАТЪК преглед (до 3 изречения) на идея: '{text_idea}'."
                    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": free_prompt}], temperature=0.7)

                    st.markdown("---")
                    st.markdown("### 🔓 Твоят безплатен предварителен анализ:")
                    st.info(response.choices[0].message.content)

                    st.markdown("### 📊 Отключи Пълния Експертен Доклад")

                    client_ref = encode_client_ref(
                        st.session_state.fixed_costs,
                        st.session_state.price,
                        st.session_state.cost,
                        text_idea,
                    )
                    embedded = decode_client_ref(client_ref)
                    if embedded and len(embedded["idea"]) < len(text_idea):
                        st.caption(
                            f"ℹ️ Заради ограничение на платежната система, в пълния доклад ще "
                            f"използваме първите {len(embedded['idea'])} символа от идеята ти."
                        )

                    stripe_link = "https://buy.stripe.com/6oU4gBdtE0D17sV8q4cjS00"
                    dynamic_url = f"{stripe_link}?client_reference_id={client_ref}"

                    st.write("Нашият AI ще състави подробна пътна карта и чек-лист специално за тези стойности.")
                    st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 евро", dynamic_url, use_container_width=True)
                except Exception as e:
                    print(f"[OpenAI] Грешка при безплатен анализ: {e}")
                    st.error("⚠️ Възникна временен проблем. Моля, опитайте отново.")
