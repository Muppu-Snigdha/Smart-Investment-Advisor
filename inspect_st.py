import streamlit as st
print([a for a in dir(st) if 'set_query' in a.lower()])
print('query_params attr type:', type(st.query_params))
print('query_params value', st.query_params)
