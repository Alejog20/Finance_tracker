import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simple Finance App", page_icon="💳", layout="wide")

def clean_numeric_value(value):
    """Limpia y convierte valores numéricos manteniendo el formato original"""
    try:
        # Si es None o NaN, retornamos None
        if pd.isna(value):
            return None
            
        # Si ya es número, convertimos a float
        if isinstance(value, (int, float)):
            return float(value)
        
        # Si es string, procesamos el formato
        if isinstance(value, str):
            # Removemos caracteres no numéricos excepto - , .
            cleaned = value.replace('$', '').strip()
            
            # Verificamos si tiene puntos como separadores de miles
            if '.' in cleaned and ',' not in cleaned:
                # Formato: 300.000.00
                cleaned = cleaned.replace('.', '')
            elif '.' in cleaned and ',' in cleaned:
                # Formato: 1.000,00
                cleaned = cleaned.replace('.', '').replace(',', '.')
            elif ',' in cleaned:
                # Formato: 1000,00
                cleaned = cleaned.replace(',', '.')
                
            return float(cleaned)
            
    except Exception as e:
        st.write(f"Error procesando valor: '{value}', Tipo: {type(value)}")
        return None

def load_transactions(file):
    try:
        # Leer el archivo
        df = pd.read_excel(file)
        
        # Convertir VALOR a string primero para asegurar consistencia
        df['VALOR'] = df['VALOR'].astype(str)
        
        # Limpiar y convertir valores
        df['VALOR_NUMERICO'] = df['VALOR'].apply(clean_numeric_value)
        
        # Crear columna DEBIT/CREDIT
        df['DEBIT/CREDIT'] = df['VALOR_NUMERICO'].apply(
            lambda x: 'DEBIT' if pd.notnull(x) and x < 0 else 'CREDIT'
        )
        
        # Formatear VALOR_NUMERICO para mostrar
        df['VALOR_NUMERICO'] = df['VALOR_NUMERICO'].apply(
            lambda x: f"{x:,.2f}" if pd.notnull(x) else None
        )
        
        # Mostrar DataFrame
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "VALOR": st.column_config.TextColumn(
                    "VALOR Original",
                    width="medium"
                ),
                "VALOR_NUMERICO": st.column_config.TextColumn(
                    "VALOR Procesado",
                    width="medium"
                ),
                "DEBIT/CREDIT": st.column_config.TextColumn(
                    width="small"
                )
            }
        )
        
        return df
        
    except Exception as e:
        st.error(f'Error en el procesamiento: {str(e)}')
        # Mostrar información de debugging
        if 'df' in locals():
            st.write("Tipos de datos en VALOR:", df['VALOR'].apply(type).value_counts())
        return None

def main():
    st.title("Simple Finance Dashboard")
    
    uploaded_file = st.file_uploader(
        "Upload your Excel file (.xlsx)",
        type=["xlsx"]
    )
    
    if uploaded_file is not None:
        df = load_transactions(uploaded_file)
        
        if df is not None:
            # Mostrar valores problemáticos si existen
            problematic = df[pd.isna(df['VALOR_NUMERICO'])]
            if not problematic.empty:
                st.warning("Valores que necesitan atención:")
                st.write(problematic[['FECHA', 'VALOR']])

if __name__ == "__main__":
    main()