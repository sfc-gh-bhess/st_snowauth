# Snowflake OAuth component for Streamlit

This Python package implements a "gate" for the Streamlit app
that will only allow the app to proceed once the user authenticates
via Snowflake OAuth.

Simply include the component at the top of the Streamlit app, such as
```
import streamlit as st
from st_snowauth import snowauth_session

st.markdown("## This (and above) is always seen")
session = snowauth_session()
st.markdown("## This (and below) is only seen after authentication")
```

The returned Snowpark session can be used as usual. It is a session
for whichever user was authenticated using Snowflake OAuth.

This component works with either local Snowflake users (username/password)
or SSO, if SAML integration with an SSO provider has been configured. 

NOTE: this will not work for users whose default role is `ACCOUNTADMIN`,
`SECURITYADMIN`, or `ORGADMIN`, in addition to any other roles specified 
in the `BLOCKED_ROLES_LIST` for your security integration.

The session is stored in Streamlit session state and is validated
on each re-run of the Streamlit. If the session is closed, it is cleared
from the session state and the user is prompted to reauthenticate. There
is also an option to logout (a logout button is placed in the sidebar).

## Installation 

You can install directly from github with this command:
```
pip install git+https://github.com/sfc-gh-bhess/st_snowauth.git
```
Note that python 3.8 is the only supported python version currently.

To install directly from github via pipenv, use:
```
pipenv install git+https://github.com/sfc-gh-bhess/st_snowauth.git#egg=st_snowauth
```

## Snowflake Setup
This component works with a Snowflake OAuth for Custom Clients security integration.
For more deatils, see the [Snowflake Documentation](https://docs.snowflake.com/en/user-guide/oauth-custom)

To set up the security integration you will execute a statement such as:
```
CREATE OR REPLACE SECURITY INTEGRATION oauth_st
  TYPE=OAUTH
  ENABLED=TRUE
  OAUTH_ALLOW_NON_TLS_REDIRECT_URI = TRUE
  OAUTH_CLIENT = CUSTOM
  OAUTH_CLIENT_TYPE='PUBLIC'
  OAUTH_REDIRECT_URI='http://localhost:8501'
  OAUTH_ISSUE_REFRESH_TOKENS = TRUE
  OAUTH_REFRESH_TOKEN_VALIDITY = 86400
;
```
The `OAUTH_REDIRECT_URI` should be the URL for your Streamlit app. You 
can customize other fields and integration name; this is just an example.

Once you have created the security integration, you will need to get the
client ID and secret. You can retrieve the client ID with the following SQL:
```
DESCRIBE INTEGRATION oauth_st;
```

You can retrieve the client secret with the following SQL:
```
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS( 'OAUTH_ST' );
```

## st_snowauth configuration
The `snowauth_session()` function takes 2 optional parameters: `config` and `label`.
The `label` is the text to use in the link presented to log in. By default, 
the label is `Login to Snowflake`.

The `snowauth_session()` function also needs a configuration dictionary to function.
The necessary fields of the function are:
* `account` - the Snowflake account identier
* `authorization_endpoint` - the URL to use to get an authorization code, typically `https://<ACCOUNTID>.snowflakecomputing.com/oauth/authorize`.
* `token_endpoint` - the URL to use to trade an authorization code for a token, typically `https://<ACCOUNTID>.snowflakecomputing.com/oauth/token-request`.
* `redirect_uri` - the URL that is configured in the OAuth provider as the redirect URL (it should be the URL of the Streamlit app itself)
* `client_id` - the client ID, from the commands above.
* `client_secret` - the client secret for the client ID, from the commands above

If `snowauth_session()` is called without a `config` parameter, it will look for the
configuration parameters in the secrets file (`st.secrets`) using the default 
name `snowauth`.
```
session = snowauth_session()
```

The `.streamlit/secrets.toml` file would look something like this:
```
[snowauth]
account = "<ACCOUNTID>"
authorization_endpoint = "https://<ACCOUNTID>.snowflakecomputing.com/oauth/authorize"
token_endpoint = "https://<ACCOUNTID>.snowflakecomputing.com/oauth/token-request"
redirect_uri = "<REDIRECT URI - this Streamlit's location>"
client_id = "<OAUTH CLIENT ID>"
client_secret = "<OAUTH CLIENT SECRET>"
```

If `snowauth_session()` is called with a string valued `config` parameter, 
it will look for the configuration parameters in the secrets file (`st.secrets`) 
using the supplied name.
```
session = snowauth_session('my_snowauth')
```

The `.streamlit/secrets.toml` file would look something like this:
```
[my_snowauth]
account = "<ACCOUNTID>"
...
```

If `snowauth_session()` is called with a dictionary for the `config` parameter,
it will use those as the parameter values.
```
snowauth_params = {'account': ...} # Or any way to create the dictionary
session = snowauth_session(snowauth_params)
```

### Multipage Streamlit Apps
This component supports multipage Streamlit apps. Just include
the call to `snowauth_session()` at the top of every page. If 
the user is not logged in, they will be presented with the login
link. Once authenticated, they will return to the main page of the
Streamlit app.

### Lower-level notes
If you do need to test to see if the session is already cached,
you can test it yourself directly:
```
if st_snowauth._STKEY in st.session_state:
    do_something()
```