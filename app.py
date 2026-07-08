import streamlit as st
import math
from openai import OpenAI
import stripe
import urllib.parse
from docx import Document
from io import BytesIO
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(
    page_title="Бизнес Навигатор", 
    page_icon="🚀", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Histats брояч
st.markdown(
    '<a href="https://www.histats.com" target="_blank">'
    '<img src="https://sstatic1.histats.com/0.gif?5036919&101" alt="Histats" border="0" style="display:none;">'
    '</a>', 
    unsafe_allow_html=True
)

api_key = st.secrets.get("OPENAI_API_KEY", "")
stripe.api_key = st.secrets.get("STRIPE_API_KEY", "")

# 📥 УЛАВЯНЕ НА ДАННИТЕ ОТ URL
session_id = st.query_params.get("session_id")

# Базови стойности по подразбиране
if "fixed_costs" not in st.session_state: st.session_state.fixed_costs = 1200
if "price" not in st.session_state: st.session_state.price = 50
if "cost" not in st.session_state: st.session_state.cost = 20
if "idea_text" not in st.session_state: st.session_state.idea_text = ""

# 🌟 JS КОМПОНЕНТ ЗА СПАСЯВАНЕ НА ДАННИТЕ В БРАУЗЪРА (Local Storage)
# Този скрипт се изпълнява скрито. Ако няма session_id, той записва текущите данни от слайдерите в браузъра.
# Ако ИМА session_id (връщаме се от Stripe), той прочита записаните данни и пренасочва Streamlit да ги използва.
if not session_id:
    # Записваме текущите стойности, докато потребителят ги цъка
    js_save = f"""
    <script>
    localStorage.setItem('fc', '{st.session_state.fixed_costs}');
    localStorage.setItem('pr', '{st.session_state.price}');
    localStorage.setItem('cs', '{st.session_state.cost}');
    localStorage.setItem('idea', encodeURIComponent('{st.session_state.idea_text}'));
    </script>
    """
    components.html(js_save, height=0)
else:
    # Когато се върнем от Stripe, улавяме данните обратно през URL (ако сме успели да ги пратим) 
    # ИЛИ ако не са там, ще накараме JavaScript да презареди страницата веднъж с правилните параметри от LocalStorage.
    url_fin = st.query_params.get("fin", "")
    url_idea = st.query_params.get("idea", "")
    
    # Ако в URL липсват данните (защото Stripe ги счупи), ги взимаме от localStorage чрез JS пренасочване
    if not url_fin or "|" not in url_fin or "{CLIENT_" in url_fin:
        js_redirect = """
        <script>
        var fc = localStorage.getItem('fc') || '1200';
        var pr = localStorage.getItem('pr') || '50';
        var cs = localStorage.getItem('cs') || '20';
        var idea = localStorage.getItem('idea') || '';
        var currentUrl = window.location.href;
        
        // Почистваме счупените параметри и сглобяваме точния URL
        var url = new URL(currentUrl);
        url.searchParams.set('fin', fc + '|' + pr + '|' + cs);
        url.searchParams.set('idea', idea);
        
        // Пренасочваме към същия таб, но с поправени параметри в URL
        window.location.href = url.href;
        </script>
        """
        components.html(js_redirect, height=0)
        st.stop() # Спираме изпълнението, докато JS не презареди страницата с точния URL

    # Ако параметрите вече са успешно изтеглени от localStorage и наместени в URL:
    try:
        parts = url_fin.split("|")
        if len(parts) == 3:
            st.session_state.fixed_costs = int(float(parts[0]))
            st.session_state.price = int(float(parts[1]))
            st.session_state.cost = int(float(parts[2]))
        if url_idea:
            st.session_state.idea_text = urllib.parse.unquote(url_idea)
    except:
        pass
