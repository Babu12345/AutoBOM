import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from modules.csv_handler import CSVHandler
from modules.ai_optimizer import AIOptimizer
from modules.bom_validator import BOMValidator
from modules.ui_components import UIComponents

load_dotenv()

st.set_page_config(
    page_title="AI BOM Optimizer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    if 'csv_handler' not in st.session_state:
        st.session_state.csv_handler = CSVHandler()
    if 'ai_optimizer' not in st.session_state:
        st.session_state.ai_optimizer = AIOptimizer()
    if 'validator' not in st.session_state:
        st.session_state.validator = BOMValidator()
    if 'current_df' not in st.session_state:
        st.session_state.current_df = pd.DataFrame()
    if 'file_uploaded' not in st.session_state:
        st.session_state.file_uploaded = False
    if 'columns_mapped' not in st.session_state:
        st.session_state.columns_mapped = False

def upload_and_process_page():
    st.title("🤖 AI BOM Optimizer")
    st.subheader("Upload & Process Your Bill of Materials")

    api_configured = UIComponents.render_api_key_input()

    uploaded_file = UIComponents.render_file_upload()

    if uploaded_file and not st.session_state.file_uploaded:
        with st.spinner("Loading file..."):
            if st.session_state.csv_handler.load_file(uploaded_file):
                st.session_state.file_uploaded = True
                st.success("✅ File loaded successfully!")
                st.rerun()

    if st.session_state.file_uploaded and not st.session_state.columns_mapped:
        st.markdown("---")
        original_columns = st.session_state.csv_handler.original_columns

        suggestions = st.session_state.csv_handler.get_column_mapping_suggestions()
        st.info(f"💡 Found {len(suggestions)} automatic column mappings")

        column_mapping = UIComponents.render_column_mapping(original_columns)

        if st.button("🔗 Apply Column Mapping"):
            if column_mapping:
                with st.spinner("Applying column mapping..."):
                    if st.session_state.csv_handler.apply_column_mapping(column_mapping):
                        st.session_state.columns_mapped = True
                        st.session_state.current_df = st.session_state.csv_handler.get_dataframe()
                        st.success("✅ Column mapping applied successfully!")
                        st.rerun()
            else:
                st.warning("Please map at least the required columns")

    if st.session_state.columns_mapped:
        st.markdown("---")
        st.subheader("📊 Data Validation")

        validation_results = st.session_state.validator.validate_dataframe(st.session_state.current_df)
        UIComponents.render_validation_results(validation_results)

        missing_summary = st.session_state.csv_handler.get_missing_data_summary()
        UIComponents.render_missing_data_summary(missing_summary)

        if api_configured and st.button("🚀 Start AI Optimization", type="primary"):
            st.session_state.page = "AI Optimization"
            st.rerun()

def review_and_edit_page():
    st.title("✏️ Review & Edit BOM Data")

    if st.session_state.current_df.empty:
        st.warning("No data loaded. Please upload and process a file first.")
        return

    edited_df = UIComponents.render_data_editor(st.session_state.current_df)

    if not edited_df.equals(st.session_state.current_df):
        st.session_state.current_df = edited_df
        st.success("✅ Changes saved!")

    if st.button("🔄 Recalculate Total Costs"):
        with st.spinner("Calculating costs..."):
            st.session_state.csv_handler.df = st.session_state.current_df
            if st.session_state.csv_handler.calculate_total_costs():
                st.session_state.current_df = st.session_state.csv_handler.get_dataframe()
                st.success("✅ Total costs recalculated!")
                st.rerun()

def ai_optimization_page():
    st.title("🤖 AI-Powered BOM Optimization")

    if st.session_state.current_df.empty:
        st.warning("No data loaded. Please upload and process a file first.")
        return

    if not st.session_state.ai_optimizer.is_api_configured():
        st.error("❌ Claude API not configured. Please enter your API key on the Upload page.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔧 Complete Missing Fields")

        incomplete_rows = st.session_state.csv_handler.get_rows_needing_completion()

        if incomplete_rows.empty:
            st.success("🎉 All fields are complete!")
        else:
            st.info(f"Found {len(incomplete_rows)} rows with missing data")

            max_rows = st.slider("Max rows to process", 1, min(20, len(incomplete_rows)), 5)

            if st.button("🚀 Start Batch Completion"):
                with st.spinner("AI is completing your BOM..."):
                    completed_df = st.session_state.ai_optimizer.batch_complete_bom(
                        st.session_state.current_df, max_rows
                    )
                    st.session_state.current_df = completed_df
                    st.success("✅ Batch completion finished!")
                    st.rerun()

    with col2:
        st.subheader("💡 Supplier Optimization")

        if st.button("🔍 Analyze Suppliers"):
            with st.spinner("Analyzing supplier optimization opportunities..."):
                suggestions = st.session_state.ai_optimizer.optimize_suppliers(st.session_state.current_df)
                st.session_state.optimization_suggestions = suggestions

        if hasattr(st.session_state, 'optimization_suggestions'):
            UIComponents.render_optimization_suggestions(st.session_state.optimization_suggestions)

    st.markdown("---")
    st.subheader("🎯 Completion Priority")

    priorities = st.session_state.validator.get_completion_priority(st.session_state.current_df)

    if priorities:
        priority_df = pd.DataFrame(priorities, columns=['Row', 'Missing Fields', 'Priority Score'])
        st.dataframe(priority_df.head(10), hide_index=True)
    else:
        st.success("🎉 No completion priorities - all data is complete!")

def analytics_page():
    st.title("📊 BOM Analytics")

    if st.session_state.current_df.empty:
        st.warning("No data loaded. Please upload and process a file first.")
        return

    UIComponents.render_cost_analytics(st.session_state.current_df)

    st.markdown("---")
    st.subheader("📈 Data Completeness")

    missing_summary = st.session_state.csv_handler.get_missing_data_summary()
    UIComponents.render_missing_data_summary(missing_summary)

def export_page():
    st.title("📤 Export Your Completed BOM")

    if st.session_state.current_df.empty:
        st.warning("No data to export. Please upload and process a file first.")
        return

    UIComponents.render_export_options(st.session_state.current_df)

    st.markdown("---")
    st.subheader("📋 Final Data Preview")
    st.dataframe(st.session_state.current_df, use_container_width=True)

def main():
    initialize_session_state()

    page = UIComponents.render_sidebar()

    if page == "Upload & Process":
        upload_and_process_page()
    elif page == "Review & Edit":
        review_and_edit_page()
    elif page == "AI Optimization":
        ai_optimization_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "Export":
        export_page()

    st.markdown("---")
    st.markdown(
        "💡 **Tip:** Start by uploading your BOM file, then use AI optimization to complete missing fields!"
    )

if __name__ == "__main__":
    main()