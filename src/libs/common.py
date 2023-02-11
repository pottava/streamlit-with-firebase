import streamlit as st


def init_page(title):
    st.set_page_config(
        page_icon="🐳",
        page_title=f"{title} | Streamlit App"
    )
    st.markdown(
        """
        <style>
            #MainMenu {visibility: hidden; }
            footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )
