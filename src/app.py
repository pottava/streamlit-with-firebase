import os

import streamlit as st
from streamlit.components.v1 import html

from libs import common, firebase

common.init_page("ログイン")
st.title("Streamlit & Firebase sample")


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
    st.text("ログインしました。左のメニューから各機能を試せます。")


if "user" not in st.session_state:
    signin()
else:
    index()

rev = os.getenv("K_REVISION")
if rev:
    html(f'<script>console.log("Revision: {rev}");</script>', height=1)
