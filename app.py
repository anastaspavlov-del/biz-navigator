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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Histats безплатен невидим брояч
st.markdown(
    '<a href="https://www.histats.com" target="_blank">'
    '<img src="https://sstatic1.histats.com/0.gif?5036919&101" alt="Histats" border="0" style="display:none;">'
    '</a>',
    unsafe_allow_html=True
)

# 🎨 ВИЗУАЛНА ТЕМА (тъмно червено-черно, зелени акценти, картови контейнери)
st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse 90% 60% at 50% -5%, #6b0f0f 0%, transparent 60%),
            linear-gradient(180deg, #1c0505 0%, #100202 55%, #0a0101 100%);
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        opacity: 0.05;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='104' viewBox='0 0 60 104'%3E%3Cpolygon points='30,0 60,17 60,52 30,69 0,52 0,17' fill='none' stroke='%23ff6666' stroke-width='1'/%3E%3C/svg%3E");
        background-size: 60px 104px;
        z-index: 0;
    }

    /* --- Responsive ширина: пълен екран на десктоп, центрирано до разумен
       максимум, пълна ширина на мобилни устройства --- */
    [data-testid="stMainBlockContainer"] {
        position: relative;
        z-index: 1;
        max-width: 900px;
        margin: 0 auto;
        padding-top: 1rem !important;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    [data-testid="stHeader"] { height: 2.2rem; background: transparent; }
    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"] {
            max-width: 100%;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
            padding-top: 0.6rem !important;
        }
    }

    /* --- Пояснителни/вторични текстове: по-светъл цвят --- */
    [data-testid="stCaptionContainer"] p { color: #e3cccc !important; }

    /* --- Табове като "pill" бутони --- */
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 10px; border-bottom: none; }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none; }
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }
    [data-testid="stTab"] {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 14px;
        padding: 10px 8px;
        justify-content: center;
    }
    [data-testid="stTab"] p { font-weight: 600; font-size: 0.95rem; }
    [data-testid="stTab"]:nth-of-type(1)[aria-selected="true"] {
        background: linear-gradient(135deg, #3b5bfd, #2540c9);
        border-color: transparent;
    }
    [data-testid="stTab"]:nth-of-type(2)[aria-selected="true"] {
        background: linear-gradient(135deg, #9333ea, #6b21a8);
        border-color: transparent;
    }

    /* --- Картови контейнери: st.container(key="card_...") --- */
    div[class*="st-key-card_"] {
        background: rgba(40, 10, 10, 0.55);
        border: 1px solid rgba(220, 70, 70, 0.30) !important;
        border-radius: 16px;
        padding: 14px 16px 4px 16px;
    }
    .bn-label { font-weight: 600; font-size: 0.98rem; margin-bottom: 2px; }
    .bn-sublabel { color: #e3cccc; font-size: 0.82rem; font-weight: 400; }

    /* --- Слайдер зелен (допълва темата), номер-инпут да пасва на картата --- */
    [data-testid="stNumberInput"] input {
        background: rgba(0,0,0,0.35) !important;
        border: 1px solid #22c55e !important;
        color: #4ade80 !important;
        font-weight: 700 !important;
        font-size: 1.25rem !important;
        border-radius: 10px !important;
        text-align: center;
    }
    [data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] { display: none; }
    /* Visually appended € sign (widget value itself stays numeric) */
    [data-testid="stNumberInputContainer"] { position: relative; }
    [data-testid="stNumberInputContainer"]::after {
        content: "€";
        position: absolute;
        right: 14px;
        top: 50%;
        transform: translateY(-50%);
        color: #4ade80;
        font-weight: 700;
        font-size: 1.1rem;
        pointer-events: none;
    }
    [data-testid="stNumberInputField"] { padding-right: 30px !important; }

    /* --- Стат карти: st.container(key="stat_...") --- */
    div[class*="st-key-stat_"] {
        background: rgba(40, 10, 10, 0.55);
        border: 1px solid rgba(220, 70, 70, 0.30) !important;
        border-radius: 16px;
        text-align: center;
        padding: 16px 10px !important;
    }
    div[class*="st-key-stat_"] [data-testid="stMarkdownContainer"] { width: 100%; text-align: center; margin-bottom: 0 !important; }
    .bn-stat-label { color: #e7d3d3; font-size: 0.85rem; margin-bottom: 4px; text-align: center; }
    .bn-stat-value { color: #4ade80; font-size: 2.3rem; font-weight: 800; line-height: 1.1; text-align: center; }
    .bn-stat-unit { color: #e3cccc; font-size: 0.8rem; text-align: center; }

    /* --- Tip box: st.container(key="tip_box") --- */
    div[class*="st-key-tip_box"] {
        background: rgba(34, 197, 94, 0.08);
        border: 1px solid rgba(74, 222, 128, 0.35) !important;
        border-radius: 14px;
        display: flex !important;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 68px;
        padding: 14px 16px !important;
    }
    div[class*="st-key-tip_box"] [data-testid="stMarkdownContainer"] { width: 100%; text-align: center; margin-bottom: 0 !important; }
    div[class*="st-key-tip_box"] p { color: #86efac !important; margin: 0; text-align: center; }

    /* --- CTA бутони (зелени, като в дизайна) --- */
    [data-testid="stButton"] button, [data-testid="stLinkButton"] a {
        background: linear-gradient(135deg, #22c55e, #16a34a) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        padding: 0.8rem 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# API Keys Check от Secrets
api_key = st.secrets.get("OPENAI_API_KEY", "")

# 📥 УЛАВЯНЕ НА ДАННИТЕ ОТ URL
session_id = st.query_params.get("session_id")

# 🧪 ТЕСТОВ РЕЖИМ, ВИДИМ САМО ЗА СОБСТВЕНИКА (за донастройки на живо, без риск
# обикновени посетители да ползват тестова карта вместо реално плащане).
#
# - Преди плащане: тестовият линк се показва само ако в URL-а има таен параметър
#   ?owner_test=<OWNER_TEST_TOKEN>, известен само на теб. Обикновените посетители
#   никога не виждат и не могат да отворят тестовия линк.
# - След плащане: ?owner_test не преживява Stripe redirect-а (Stripe връща само
#   session_id), затова режимът се определя directly от префикса на самото
#   session_id - Stripe маркира тестовите сесии с "cs_test_", реалните с "cs_live_".
#   Това работи независимо дали тайният параметър е останал в адреса.
STRIPE_API_KEY_LIVE = st.secrets.get("STRIPE_API_KEY_LIVE", st.secrets.get("STRIPE_API_KEY", ""))
STRIPE_API_KEY_TEST = st.secrets.get("STRIPE_API_KEY_TEST", "")
STRIPE_LINK_LIVE = st.secrets.get("STRIPE_LINK_LIVE", "https://buy.stripe.com/6oU4gBdtE0D17sV8q4cjS00")
STRIPE_LINK_TEST = st.secrets.get("STRIPE_LINK_TEST", "https://buy.stripe.com/test_6oU4gBdtE0D17sV8q4cjS00")
OWNER_TEST_TOKEN = st.secrets.get("OWNER_TEST_TOKEN", "")

if session_id:
    use_test_mode = session_id.startswith("cs_test_")
else:
    use_test_mode = bool(OWNER_TEST_TOKEN) and st.query_params.get("owner_test") == OWNER_TEST_TOKEN

stripe.api_key = STRIPE_API_KEY_TEST if use_test_mode else STRIPE_API_KEY_LIVE
STRIPE_LINK = STRIPE_LINK_TEST if use_test_mode else STRIPE_LINK_LIVE

if use_test_mode:
    st.sidebar.warning("🧪 Тестов режим е активен (видим само за теб чрез тайния параметър).")

# Базови стойности по подразбиране в session_state
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = 1200
if "price" not in st.session_state: st.session_state.price = 50
if "cost" not in st.session_state: st.session_state.cost = 20
if "idea_text" not in st.session_state: st.session_state.idea_text = ""
if "verified_sessions" not in st.session_state: st.session_state.verified_sessions = {}
if "generated_reports" not in st.session_state: st.session_state.generated_reports = {}

CLIENT_REF_MAX_LEN = 200  # твърд лимит на Stripe за client_reference_id

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


def get_stripe_session(sid):
    if not sid:
        return None
    try:
        return stripe.checkout.Session.retrieve(sid)
    except Exception as e:
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

if is_payment_valid and st.session_state.get("applied_payment_session") != session_id:
    decoded = decode_client_ref(stripe_session.client_reference_id if stripe_session else None)
    if decoded:
        st.session_state.fixed_costs = decoded["fixed_costs"]
        st.session_state.price = decoded["price"]
        st.session_state.cost = decoded["cost"]
        st.session_state.idea_text = decoded["idea"]
    st.session_state.applied_payment_session = session_id

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

def synced_metric(key, label_html, min_v, max_v, step, help_text=None):
    """Слайдер + число, синхронизирани в двете посоки, увити в стилизирана карта."""
    slider_key = f"{key}__slider"
    num_key = f"{key}__num"
    if slider_key not in st.session_state:
        st.session_state[slider_key] = st.session_state[key]
    if num_key not in st.session_state:
        st.session_state[num_key] = st.session_state[key]

    def _from_slider():
        v = st.session_state[slider_key]
        st.session_state[key] = v
        st.session_state[num_key] = v

    def _from_num():
        v = max(min_v, min(max_v, st.session_state[num_key]))
        st.session_state[key] = v
        st.session_state[slider_key] = v
        st.session_state[num_key] = v

    with st.container(border=True, key=f"card_{key}"):
        st.markdown(f'<div class="bn-label">{label_html}</div>', unsafe_allow_html=True)
        col_slider, col_num = st.columns([2.4, 1], vertical_alignment="center")
        with col_slider:
            st.slider("", min_value=min_v, max_value=max_v, step=step,
                       key=slider_key, on_change=_from_slider, label_visibility="collapsed",
                       help=help_text)
        with col_num:
            st.number_input("", min_value=min_v, max_value=max_v, step=step,
                             key=num_key, on_change=_from_num, label_visibility="collapsed")
    return st.session_state[key]


st.title("🚀 Бизнес Навигатор")
st.caption("Твоят дигитален стартъп ментор")

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

                    daily_sales_needed = be_units / 30 if be_units else 0

                    paid_prompt = f"""
                    Ти си топ бизнес консултант с 20 години опит в съветването на стартиращи
                    компании в България — работил си с банки, инвеститори и над 500 малки бизнеса.
                    Пишеш доклади, за които клиентите казват, че си им спестил месеци проучване.

                    Напиши изключително подробен, дълбоко персонализиран и максимално професионален
                    бизнес доклад на български език. Никакви общи приказки, никакви клишета като
                    "усърдна работа" или "вярвай в себе си" — само конкретни, приложими съвети,
                    основани на числата и идеята на потребителя. Пиши все едно клиентът е платил
                    500 евро за консултация с реален експерт, не за автоматичен текст.

                    КОНКРЕТНА ИДЕЯ НА ПОТРЕБИТЕЛЯ: "{current_idea}"

                    ВЪВЕДЕНИ ФИНАНСИ ОТ ПОТРЕБИТЕЛЯ:
                    - Постоянни месечни разходи: {st.session_state.fixed_costs} евро
                    - Продажна цена на бройка/час: {st.session_state.price} евро
                    - Себестойност на бройка/минимален разход: {st.session_state.cost} евро
                    - Марж на бройка/час: {margin} евро
                    - Точка на баланса (Break-even): Нужни са точно {be_units} продажби на месец
                      (средно {daily_sales_needed:.1f} на ден) за оборот от {min_turnover} евро,
                      само за да покрият разходите (нулева печалба).

                    Докладът ТРЯБВА да съдържа следните раздели, с точно тези заглавия, в този ред,
                    и да е богат на конкретика — навсякъде, където е relevant, цитирай директно
                    числата по-горе:

                    ### 📊 ЧАСТ 1: ОБОБЩЕНИЕ ЗА РЪКОВОДСТВОТО (EXECUTIVE SUMMARY)
                    - 3-4 изречения, обобщаващи реалистичната перспектива пред този конкретен бизнес:
                      колко трудно/лесно е да се стигне до break-even с тези числа, и какъв е
                      най-големият шанс за успех.

                    ### 💪 ЧАСТ 2: ПЕРСОНАЛИЗИРАН АНАЛИЗ НА МОДЕЛА
                    - СИЛНИ СТРАНИ: 3-те най-големи стратегически предимства на този конкретен модел,
                      всяко обяснено в 2-3 изречения защо точно за тази идея и тези числа е предимство.
                    - СКРИТИ РИСКОВЕ: 3-те най-големи опасности специално за този бизнес на българския
                      пазар (данъци и осигуровки, скрита/наситена конкуренция, регулации, сезонност,
                      кешфлоу), с КОНКРЕТЕН начин за избягване на всеки риск, не просто описание.

                    ### 💰 ЧАСТ 3: ФИНАНСОВА СТРАТЕГИЯ И ЦЕНООБРАЗУВАНЕ
                    - Кратка интерпретация какво точно означава маржът от {margin} евро на бройка/час
                      за устойчивостта на бизнеса.
                    - Конкретна препоръка: трябва ли цената/себестойността да се коригират, и с колко,
                      за да бъде break-even точката реалистично достижима.
                    - Три сценария за първите 3 месеца (консервативен, реалистичен, оптимистичен) —
                      за всеки: очакван брой продажби на месец и прогнозна печалба/загуба в евро.

                    ### 🗺️ ЧАСТ 4: ПЪТНА КАРТА ПО СТЪПКИ (ROADMAP)
                    - Детайлна хронологична пътна карта, специфична за тази идея, разбита по:
                      Седмица 1, Седмица 2, Седмица 3-4, Месец 2, Месец 3 — какво точно се прави
                      всяка от тези фази и защо е точно в тази последователност.

                    ### 📣 ЧАСТ 5: МАРКЕТИНГ И ПРИДОБИВАНЕ НА ПЪРВИ КЛИЕНТИ
                    - 3 конкретни, нискобюджетни маркетингови канала/тактики, подходящи специално
                      за тази идея и българския пазар, с приблизителен бюджет и очакван резултат за всеки.

                    ### 📝 ЧАСТ 6: AI ЧЕК-ЛИСТ СЪС ЗАДАЧИ ЗА ТАЗИ СЕДМИЦА
                    - Списък от точно 5 конкретни, практически задачи, специфични за този бизнес,
                      подредени по приоритет, които потребителят може да изпълни веднага.

                    ### 🎯 ЗАКЛЮЧЕНИЕ
                    - 2-3 изречения с честна, но мотивираща обобщена оценка, и ЕДНО единствено
                      най-важно следващо действие, което потребителят трябва да направи утре.

                    Форматирай с ясни markdown заглавия и bullet points където е подходящо.
                    Бъди максимално конкретен, цитирай цифрите навсякъде, където е relevant,
                    и никъде не изпадай в общи приказки, приложими за произволен бизнес.
                    """

                    response = client.chat.completions.create(
                        model="gpt-4o",
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
    st.caption("Нагласи слайдерите или въведи стойност на ръка, за да видиш минимума за оцеляване:")

    synced_metric(
        "fixed_costs",
        "💼 Месечни постоянни разходи<br><span class='bn-sublabel'>(наем, осигуровки)</span>",
        min_v=200, max_v=10000, step=100,
    )
    synced_metric(
        "price",
        "💰 Продажна цена за 1 бройка / час",
        min_v=0, max_v=500, step=1,
    )
    synced_metric(
        "cost",
        "📦 Себестойност на 1 бройка<br><span class='bn-sublabel'>(материали/доставка)</span>",
        min_v=0, max_v=300, step=1,
    )

    if st.session_state.price <= st.session_state.cost:
        st.error("🛑 Цената трябва да е по-висока от себестойността!")
    else:
        margin = st.session_state.price - st.session_state.cost
        be_units = math.ceil(st.session_state.fixed_costs / margin)
        min_turnover = be_units * st.session_state.price
        daily_sales = be_units / 30

        st.markdown("#### Резултат за твоя бизнес:")
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True, key="stat_sales"):
                st.markdown(
                    f'<div class="bn-stat-label">Нужни продажби</div>'
                    f'<div class="bn-stat-value">{be_units}</div>'
                    f'<div class="bn-stat-unit">бр./мес.</div>',
                    unsafe_allow_html=True,
                )
        with col2:
            with st.container(border=True, key="stat_turnover"):
                st.markdown(
                    f'<div class="bn-stat-label">Минимум оборот</div>'
                    f'<div class="bn-stat-value">{min_turnover}</div>'
                    f'<div class="bn-stat-unit">евро</div>',
                    unsafe_allow_html=True,
                )

        with st.container(border=True, key="tip_box"):
            st.markdown(
                f"💡 Това означава средно по **{daily_sales:.1f}** продажби на ден, за да излезеш на нула."
            )

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

                    dynamic_url = f"{STRIPE_LINK}?client_reference_id={client_ref}"

                    if use_test_mode:
                        st.caption("🧪 Тестов режим — картата 4242 4242 4242 4242 не таксува нищо реално.")

                    st.write("Нашият AI ще състави подробна пътна карта и чек-лист специално за тези стойности.")
                    st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 евро", dynamic_url, use_container_width=True)
                except Exception as e:
                    print(f"[OpenAI] Грешка при безплатен анализ: {e}")
                    st.error("⚠️ Възникна временен проблем. Моля, опитайте отново.")
