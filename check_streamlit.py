import streamlit as st
print(st.__version__)
print([a for a in dir(st) if 'query' in a.lower()])
