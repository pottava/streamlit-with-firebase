import streamlit as st

from libs import firebase

st.title("Streamlit & Firebase sample")
st.markdown("<style>#MainMenu {visibility: hidden;}</style>", unsafe_allow_html=True)


def signin():
    email = st.empty()
    email = email.text_input("Email アドレスを入力してください")
    password = st.text_input("パスワードを入力してください", type="password")
    submit = st.button("ログイン")
    if submit and firebase.authenticate(email, password):
        st.experimental_rerun()


def index():
    if not firebase.refresh():
        st.experimental_rerun()
        return
    st.text(firebase.user()["email"])


if "user" not in st.session_state:
    signin()
else:
    index()
