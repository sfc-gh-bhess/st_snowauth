from urllib.parse import urlencode, quote
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

def show_auth_link(config, label):
    state_parameter = string_num_generator(15)
    qp_dict = {
        'redirect_uri': config['redirect_uri'], 
        'client_id': config['client_id'], 
        'response_type': 'code', 
        'state': state_parameter
    }
    if 'role' in config:
        qp_dict['scope'] = f"session:role-encoded:{quote(config['role'])}"
    query_params = urlencode(qp_dict)
    request_url = f"{config['authorization_endpoint']}?{query_params}"
    if len(st.query_params) > 0:
        qpcache = qparms_cache(state_parameter)
        qpcache.update(st.query_params.to_dict())
    st.markdown(f'<a href="{request_url}" target="_self">{label}</a>', unsafe_allow_html=True)
    st.stop()

def snowauth_session(config=None, label="Login to Snowflake"):
    if not config:
        config = _DEFAULT_SECKEY
    if isinstance(config, str):
        config = st.secrets[config]
    if _STKEY in st.session_state:
        session = st.session_state[_STKEY]
        if session._conn._conn.is_closed():
            logout()
    if _STKEY not in st.session_state:
        if not validate_config(config):
            st.error("Invalid OAuth Configuration")
            st.stop()
        if 'code' not in st.query_params:
            show_auth_link(config, label)
        code = st.query_params['code']
        state = st.query_params['state']
        st.query_params.clear()
        st.query_params.update(qparms_cache(state))
        qparms_cache(state).clear()
        theaders = {
                        'Authorization': 'Basic {}'.format(base64.b64encode('{}:{}'.format(config["client_id"], config["client_secret"]).encode()).decode()), 
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
            show_auth_link(config, label)
        token = ret.json()

        snow_configs = {
            'account': config['account'], 
            'authenticator': 'oauth',
            'token': token['access_token']
        }
        if 'connection' in config:
            snow_configs = {**config['connection'], **snow_configs}
        del token
        try:
            st.session_state[_STKEY] = Session.builder.configs(snow_configs).create()
        except Exception as e :
            st.error(f"Error connecting to Snowflake: \n{str(e)}")
            show_auth_link(config, label)


    session = st.session_state[_STKEY]
    st.sidebar.button("Logout", on_click=logout)
    return session