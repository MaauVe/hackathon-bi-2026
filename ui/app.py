import streamlit as st
import pandas as pd

# título de la aplicación
st.title("Tablero de Inteligencia de Negocios")

# texto simple
st.write("¡El entorno de Streamlit está configurado y listo para el hackathon!")

# botón
if st.button("Haz clic para una sorpresa"):
    st.success("¡Todo funciona a la perfección, estás listo para empezar a diseñar!")