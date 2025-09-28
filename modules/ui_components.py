import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
from config import ALL_COLUMNS, REQUIRED_COLUMNS, OPTIONAL_COLUMNS, COLUMN_DESCRIPTIONS

class UIComponents:
    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.title("🤖 AI BOM Optimizer")
            st.markdown("---")

            st.subheader("Navigation")
            page = st.radio(
                "Choose a page:",
                ["Upload & Process", "Review & Edit", "AI Optimization", "Analytics", "Export"],
                index=0
            )

            st.markdown("---")
            st.subheader("Quick Actions")

            if st.button("🔄 Reset Session"):
                for key in list(st.session_state.keys()):
                    if key.startswith('bom_'):
                        del st.session_state[key]
                st.rerun()

            if st.button("📥 Download Template"):
                UIComponents.download_template()

            return page

    @staticmethod
    def download_template():
        template_path = "templates/bom_template.csv"
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            st.download_button(
                label="📥 BOM Template",
                data=template_content,
                file_name="bom_template.csv",
                mime="text/csv"
            )
        except FileNotFoundError:
            st.error("Template file not found")

    @staticmethod
    def render_api_key_input():
        st.subheader("🔑 API Configuration")

        api_key = st.text_input(
            "Claude API Key",
            type="password",
            placeholder="Enter your Anthropic API key",
            help="Get your API key from https://console.anthropic.com/"
        )

        if api_key:
            import os
            os.environ["ANTHROPIC_API_KEY"] = api_key
            st.success("✅ API key configured")

            # Store current API key
            st.session_state.current_api_key = api_key

            # Add buttons for testing and fetching models
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🧪 Test API Connection"):
                    from modules.ai_optimizer import AIOptimizer

                    # Force reinitialize the optimizer with new API key
                    if 'ai_optimizer' in st.session_state:
                        st.session_state.ai_optimizer = AIOptimizer()

                    test_optimizer = st.session_state.ai_optimizer
                    if test_optimizer.test_api_connection():
                        st.success("🎉 API connection successful!")
                    else:
                        st.error("❌ API connection failed. Check the error details above.")

            with col2:
                if st.button("🔄 Fetch Latest Models"):
                    with st.spinner("🔍 Fetching available models from Anthropic API..."):
                        try:
                            from config import fetch_available_models
                            new_models = fetch_available_models(api_key)
                            st.session_state.available_models = new_models
                            st.session_state.models_fetched = True

                            # Count how many models we got
                            model_count = len(new_models)
                            st.success(f"✅ Fetched {model_count} available models!")

                            # Show new models found
                            new_model_names = [info['name'] for info in new_models.values()]
                            st.info(f"📋 Available models: {', '.join(new_model_names[:3])}{'...' if len(new_model_names) > 3 else ''}")

                            # Force page refresh to update dropdown
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Failed to fetch models: {str(e)}")
                            st.warning("Using static model list as fallback")

            # Model selection dropdown (after API key is entered)
            st.markdown("---")
            st.subheader("🤖 Model Selection")

            # Model selection dropdown with dynamic fetching
            from config import AVAILABLE_MODELS, CLAUDE_MODEL

            # Check if we have cached models in session state
            if 'available_models' not in st.session_state:
                st.session_state.available_models = AVAILABLE_MODELS
                st.session_state.models_fetched = False

            model_options = []
            model_keys = []
            default_index = 0

            # Use current models (cached or static)
            available_models = st.session_state.available_models

            for i, (model_key, model_info) in enumerate(available_models.items()):
                display_name = model_info["name"]
                if model_info["recommended"]:
                    display_name += " ⭐ (Recommended)"
                model_options.append(display_name)
                model_keys.append(model_key)

                if model_key == CLAUDE_MODEL:
                    default_index = i

            selected_model_index = st.selectbox(
                "Select Claude Model",
                range(len(model_options)),
                format_func=lambda x: model_options[x],
                index=default_index,
                help="Choose the Claude model to use for AI completion"
            )

            selected_model_key = model_keys[selected_model_index]
            selected_model_info = available_models[selected_model_key]

            # Show model description
            st.info(f"📋 {selected_model_info['description']}")
            st.caption(f"Max tokens: {selected_model_info['max_tokens']:,}")

            # Store selected model in session state
            if 'selected_model' not in st.session_state or st.session_state.selected_model != selected_model_key:
                st.session_state.selected_model = selected_model_key
                # Force reinitialize AI optimizer when model changes
                if 'ai_optimizer' in st.session_state:
                    st.session_state.ai_optimizer = None

            # Show status of model fetching
            if not st.session_state.models_fetched:
                st.caption("💡 Click 'Fetch Latest Models' above to get the most up-to-date model list from Anthropic")
            else:
                st.caption("✅ Using dynamically fetched models from Anthropic API")

            return True
        else:
            st.warning("⚠️ Please enter your Claude API key to use AI features")
            return False

    @staticmethod
    def render_file_upload():
        st.subheader("📁 Upload BOM File")

        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload your Bill of Materials file. Use our template for best results."
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Template"):
                UIComponents.download_template()

        with col2:
            if uploaded_file and st.button("🔍 Preview File"):
                try:
                    if uploaded_file.name.endswith('.csv'):
                        preview_df = pd.read_csv(uploaded_file, nrows=5)
                    else:
                        preview_df = pd.read_excel(uploaded_file, nrows=5)
                    st.write("Preview (first 5 rows):")
                    st.dataframe(preview_df)
                except Exception as e:
                    st.error(f"Error previewing file: {str(e)}")

        return uploaded_file

    @staticmethod
    def render_column_mapping(original_columns: List[str]) -> Dict[str, str]:
        st.subheader("🔗 Column Mapping")
        st.write("Map your file columns to standard BOM fields:")

        mapping = {}
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Required Fields:**")
            for field in REQUIRED_COLUMNS:
                mapping[field] = st.selectbox(
                    f"{field} *",
                    [""] + original_columns,
                    help=COLUMN_DESCRIPTIONS.get(field, "")
                )

        with col2:
            st.write("**Optional Fields:**")
            for field in OPTIONAL_COLUMNS:
                mapping[field] = st.selectbox(
                    f"{field}",
                    [""] + original_columns,
                    help=COLUMN_DESCRIPTIONS.get(field, "")
                )

        return {k: v for k, v in mapping.items() if v}

    @staticmethod
    def render_validation_results(validation_results: Dict):
        if not any(validation_results.values()):
            st.success("✅ All validations passed!")
            return

        errors = validation_results.get('errors', [])
        warnings = validation_results.get('warnings', [])
        info = validation_results.get('info', [])

        if errors:
            st.error(f"❌ {len(errors)} Error(s) found:")
            for error in errors[:10]:
                row_info = f" (Row {error['row'] + 1})" if error['row'] is not None else ""
                st.write(f"• {error['message']}{row_info}")
            if len(errors) > 10:
                st.write(f"... and {len(errors) - 10} more errors")

        if warnings:
            st.warning(f"⚠️ {len(warnings)} Warning(s):")
            for warning in warnings[:10]:
                row_info = f" (Row {warning['row'] + 1})" if warning['row'] is not None else ""
                st.write(f"• {warning['message']}{row_info}")
            if len(warnings) > 10:
                st.write(f"... and {len(warnings) - 10} more warnings")

        if info:
            st.info(f"ℹ️ {len(info)} Info message(s):")
            for information in info[:5]:
                row_info = f" (Row {information['row'] + 1})" if information['row'] is not None else ""
                st.write(f"• {information['message']}{row_info}")

    @staticmethod
    def render_missing_data_summary(missing_summary: Dict):
        st.subheader("📊 Missing Data Summary")

        if not missing_summary:
            st.info("No missing data summary available")
            return

        summary_data = []
        for field, data in missing_summary.items():
            summary_data.append({
                'Field': field,
                'Missing': data['missing_count'],
                'Total': data['total_count'],
                'Percentage': f"{data['missing_percentage']:.1f}%",
                'Required': '✓' if data['is_required'] else '○'
            })

        df_summary = pd.DataFrame(summary_data)

        df_summary['Missing_Numeric'] = [missing_summary[row['Field']]['missing_count'] for _, row in df_summary.iterrows()]
        df_summary['Percentage_Numeric'] = [missing_summary[row['Field']]['missing_percentage'] for _, row in df_summary.iterrows()]

        col1, col2 = st.columns(2)

        with col1:
            st.dataframe(
                df_summary[['Field', 'Missing', 'Total', 'Percentage', 'Required']],
                hide_index=True
            )

        with col2:
            if len(summary_data) > 0:
                fig = px.bar(
                    df_summary,
                    x='Field',
                    y='Missing_Numeric',
                    title='Missing Data by Field',
                    color='Required',
                    color_discrete_map={'✓': '#ff6b6b', '○': '#feca57'}
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    height=400,
                    xaxis={'tickangle': 45}
                )
                st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_data_editor(df: pd.DataFrame) -> pd.DataFrame:
        st.subheader("✏️ Edit BOM Data")

        if df.empty:
            st.info("No data to edit")
            return df

        col1, col2, col3 = st.columns(3)
        with col1:
            show_all = st.checkbox("Show all rows", value=False)
        with col2:
            show_empty_only = st.checkbox("Show incomplete rows only", value=True)
        with col3:
            max_rows = st.slider("Max rows to display", 5, 50, 20)

        display_df = df.copy()

        if show_empty_only and not show_all:
            mask = pd.Series([False] * len(df), index=df.index)
            for col in df.columns:
                mask |= (df[col].isna() | (df[col] == ""))
            display_df = df[mask]

        if not show_all:
            display_df = display_df.head(max_rows)

        if display_df.empty:
            st.info("No rows match the current filter criteria")
            return df

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=False,
            num_rows="dynamic"
        )

        return edited_df

    @staticmethod
    def render_cost_analytics(df: pd.DataFrame):
        st.subheader("💰 Cost Analytics")

        if df.empty or 'total_cost' not in df.columns:
            st.info("No cost data available for analysis")
            return

        cost_data = pd.to_numeric(df['total_cost'], errors='coerce').dropna()

        if cost_data.empty:
            st.info("No valid cost data found")
            return

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Cost", f"${cost_data.sum():.2f}")
        with col2:
            st.metric("Average Cost", f"${cost_data.mean():.2f}")
        with col3:
            st.metric("Median Cost", f"${cost_data.median():.2f}")
        with col4:
            st.metric("Cost Items", len(cost_data))

        if 'category' in df.columns:
            category_costs = df.groupby('category')['total_cost'].sum().reset_index()
            category_costs = category_costs[category_costs['total_cost'] > 0]

            if not category_costs.empty:
                fig = px.pie(
                    category_costs,
                    values='total_cost',
                    names='category',
                    title='Cost Distribution by Category'
                )
                st.plotly_chart(fig, use_container_width=True)

        if 'supplier' in df.columns:
            supplier_costs = df.groupby('supplier')['total_cost'].sum().reset_index()
            supplier_costs = supplier_costs[supplier_costs['total_cost'] > 0]
            supplier_costs = supplier_costs.sort_values('total_cost', ascending=False).head(10)

            if not supplier_costs.empty:
                fig = px.bar(
                    supplier_costs,
                    x='supplier',
                    y='total_cost',
                    title='Top 10 Suppliers by Cost'
                )
                fig.update_layout(xaxis={'tickangle': 45})
                st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_optimization_suggestions(suggestions: List[Dict]):
        st.subheader("🎯 AI Optimization Suggestions")

        if not suggestions:
            st.info("No optimization suggestions available")
            return

        for i, suggestion in enumerate(suggestions):
            with st.expander(f"Suggestion {i+1}: {suggestion.get('recommendation', 'Unknown')}"):
                st.write(f"**Current Suppliers:** {', '.join(suggestion.get('current_suppliers', []))}")
                st.write(f"**Suggested Supplier:** {suggestion.get('suggested_supplier', 'N/A')}")
                st.write(f"**Affected Parts:** {', '.join(suggestion.get('affected_parts', []))}")
                st.write(f"**Potential Savings:** {suggestion.get('potential_savings', 'Unknown')}")

    @staticmethod
    def render_export_options(df: pd.DataFrame):
        st.subheader("📤 Export Options")

        if df.empty:
            st.info("No data to export")
            return

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Export as CSV:**")
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name="completed_bom.csv",
                mime="text/csv"
            )

        with col2:
            st.write("**Export as Excel:**")
            try:
                import io
                output = io.BytesIO()
                df.to_excel(output, index=False, engine='openpyxl')
                excel_data = output.getvalue()

                st.download_button(
                    label="📊 Download Excel",
                    data=excel_data,
                    file_name="completed_bom.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except ImportError:
                st.error("Excel export requires openpyxl package")

        st.subheader("📈 Export Summary")
        total_rows = len(df)
        complete_rows = 0
        for _, row in df.iterrows():
            if all(pd.notna(row[col]) and str(row[col]).strip() != "" for col in REQUIRED_COLUMNS if col in df.columns):
                complete_rows += 1

        completion_rate = (complete_rows / total_rows) * 100 if total_rows > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", total_rows)
        with col2:
            st.metric("Complete Rows", complete_rows)
        with col3:
            st.metric("Completion Rate", f"{completion_rate:.1f}%")