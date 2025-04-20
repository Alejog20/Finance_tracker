import streamlit as st
import pandas as pd
import numpy as np
import json 
import os
import logging
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(page_title="Simple Finance App", page_icon="💳", layout="wide")

def initialize_categories() -> Dict[str, List[str]]:
    """Inicializa y carga las categorías desde el archivo"""
    logger.debug("Starting categories initialization")
    category_file = "categories.json"
    default_categories = {"Uncategorized": []}
    
    if "categories" not in st.session_state:
        st.session_state.categories = default_categories
        
    if os.path.exists(category_file):
        try:
            with open(category_file, "r") as f:
                st.session_state.categories = json.load(f)
                logger.debug(f"Categories loaded: {st.session_state.categories}")
        except json.JSONDecodeError as e:
            logger.error(f"Error loading categories: {e}")
            st.error(f"Error loading categories: {e}")
            return default_categories
    
    return st.session_state.categories

def save_categories() -> None:
    """Guarda las categorías en el archivo"""
    try:
        with open("categories.json", "w") as f:
            json.dump(st.session_state.categories, f)
            logger.debug("Categories saved successfully")
    except Exception as e:
        logger.error(f"Error saving categories: {e}")
        st.error(f"Error saving categories: {e}")

def validate_dataframe(df: pd.DataFrame) -> bool:
    """Valida que el DataFrame tenga la estructura correcta"""
    required_columns = ['VALOR', 'DESCRIPCIÓN']
    
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            st.error(f"Missing required column: {col}")
            return False
            
    return True

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
        logger.error(f"Error processing value: '{value}', Type: {type(value)}, Error: {e}")
        return None

def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Categoriza las transacciones basándose en palabras clave"""
    logger.debug("Starting transaction categorization")
    df["Category"] = "Uncategorized"
    
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue
            
        # Convertir keywords a minúsculas una sola vez
        lowered_keywords = set(keyword.lower().strip() for keyword in keywords)
        
        # Usar vectorización en lugar de bucle
        mask = df["DESCRIPCIÓN"].str.lower().str.strip().isin(lowered_keywords)
        df.loc[mask, "Category"] = category
    
    return df

def load_transactions(file):
    """Carga y procesa el archivo de transacciones"""
    try:
        logger.debug("Starting file load")
        # Leer el archivo
        df = pd.read_excel(file)
        
        # Validar estructura del DataFrame
        if not validate_dataframe(df):
            return None
        
        # Convertir VALOR a string primero para asegurar consistencia
        df['VALOR'] = df['VALOR'].astype(str)
        logger.debug("Values converted to string")
        
        # Limpiar y convertir valores
        df['VALOR_NUMERICO'] = df['VALOR'].apply(clean_numeric_value)
        
        # Crear columna DEBIT/CREDIT
        df['DEBIT/CREDIT'] = df['VALOR_NUMERICO'].apply(
            lambda x: 'DEBIT' if pd.notnull(x) and x < 0 else 'CREDIT'
        )
        
        # Eliminar columna DCTO. si existe
        if 'DCTO.' in df.columns:
            df = df.drop('DCTO.', axis=1)
        
        # Formatear VALOR_NUMERICO para mostrar
        df['VALOR_NUMERICO'] = df['VALOR_NUMERICO'].apply(
            lambda x: f"{x:,.2f}" if pd.notnull(x) else None
        )
        
        logger.debug("File processed successfully")
        return df
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        st.error(f'Error processing file: {str(e)}')
        return None

def process_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Procesa y separa las transacciones en débitos y créditos"""
    try:
        logger.debug("Starting transaction processing")
        # Crear copias seguras
        debits_df = df[df['DEBIT/CREDIT'] == 'DEBIT'].copy()
        credits_df = df[df['DEBIT/CREDIT'] == 'CREDIT'].copy()
        
        # Verificar que la separación fue correcta
        total_rows = len(df)
        split_rows = len(debits_df) + len(credits_df)
        
        if total_rows != split_rows:
            logger.warning(f"Possible data loss: Total={total_rows}, Split={split_rows}")
            st.warning(f"Possible data loss: Total={total_rows}, Split={split_rows}")
            
        return debits_df, credits_df
        
    except Exception as e:
        logger.error(f"Error processing transactions: {e}")
        st.error(f"Error processing transactions: {e}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    st.title("Simple Finance Dashboard")
    
    try:
        # Inicializar categorías
        categories = initialize_categories()
        logger.debug(f"Categories initialized: {categories}")
        
        uploaded_file = st.file_uploader('Upload your transaction Excel file', type=["xlsx"])
        
        if uploaded_file is not None:
            df = load_transactions(uploaded_file)
            
            if df is not None:
                # Procesar transacciones
                debits_df, credits_df = process_transactions(df)
                
                # Crear tabs
                tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
                
                with tab1:
                    st.subheader("Debits Analysis")
                    new_category = st.text_input("New Category")
                    
                    if st.button("Add Category") and new_category:
                        if new_category not in categories:
                            categories[new_category] = []
                            save_categories()
                            st.success(f"Added category: {new_category}")
                            st.rerun()
                    
                    st.write(debits_df)
                    
                with tab2:
                    st.subheader("Credits Analysis")
                    st.write(credits_df)
    
    except Exception as e:
        logger.error(f"Main execution error: {e}")
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()