import pandas as pd
import streamlit as st
from google.cloud import bigquery

from libs import firebase

st.title("Streamlit & Firebase sample")
hide_streamlit_menu = "<style>#MainMenu {visibility: hidden;}</style>"
st.markdown(hide_streamlit_menu, unsafe_allow_html=True)


@st.experimental_singleton()
def bq():
    client = bigquery.Client()
    return client


def signin():
    email = st.empty()
    email = email.text_input("Email アドレスを入力してください")
    password = st.text_input("パスワードを入力してください", type="password")
    submit = st.button("ログイン")
    if submit and firebase.authenticate(email, password):
        st.experimental_rerun()


@st.experimental_memo(ttl=60 * 10)
def query(sql) -> pd.DataFrame:
    return bq().query(sql).to_dataframe()


def index():
    if not firebase.refresh():
        st.experimental_rerun()
        return

    st.subheader("Open Source Insights")
    sql = """
    SELECT p.System, License, COUNT(DISTINCT p.Name) AS Packages
    FROM `bigquery-public-data.deps_dev_v1.PackageVersionsLatest` AS p,
         p.Licenses AS License
    GROUP BY System, License ORDER BY Packages DESC LIMIT 10
    """
    st.dataframe(query(sql))


if "user" not in st.session_state:
    signin()
else:
    index()
