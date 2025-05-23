import streamlit as st
# MUST be the first Streamlit command
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide"
)
# Now import other modules
import pandas as pd
from tracker import FinanceTracker
from visualizer import FinanceVisualizer
import logging
import os
import tempfile
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_settings_tab(tracker):
    """Renderiza la pestaña de configuraciones"""
    st.subheader("⚙️ Category Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Add New Category")
        new_category = st.text_input("Category Name")
        keywords = st.text_area("Keywords (one per line)")
        
        if st.button("Add Category"):
            if new_category and keywords:
                keywords_list = [k.strip() for k in keywords.split('\n') if k.strip()]
                if tracker.add_category(new_category, keywords_list):
                    st.success(f"✅ Category '{new_category}' added successfully!")
                    st.rerun()
                else:
                    st.warning("Category already exists!")
            else:
                st.warning("Please enter both category name and keywords")
    
    with col2:
        st.write("### Current Categories")
        stats = tracker.get_categories_stats()
        st.metric("Total Categories", stats["total_categories"])
        st.metric("Total Keywords", stats["total_keywords"])
        
        # Show categories
        for category, keywords in tracker.categories.items():
            with st.expander(f"{category} ({len(keywords)} keywords)"):
                if keywords:
                    for kw in keywords:
                        st.write(f"• {kw}")
                else:
                    st.write("_No keywords defined_")

def render_dashboard(visualizer, df):
    """Renderiza el dashboard principal"""
    st.subheader("📊 Financial Dashboard")
    
    # Summary metrics
    visualizer.create_summary_metrics(df)
    
    st.divider()
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        visualizer.create_spending_trends(df)
    
    with col2:
        visualizer.create_category_analysis(df)
    
    st.divider()
    
    # Additional charts
    col1, col2 = st.columns(2)
    
    with col1:
        visualizer.create_income_vs_expenses_chart(df)
    
    with col2:
        visualizer.create_daily_spending_heatmap(df)

def main():
    """Main application entry point"""
    st.title("💳 Personal Finance Tracker")
    st.markdown("Upload your Bancolombia bank statement to analyze your finances")
    
    # Initialize tracker and visualizer
    tracker = FinanceTracker()
    visualizer = FinanceVisualizer()
    
    # Initialize categories
    categories = tracker.initialize_categories()
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Upload File")
        uploaded_file = st.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            help="Upload your Bancolombia bank statement in Excel format"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.info(f"Size: {uploaded_file.size / 1024:.2f} KB")
    
    # Main content
    if uploaded_file is None:
        # Show welcome message
        st.info("👈 Please upload your bank statement Excel file to begin")
        
        # Show instructions
        with st.expander("📋 Instructions"):
            st.markdown("""
            1. **Export your bank statement** from Bancolombia in Excel format
            2. **Upload the file** using the sidebar
            3. **Explore your finances** through the different tabs
            
            The file should contain at least these columns:
            - `VALOR`: Transaction amount
            - `DESCRIPCIÓN`: Transaction description
            - `FECHA` (optional): Transaction date for trend analysis
            """)
    else:
        # Process uploaded file
        temp_file = None
        try:
            # Create a temporary file with a unique name
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
                temp_file = tmp_file.name
                tmp_file.write(uploaded_file.getbuffer())
            
            # Process the file
            with st.spinner("Processing file..."):
                result = tracker.load_transactions(temp_file)
            
            if result['success']:
                st.success(f"✅ {result['message']}")
                
                # Show processing summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Transactions", result['data']['total'])
                with col2:
                    st.metric("Expenses", result['data']['debits'])
                with col3:
                    st.metric("Income", result['data']['credits'])
                
                # Get processed data
                df, debits_df, credits_df = tracker.get_processed_data()
                
                # Create tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Dashboard", 
                    "💸 Expenses", 
                    "💰 Income", 
                    "⚙️ Settings"
                ])
                
                with tab1:
                    render_dashboard(visualizer, df)
                
                with tab2:
                    st.subheader("💸 Expense Transactions")
                    if not debits_df.empty:
                        # Category filter
                        categories = debits_df['Category'].unique()
                        selected_cats = st.multiselect(
                            "Filter by category",
                            options=categories,
                            default=categories
                        )
                        
                        # Filter data
                        filtered_df = debits_df[debits_df['Category'].isin(selected_cats)]
                        
                        # Show data
                        st.dataframe(filtered_df, use_container_width=True)
                        
                        # Download button
                        csv = filtered_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Expenses CSV",
                            csv,
                            "expenses.csv",
                            "text/csv"
                        )
                    else:
                        st.info("No expense transactions found")
                
                with tab3:
                    st.subheader("💰 Income Transactions")
                    if not credits_df.empty:
                        st.dataframe(credits_df, use_container_width=True)
                        
                        # Download button
                        csv = credits_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Income CSV",
                            csv,
                            "income.csv",
                            "text/csv"
                        )
                    else:
                        st.info("No income transactions found")
                
                with tab4:
                    render_settings_tab(tracker)
            else:
                st.error(f"❌ {result['message']}")
                    
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please check your file format and try again.")
            logger.error(f"Error in main: {e}", exc_info=True)
            
        finally:
            # Always try to clean up the temp file
            if temp_file:
                try:
                    # Add a small delay to ensure file is closed
                    time.sleep(0.1)
                    
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        logger.debug(f"Temp file removed: {temp_file}")
                except PermissionError:
                    # If we can't delete it, try using a different approach
                    try:
                        import gc
                        gc.collect()  # Force garbage collection
                        time.sleep(0.2)
                        os.remove(temp_file)
                    except:
                        # If still can't delete, just log it
                        logger.warning(f"Could not remove temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Error removing temp file: {e}")

if __name__ == "__main__":
    main()