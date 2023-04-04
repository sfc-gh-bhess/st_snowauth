from urllib.parse import urlencode
import requests
import base64
import streamlit as st
from snowflake.snowpark import Session

import string
import random

_STKEY = 'SNOW_SESSION'
_DEFAULT_SECKEY = 'snowauth'

@st.cache_resource(ttl=300)
def qparms_cache(key):
    return {}

def logout():
    if _STKEY in st.session_state:
        st.session_state[_STKEY].close()
        del st.session_state[_STKEY]

def string_num_generator(size):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))

def validate_config(config):
    required_config_options = [ 'authorization_endpoint', 
                                'token_endpoint', 
                                'redirect_uri', 
                                'client_id', 
                                'client_secret', 
                                'account' ]
    return all([k in config for k in required_config_options])

def show_auth_link(config):
    state_parameter = string_num_generator(15)
    query_params = urlencode({'redirect_uri': config['redirect_uri'], 'client_id': config['client_id'], 'response_type': 'code', 'state': state_parameter})
    request_url = f"{config['authorization_endpoint']}?{query_params}"
    if st.experimental_get_query_params():
        qpcache = qparms_cache(state_parameter)
        qpcache = st.experimental_get_query_params()
    st.markdown(f'<a href="{request_url}" target="_self">Login to Snowflake</a>', unsafe_allow_html=True)
    st.stop()

def snowauth_session(config=None):
    if not config:
        config = _DEFAULT_SECKEY
    if isinstance(config, str):
        config = st.secrets[config]
    if _STKEY in st.session_state:
        session = st.session_state[_STKEY]
        if session._conn._conn.is_closed():
            logout()
    if _STKEY not in st.session_state:
        if 'code' not in st.experimental_get_query_params():
            show_auth_link(config)
        code = st.experimental_get_query_params()['code'][0]
        state = st.experimental_get_query_params()['state'][0]
        qpcache = qparms_cache(state)
        qparms = qpcache
        qpcache = {}

        theaders = {
                        'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(config["client_id"], config["secret"]).encode()).decode()), 
                        'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
                    }
        tdata = {
                    'grant_type': 'authorization_code', 
                    'code': code, 
                    'redirect_uri': config['redirect_uri']
                }
        try:
            ret = requests.post(config["token_endpoint"], 
                                headers=theaders,
                                data=urlencode(tdata).encode("utf-8")
                            )
            ret.raise_for_status()
        except requests.exceptions.RequestException as e:
            st.error(e)
            show_auth_link(config)
        token = ret.json()
        st.experimental_set_query_params(**qparms)
        snow_configs = {
            'account': config['account'], 
            'authenticator': 'oauth',
            'token': token['access_token']
        }
        del token
        try:
            st.session_state[_STKEY] = Session.builder.configs(snow_configs).create()
        except Exception as e :
            st.error(f"Error connecting to Snowflake: \n{str(e)}")
            show_auth_link(config)


    session = st.session_state[_STKEY]
    st.sidebar.button("Logout", on_click=logout)
    return session