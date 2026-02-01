import streamlit as st


def local_css():
    # Load external CSS
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Inject Javascript for menu interactivity
    st.markdown(
        """
        <script>
        function updateMenuButtons() {
            let currentMenu = '"""
        + st.session_state.current_menu
        + """';
            
            const buttonMap = {
                'Dashboard': 'Dashboard',
                'Log a Mistake': 'Log Error',
                'IA Coach': 'Coach AI',
                'History': 'History'
            };
            
            const buttons = document.querySelectorAll('.menu-button');
            buttons.forEach(button => {
                const span = button.querySelector('span');
                const indicator = button.querySelector('.indicator');
                
                if (!span) return;
                
                const text = span.innerText.trim();
                let isActive = false;
                
                for (let btnText in buttonMap) {
                    if (text === btnText && buttonMap[btnText] === currentMenu) {
                        isActive = true;
                        break;
                    }
                }
                
                if (isActive) {
                    button.classList.add('active');
                    button.style.background = '#eeeeeeff';
                    span.style.color = '#1a1a1a';
                    button.querySelector('svg').style.color = '#6366f1';
                    indicator.style.opacity = '1';
                } else {
                    button.classList.remove('active');
                    button.style.background = 'transparent';
                    span.style.color = '#9ca3af';
                    button.querySelector('svg').style.color = '#9ca3af';
                    indicator.style.opacity = '0';
                }
            });
        }

        document.addEventListener('DOMContentLoaded', updateMenuButtons);
        window.addEventListener('load', updateMenuButtons);

        </script>
        """,
        unsafe_allow_html=True,
    )
