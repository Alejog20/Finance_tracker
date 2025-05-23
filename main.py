import streamlit as st

st.set_page_config(
    page_title="Finance App - Bancolombia Statements", 
    page_icon="💳", 
    layout="wide"
)
from tracker import FinanceTracker
import pandas as pd
from visualizer import FinanceVisualizer
import logging
import os

class FinanceApp:
    """Aplicación principal que coordina el tracker y el visualizador"""
    
    def __init__(self):
        """Inicializa la aplicación"""
        self.tracker = FinanceTracker()
        self.visualizer = FinanceVisualizer()
    
    def render_dashboard_tab(self, df):
        """Renderiza la pestaña de dashboard con visualizaciones"""
        st.subheader("📈 Financial Overview")
        
        # Summary metrics
        self.visualizer.create_summary_metrics(df)
        
        st.divider()
        
        # Trends and category analysis
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container():
                self.visualizer.create_spending_trends(df)
        
        with col2:
            with st.container():
                self.visualizer.create_category_analysis(df)
        
        st.divider()
        
        # Additional visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Income vs Expenses")
            self.visualizer.create_income_vs_expenses_chart(df)
        
        with col2:
            st.subheader("🔥 Daily Spending Heatmap")
            self.visualizer.create_daily_spending_heatmap(df)
    
    def render_expenses_tab(self, debits_df):
        """Renderiza la pestaña de gastos"""
        st.subheader("💸 Expenses Analysis")
        
        if debits_df.empty:
            st.warning("No expense transactions found.")
            return
        
        # Category filter
        available_categories = debits_df['Category'].unique()
        selected_categories = st.multiselect(
            "Filter by Category",
            options=available_categories,
            default=available_categories,
            help="Select categories to filter the expense data"
        )
        
        filtered_debits = debits_df[debits_df['Category'].isin(selected_categories)] if selected_categories else debits_df
        
        # Display filtered data
        st.dataframe(filtered_debits, use_container_width=True)
        
        # Download button
        if not filtered_debits.empty:
            csv_data = filtered_debits.to_csv(index=False)
            st.download_button(
                label="💾 Download Expenses CSV",
                data=csv_data,
                file_name="expenses.csv",
                mime="text/csv",
                help="Download the filtered expense data as CSV"
            )
    
    def render_income_tab(self, credits_df):
        """Renderiza la pestaña de ingresos"""
        st.subheader("💰 Income Analysis")
        
        if credits_df.empty:
            st.warning("No income transactions found.")
            return
        
        st.dataframe(credits_df, use_container_width=True)
        
        # Download button
        csv_data = credits_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Income CSV",
            data=csv_data,
            file_name="income.csv",
            mime="text/csv",
            help="Download the income data as CSV"
        )
    
    def render_settings_tab(self):
        """Renderiza la pestaña de configuraciones"""
        st.subheader("⚙️ Category Management")
        
        st.info("💡 **Tip**: For best results, manage your categories directly in the `categories.json` file")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Quick Add Category**")
            new_category = st.text_input("Category Name")
            new_keywords = st.text_area("Keywords (one per line)")
            
            if st.button("➕ Add Category") and new_category and new_keywords:
                keywords_list = [kw.strip() for kw in new_keywords.split('\n') if kw.strip()]
                
                if self.tracker.add_category(new_category, keywords_list):
                    st.success(f"✅ Added category: {new_category}")
                    st.info("📝 Category saved to categories.json")
                    st.rerun()
                else:
                    st.warning("Category already exists!")
            
            st.write("**JSON File Management**")
            st.markdown("""
            **Recommended approach:**
            1. Edit `categories.json` directly in your text editor
            2. Use the JSON format shown in the Current Categories section
            3. Restart the app to load changes
            
            **Benefits:**
            - Faster bulk editing
            - Version control friendly
            - Easy backup/restore
            """)
        
        with col2:
            st.write("**Current Categories**")
            
            # Show total stats
            stats = self.tracker.get_categories_stats()
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Total Categories", stats["total_categories"])
            with col_b:
                st.metric("Total Keywords", stats["total_keywords"])
            
            # Show categories in expandable format
            for category, keywords in self.tracker.categories.items():
                with st.expander(f"📁 {category} ({len(keywords)} keywords)"):
                    if keywords:
                        st.write("**Keywords:**")
                        for kw in keywords:
                            st.write(f"• {kw}")
                    else:
                        st.write("_No keywords defined_")
            
            # Show JSON structure example
            with st.expander("📋 JSON Format Example"):
                st.code('''
{
  "Category Name": [
    "KEYWORD1",
    "KEYWORD2",
    "PARTIAL_MATCH"
  ],
  "Another Category": [
    "MORE_KEYWORDS"
  ]
}
                ''', language='json')
    
    def run(self):
        """Ejecuta la aplicación principal"""
        try:
            # Initialize categories
            categories = self.tracker.initialize_categories()
            
            # File uploader
            uploaded_file = st.file_uploader(
                'Upload your transaction Excel file', 
                type=["xlsx"],
                help="Make sure your file has columns: VALOR, DESCRIPCIÓN, and optionally FECHA for trend analysis"
            )
            
            if uploaded_file is not None:
                # Load and process transactions
                df = self.tracker.load_transactions(uploaded_file)
                
                if df is not None:
                    debits_df, credits_df = self.tracker.process_transactions(df)
                    
                    # Create tabs
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "📊 Dashboard", 
                        "💸 Expenses", 
                        "💰 Income", 
                        "⚙️ Settings"
                    ])
                    
                    with tab1:
                        self.render_dashboard_tab(df)
                    
                    with tab2:
                        self.render_expenses_tab(debits_df)
                    
                    with tab3:
                        self.render_income_tab(credits_df)
                    
                    with tab4:
                        self.render_settings_tab()
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Please check your file format and try again.")

def main():
    """Función principal de entrada"""
    app = FinanceApp()
    app.run()

if __name__ == "__main__":
    main()