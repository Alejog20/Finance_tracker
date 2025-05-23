import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import logging

class FinanceVisualizer:
    """Clase encargada de crear visualizaciones para el análisis"""
    
    def __init__(self):
        """Inicializa el visualizador de finanzas"""
        self.logger = logging.getLogger(__name__)
    
    def create_spending_trends(self, df: pd.DataFrame) -> None:
        """Crea gráficos de tendencias de gastos mensuales y semanales"""
        if 'FECHA' not in df.columns:
            st.warning("No date column found. Please ensure your Excel file has a 'FECHA' column for trend analysis.")
            return
        
        # Filter only expenses (negative values)
        expenses_df = df[df['DEBIT/CREDIT'] == 'DEBIT'].copy()
        
        if expenses_df.empty:
            st.warning("No expense data found for trend analysis.")
            return
        
        # Convert VALOR_NUMERICO back to float for calculations
        expenses_df['Amount'] = expenses_df['VALOR_NUMERICO'].str.replace(',', '').astype(float).abs()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Monthly Spending Trends")
            self._create_monthly_trend_chart(expenses_df)
        
        with col2:
            st.subheader("📈 Weekly Spending Trends")
            self._create_weekly_trend_chart(expenses_df)
    
    def _create_monthly_trend_chart(self, expenses_df: pd.DataFrame) -> None:
        """Crea el gráfico de tendencias mensuales"""
        monthly_spending = expenses_df.groupby('Month_Year')['Amount'].sum().reset_index()
        monthly_spending['Month_Year_Str'] = monthly_spending['Month_Year'].astype(str)
        
        fig_monthly = px.line(
            monthly_spending, 
            x='Month_Year_Str', 
            y='Amount',
            title='Monthly Spending Over Time',
            markers=True
        )
        fig_monthly.update_layout(
            xaxis_title="Month",
            yaxis_title="Total Spending",
            showlegend=False
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    def _create_weekly_trend_chart(self, expenses_df: pd.DataFrame) -> None:
        """Crea el gráfico de tendencias semanales"""
        weekly_spending = expenses_df.groupby('Week_Year')['Amount'].sum().reset_index()
        weekly_spending = weekly_spending.tail(12)  # Last 12 weeks
        weekly_spending['Week_Year_Str'] = weekly_spending['Week_Year'].astype(str)
        
        fig_weekly = px.bar(
            weekly_spending, 
            x='Week_Year_Str', 
            y='Amount',
            title='Weekly Spending (Last 12 Weeks)'
        )
        fig_weekly.update_layout(
            xaxis_title="Week",
            yaxis_title="Total Spending",
            showlegend=False
        )
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    def create_category_analysis(self, df: pd.DataFrame) -> None:
        """Crea análisis visual por categorías"""
        expenses_df = df[df['DEBIT/CREDIT'] == 'DEBIT'].copy()
        
        if expenses_df.empty:
            st.warning("No expense data found for category analysis.")
            return
        
        expenses_df['Amount'] = expenses_df['VALOR_NUMERICO'].str.replace(',', '').astype(float).abs()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Spending by Category")
            self._create_category_pie_chart(expenses_df)
        
        with col2:
            st.subheader("💰 Top Categories")
            self._create_top_categories_metrics(expenses_df)
    
    def _create_category_pie_chart(self, expenses_df: pd.DataFrame) -> None:
        """Crea el gráfico de pastel por categorías"""
        category_spending = expenses_df.groupby('Category')['Amount'].sum().reset_index()
        category_spending = category_spending.sort_values('Amount', ascending=False)
        
        fig_pie = px.pie(
            category_spending, 
            values='Amount', 
            names='Category',
            title='Spending Distribution by Category'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    def _create_top_categories_metrics(self, expenses_df: pd.DataFrame) -> None:
        """Crea métricas de las categorías principales"""
        category_spending = expenses_df.groupby('Category')['Amount'].sum().reset_index()
        category_spending = category_spending.sort_values('Amount', ascending=False)
        
        # Display top 5 categories as metrics
        for idx, row in category_spending.head(5).iterrows():
            st.metric(
                label=row['Category'],
                value=f"${row['Amount']:,.2f}"
            )
    
    def create_income_vs_expenses_chart(self, df: pd.DataFrame) -> None:
        """Crea un gráfico comparativo de ingresos vs gastos"""
        if 'FECHA' not in df.columns:
            st.warning("No date column found for income vs expenses comparison.")
            return
        
        # Separate expenses and income
        expenses_df = df[df['DEBIT/CREDIT'] == 'DEBIT'].copy()
        income_df = df[df['DEBIT/CREDIT'] == 'CREDIT'].copy()
        
        if expenses_df.empty and income_df.empty:
            st.warning("No data found for income vs expenses analysis.")
            return
        
        # Process expenses
        if not expenses_df.empty:
            expenses_df['Amount'] = expenses_df['VALOR_NUMERICO'].str.replace(',', '').astype(float).abs()
            monthly_expenses = expenses_df.groupby('Month_Year')['Amount'].sum().reset_index()
            monthly_expenses['Type'] = 'Expenses'
        else:
            monthly_expenses = pd.DataFrame(columns=['Month_Year', 'Amount', 'Type'])
        
        # Process income
        if not income_df.empty:
            income_df['Amount'] = income_df['VALOR_NUMERICO'].str.replace(',', '').astype(float)
            monthly_income = income_df.groupby('Month_Year')['Amount'].sum().reset_index()
            monthly_income['Type'] = 'Income'
        else:
            monthly_income = pd.DataFrame(columns=['Month_Year', 'Amount', 'Type'])
        
        # Combine data
        combined_data = pd.concat([monthly_expenses, monthly_income], ignore_index=True)
        
        if combined_data.empty:
            st.warning("No data to display for income vs expenses.")
            return
        
        combined_data['Month_Year_Str'] = combined_data['Month_Year'].astype(str)
        
        fig = px.bar(
            combined_data,
            x='Month_Year_Str',
            y='Amount',
            color='Type',
            barmode='group',
            title='Monthly Income vs Expenses',
            labels={'Month_Year_Str': 'Month', 'Amount': 'Amount ($)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_daily_spending_heatmap(self, df: pd.DataFrame) -> None:
        """Crea un mapa de calor de gastos diarios"""
        if 'FECHA' not in df.columns:
            st.warning("No date column found for daily spending heatmap.")
            return
        
        expenses_df = df[df['DEBIT/CREDIT'] == 'DEBIT'].copy()
        
        if expenses_df.empty:
            st.warning("No expense data found for daily spending analysis.")
            return
        
        expenses_df['Amount'] = expenses_df['VALOR_NUMERICO'].str.replace(',', '').astype(float).abs()
        expenses_df['Day'] = expenses_df['FECHA'].dt.day
        expenses_df['Month'] = expenses_df['FECHA'].dt.month
        
        # Group by day and month
        daily_spending = expenses_df.groupby(['Month', 'Day'])['Amount'].sum().reset_index()
        
        # Create pivot table for heatmap
        heatmap_data = daily_spending.pivot(index='Month', columns='Day', values='Amount')
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='Reds',
            showscale=True
        ))
        
        fig.update_layout(
            title='Daily Spending Heatmap',
            xaxis_title='Day of Month',
            yaxis_title='Month'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_summary_metrics(self, df: pd.DataFrame) -> None:
        """Crea métricas de resumen financiero"""
        if df.empty:
            st.warning("No data available for summary metrics.")
            return
        
        # Separate expenses and income
        expenses_df = df[df['DEBIT/CREDIT'] == 'DEBIT'].copy()
        income_df = df[df['DEBIT/CREDIT'] == 'CREDIT'].copy()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_transactions = len(df)
            st.metric("Total Transactions", total_transactions)
        
        with col2:
            expense_transactions = len(expenses_df)
            st.metric("Expense Transactions", expense_transactions)
        
        with col3:
            income_transactions = len(income_df)
            st.metric("Income Transactions", income_transactions)
        
        with col4:
            if not expenses_df.empty:
                expenses_df['Amount'] = expenses_df['VALOR_NUMERICO'].str.replace(',', '').astype(float).abs()
                avg_expense = expenses_df['Amount'].mean()
                st.metric("Average Expense", f"${avg_expense:,.2f}")
            else:
                st.metric("Average Expense", "$0.00")