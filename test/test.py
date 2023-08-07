from pathlib import Path                # Needed
import sys                              # just
path_root = Path(__file__).parents[1]   # for
sys.path.append(str(path_root))         # tests

import streamlit as st
import pandas as pd
from st_snowauth import snowauth_session

st.markdown("## Snowflake OAuth")

session = snowauth_session()

st.markdown("### Who Am I?")
st.write(session.sql("SELECT current_user() AS user, current_role() AS role, current_database() AS database, current_schema() AS schema").collect())
st.markdown("### What Roles do I have?")
st.write(session.sql("SHOW GRANTS").collect())
st.markdown("### What Databases Are Here?")
st.dataframe(pd.DataFrame(session.sql('SHOW DATABASES').collect()))

st.markdown("Just something to show what happens when widgets are updated.")
x = st.slider("x")
st.metric("WOW", value=x)
