from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

import streamlit as st
import pandas as pd
from st_snowauth import snowauth_session

st.markdown("## Snowflake OAuth")

session = snowauth_session()

st.markdown("### Who Am I?")
st.write(session.sql("SELECT current_user() AS user, current_role() AS role").collect())
st.markdown("### What Databases Are Here?")
st.dataframe(pd.DataFrame(session.sql('SHOW DATABASES').collect()))

st.markdown("Just something to show what happens when widgets are updated.")
x = st.slider("x")
st.metric("WOW", value=x)