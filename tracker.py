import pandas as pd
import numpy as np
import json 
import os
import logging
import streamlit as st
from typing import Dict, List, Optional

class FinanceTracker:
    """Clase principal para el seguimiento de finanzas personales"""
    
    def __init__(self):
        """Inicializa el tracker de finanzas"""
        self.logger = self._setup_logging()
        self.category_file = "categories.json"
        self.categories = {}
        self.df = None
        self.debits_df = None
        self.credits_df = None
        
    def _setup_logging(self) -> logging.Logger:
        """Configura el sistema de logging"""
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        return logger
    
    def initialize_categories(self) -> Dict[str, List[str]]:
        """Inicializa y carga las categorías desde el archivo JSON"""
        self.logger.debug("Starting categories initialization")
        
        fallback_categories = {"Uncategorized": []}
        
        if os.path.exists(self.category_file):
            try:
                with open(self.category_file, "r", encoding='utf-8') as f:
                    self.categories = json.load(f)
                    st.session_state.categories = self.categories
                    self.logger.debug(f"Categories loaded from JSON: {len(self.categories)} categories")
                    return self.categories
            except json.JSONDecodeError as e:
                self.logger.error(f"Error loading categories: {e}")
                st.error(f"❌ Error loading categories.json: {e}")
                st.info("💡 Please check your categories.json file format")
                return fallback_categories
            except Exception as e:
                self.logger.error(f"Unexpected error loading categories: {e}")
                st.error(f"❌ Error reading categories.json: {e}")
                return fallback_categories
        else:
            st.warning("📄 categories.json file not found. Please create it to enable smart categorization.")
            st.info("💡 Check the documentation for the expected JSON format")
            self.categories = fallback_categories
            return fallback_categories
        

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
        self.logger.debug("Limpiando valores numericos")
        
        try:
            # Si es None o NaN, retornamos None
            if pd.isna(value):
                return None
                
            # Si ya es número, convertimos a float
            if isinstance(value, (int, float)):
                return float(value)
            
            # Si es string, procesamos el formato
            if isinstance(value, str):
                cleaned = value.replace('$', '').strip()
                if '.' in cleaned and ',' not in cleaned:
                    cleaned = cleaned.replace('.', '')
                elif '.' in cleaned and ',' in cleaned:
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                elif ',' in cleaned:
                    cleaned = cleaned.replace(',', '.')
                    
                return float(cleaned)
                
        except Exception as e:
            logger.error(f"Error processing value: '{value}', Type: {type(value)}, Error: {e}")
            return None

    def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
        """Categoriza las transacciones basándose en palabras clave"""
        self.logger.debug("Starting transaction categorization")
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
        

    def add_category(self, new_category: str, keywords: List[str] = None) -> bool:
        """Añade una nueva categoría"""
        if new_category in self.categories:
            return False
        
        self.categories[new_category] = keywords or []
        self.save_categories()
        return True
    
    def get_categories_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de las categorías"""
        return {
            "total_categories": len(self.categories),
            "total_keywords": sum(len(keywords) for keywords in self.categories.values())
        }
    