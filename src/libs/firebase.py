import json

import pyrebase
import requests
import streamlit as st

from libs.config import firebase as cfg

firebase = pyrebase.initialize_app(cfg)
auth = firebase.auth()

# @see https://firebase.google.com/docs/reference/rest/auth


def authenticate(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.session_state.user = user  # with localId, email
        return True

    except requests.exceptions.HTTPError as e:
        msg = json.loads(e.args[1])["error"]["message"]
        if msg == "EMAIL_NOT_FOUND" or msg == "INVALID_PASSWORD":
            st.error("メールアドレスかパスワードに誤りがあります。")
        elif msg == "USER_DISABLED":
            st.error("このユーザーは無効化されています。管理者にお問い合わせください。")
        elif msg == "TOO_MANY_ATTEMPTS_TRY_LATER":
            st.error("試行回数が多すぎます。しばらく経ってからお試しください。")
        else:
            st.error("ログインに失敗しました。")

        if "user" in st.session_state:
            del st.session_state.user
    return False


def refresh():
    if "user" not in st.session_state:
        return False
    try:
        user = auth.refresh(st.session_state.user["refreshToken"])
        st.session_state.user = user  # with userId
        return True
    except:
        del st.session_state.user
    return False


def user():
    if "user" not in st.session_state:
        return None
    try:
        user = auth.get_account_info(st.session_state.user["idToken"])
    except:
        del st.session_state.user
    if "users" in user and len(user["users"]) > 0:
        return user["users"][0]
    return None
