import pandas as pd
import numpy as np
import json 
import os
import locale
import logging
import streamlit as st
from typing import Dict, List, Optional, Tuple

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
        

    def save_categories(self) -> None:
        """Guarda las categorías en el archivo"""
        try:
            with open("categories.json", "w", encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)
                self.logger.debug("Categories saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving categories: {e}")
            st.error(f"Error saving categories: {e}")

    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Valida que el DataFrame tenga la estructura correcta"""
        required_columns = ['VALOR', 'DESCRIPCIÓN']
        
        for col in required_columns:
            if col not in df.columns:
                self.logger.error(f"Missing required column: {col}")
                st.error(f"Missing required column: {col}")
                return False
                
        return True

    def clean_numeric_value(self, value):
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
            self.logger.error(f"Error processing value: '{value}', Type: {type(value)}, Error: {e}")
            return None

    def categorize_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categoriza las transacciones basándose en palabras clave"""
        self.logger.debug("Starting transaction categorization")
        df["Category"] = "Uncategorized"
        
        for category, keywords in self.categories.items():
            if category == "Uncategorized" or not keywords:
                continue
                
            # Convertir keywords a minúsculas una sola vez
            lowered_keywords = set(keyword.lower().strip() for keyword in keywords)
            
            # Usar vectorización en lugar de bucle
            mask = df["DESCRIPCIÓN"].str.lower().str.strip().isin(lowered_keywords)
            df.loc[mask, "Category"] = category
        
        return df

    def load_transactions(self, file_path: str) -> Dict[str, any]:
        """Carga y procesa el archivo de transacciones"""
        try:
            self.logger.debug(f"Starting file load from: {file_path}")
            
            # Leer el archivo usando context manager para asegurar que se cierre
            with pd.ExcelFile(file_path) as excel_file:
                df = pd.read_excel(excel_file)
            
            self.logger.debug(f"File loaded successfully. Shape: {df.shape}")
            
            # Validar estructura del DataFrame
            if not self.validate_dataframe(df):
                return {
                    'success': False,
                    'message': 'Invalid file structure. Missing required columns.'
                }
            
            # Convertir VALOR a string primero para asegurar consistencia
            df['VALOR'] = df['VALOR'].astype(str)
            self.logger.debug("Values converted to string")
            
            # Limpiar y convertir valores
            df['VALOR_NUMERICO'] = df['VALOR'].apply(self.clean_numeric_value)
            
            # Crear columna DEBIT/CREDIT
            df['DEBIT/CREDIT'] = df['VALOR_NUMERICO'].apply(
                lambda x: 'DEBIT' if pd.notnull(x) and x < 0 else 'CREDIT'
            )
            
            # Eliminar columna DCTO. si existe
            if 'DCTO.' in df.columns:
                df = df.drop('DCTO.', axis=1)
            
            # Categorizar transacciones
            df = self.categorize_transactions(df)
            
            # Procesar fechas si existe la columna
            if 'FECHA' in df.columns:
                df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
                df['Month_Year'] = df['FECHA'].dt.to_period('M')
                df['Week_Year'] = df['FECHA'].dt.to_period('W')
            
            # Crear una copia del DataFrame antes de formatear para mantener valores numéricos
            df_numeric = df.copy()
            
            # Formatear VALOR_NUMERICO para mostrar
            locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')
            df['VALOR_NUMERICO'] = df['VALOR_NUMERICO'].apply(lambda x: locale.currency(x, grouping=True) if pd.notnull(x) else None
)
            
            # Guardar el DataFrame procesado (con valores formateados)
            self.df = df
            
            # Procesar transacciones (separar débitos y créditos) usando datos numéricos
            self.debits_df, self.credits_df = self.process_transactions(df_numeric)
            
            # Formatear también los DataFrames de débitos y créditos
            if not self.debits_df.empty:
                self.debits_df = self.debits_df.copy()
                self.debits_df['VALOR_NUMERICO'] = self.debits_df['VALOR_NUMERICO'].apply(
                    lambda x: f"{x:,.2f}" if pd.notnull(x) else None
                )
            
            if not self.credits_df.empty:
                self.credits_df = self.credits_df.copy()
                self.credits_df['VALOR_NUMERICO'] = self.credits_df['VALOR_NUMERICO'].apply(
                    lambda x: f"{x:,.2f}" if pd.notnull(x) else None
                )
            
            self.logger.debug("File processed successfully")
            return {
                'success': True,
                'message': f'Successfully loaded {len(df)} transactions',
                'data': {
                    'total': len(df),
                    'debits': len(self.debits_df) if not self.debits_df.empty else 0,
                    'credits': len(self.credits_df) if not self.credits_df.empty else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            return {
                'success': False,
                'message': f'Error processing file: {str(e)}'
            }
        
        
    def process_transactions(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Procesa y separa las transacciones en débitos y créditos"""
        try:
            self.logger.debug("Starting transaction processing")
            # Copias seguras
            debits_df = df[df['DEBIT/CREDIT'] == 'DEBIT'].copy()
            credits_df = df[df['DEBIT/CREDIT'] == 'CREDIT'].copy()
            
            # Verificar que la separación fue correcta
            total_rows = len(df)
            split_rows = len(debits_df) + len(credits_df)
            
            if total_rows != split_rows:
                self.logger.warning(f"Possible data loss: Total={total_rows}, Split={split_rows}")
                st.warning(f"Possible data loss: Total={total_rows}, Split={split_rows}")
                
            return debits_df, credits_df
            
        except Exception as e:
            self.logger.error(f"Error processing transactions: {e}")
            st.error(f"Error processing transactions: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def get_processed_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Retorna los DataFrames procesados"""
        if self.df is None:
            raise ValueError("No data has been processed yet. Please load transactions first.")
        
        return self.df, self.debits_df, self.credits_df

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