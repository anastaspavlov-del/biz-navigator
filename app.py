# ==========================================
# ТАБ 2: AI ВАЛИДАЦИЯ (МОДЕЛ С ПЛАЩАНЕ ЗА ДОКЛАД)
# ==========================================
with tab2:
    st.markdown("### 🤖 Запиши идеята си")
    st.write("Въведи твоя OpenAI API ключ в полето под настройките, за да активираш учения ментор:")
    
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
                        
                        # Промпт САМО за безплатната (кратка) част
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
                        
                        # Извеждане на безплатния анализ
                        st.markdown("---")
                        st.markdown("### 🔓 Твоят безплатен предварителен анализ:")
                        st.info(response.choices[0].message.content)
                        
                        # --- СЕКЦИЯ ЗА МОНЕТИЗАЦИЯ (ПЛАТЕНАТА КУКИЧКА) ---
                        st.markdown("### 📊 Отключи Пълния Експертен Доклад")
                        st.write("Нашият AI е подготвил подробен дигитален бизнес план специално за твоята ниша, който съдържа:")
                        st.markdown("""
                        * ⚠️ **3-те най-големи скрити риска** за този бизнес в България.
                        * 💸 **Списък с пропуснати разходи** (разрешителни, патенти, софтуер).
                        * 🎯 **MVP План стъпка по стъпка:** Как да тестваш пазара безплатно още тази седмица.
                        * 📈 **Маркетингова стратегия:** Откъде да намериш първите си 10 клиенти.
                        """)
                        
                        # Голям мобилен бутон за плащане
                        # ЗАМЕНЕТЕ долния линк с вашия реален линк за плащане от Stripe или ePay
                        stripe_link = "https://buy.stripe.com/your_custom_payment_link" 
                        st.link_button("💳 Отключи Пълния Бизнес Доклад за 4.99 лв.", stripe_link, use_container_width=True)
                        
                        st.caption("🔒 Сигурно плащане. Ще получиш доклада си веднага след трансакцията.")
                        
                    except Exception as e:
                        st.error(f"Грешка при връзката с AI: {e}")
            else:
                st.warning("⚠️ Моля, въведете текст или направете запис.")

