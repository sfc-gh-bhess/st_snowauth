from pathlib import Path                # Needed
import sys                              # just
path_root = Path(__file__).parents[1]   # for
sys.path.append(str(path_root))         # tests

import streamlit as st
from st_snowauth import snowauth_session

st.markdown("## Hello there")

session = snowauth_session()

st.markdown("## Welcome")
st.json(st.session_state)
