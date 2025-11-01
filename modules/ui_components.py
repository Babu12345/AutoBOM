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

            # Get current page from session state
            current_page = st.session_state.get('current_page', "Upload & Process")

            pages = ["Upload & Process", "Review & Edit", "AI Optimization", "Analytics", "Export"]
            current_index = pages.index(current_page) if current_page in pages else 0

            page = st.radio(
                "Choose a page:",
                pages,
                index=current_index
            )

            # Store current page in session state
            st.session_state.current_page = page

            # Show workflow progress
            st.markdown("---")
            st.subheader("📋 Workflow Progress")

            progress_items = [
                ("Upload & Process", "📁", st.session_state.get('file_uploaded', False)),
                ("Review & Edit", "✏️", st.session_state.get('columns_mapped', False)),
                ("AI Optimization", "🤖", st.session_state.get('ai_completed', False)),
                ("Analytics", "📊", st.session_state.get('analytics_viewed', False)),
                ("Export", "📤", st.session_state.get('exported', False))
            ]

            for page_name, emoji, completed in progress_items:
                status = "✅" if completed else "⏳"
                st.write(f"{status} {emoji} {page_name}")

            st.markdown("---")
            st.subheader("Quick Actions")

            if st.button("🔄 Reset Session"):
                for key in list(st.session_state.keys()):
                    if key.startswith('bom_') or key in ['current_page', 'file_uploaded', 'columns_mapped', 'ai_completed', 'analytics_viewed', 'exported']:
                        del st.session_state[key]
                st.rerun()

            if st.button("📥 Download Template"):
                UIComponents.download_template()

            # Column Configuration Section
            st.markdown("---")
            st.subheader("⚙️ Column Config")

            # Show current configuration status
            column_config = UIComponents.get_current_column_config()
            required_count = len(column_config['required'])
            optional_count = len(column_config['optional'])

            if 'app_required_columns' in st.session_state:
                st.success(f"🎯 Custom: {required_count}R + {optional_count}O")
            else:
                st.info(f"📎 Default: {required_count}R + {optional_count}O")

            if st.button("⚙️ Configure Columns", key="configure_columns_button"):
                st.session_state.show_column_config = not st.session_state.get('show_column_config', False)

            if st.session_state.get('show_column_config', False):
                UIComponents.render_column_configuration()

            # Copyright notice
            st.markdown("---")
            st.markdown(
                "<div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 20px;'>"
                "© 2025 Babuabel Wanyeki<br>"
                "<em>All rights reserved</em>"
                "</div>",
                unsafe_allow_html=True
            )

            return page

    @staticmethod
    def render_next_button(current_page: str, next_page: str, condition: bool = True, button_text: str = None):
        """Render a Next button to navigate to the next step in the workflow"""
        if not condition:
            return False

        if button_text is None:
            button_text = f"➡️ Continue to {next_page}"

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(button_text, type="primary", use_container_width=True):
                st.session_state.current_page = next_page
                st.rerun()
                return True
        return False

    @staticmethod
    def mark_step_completed(step: str):
        """Mark a workflow step as completed"""
        step_map = {
            "upload": "file_uploaded",
            "mapping": "columns_mapped",
            "ai": "ai_completed",
            "analytics": "analytics_viewed",
            "export": "exported"
        }
        if step in step_map:
            st.session_state[step_map[step]] = True

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

        # Preserve API key in session state
        if 'api_key' not in st.session_state:
            st.session_state.api_key = ""

        api_key = st.text_input(
            "Claude API Key",
            type="password",
            value=st.session_state.api_key,
            placeholder="Enter your Anthropic API key",
            help="Get your API key from https://console.anthropic.com/"
        )

        # Update session state when key changes
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key

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

                # Check if user has a previously selected model in session state
                if 'selected_model' in st.session_state and model_key == st.session_state.selected_model:
                    default_index = i
                elif 'selected_model' not in st.session_state and model_key == CLAUDE_MODEL:
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

        # Show current file status if file was previously uploaded
        if st.session_state.get('file_uploaded', False) and 'uploaded_filename' in st.session_state:
            st.success(f"✅ File loaded: {st.session_state.uploaded_filename}")
            st.info("📄 File data is preserved in your session. You can navigate to other pages and preview the data below.")

        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload your Bill of Materials file. Use our template for best results."
        )

        # Store filename when file is uploaded
        if uploaded_file:
            st.session_state.uploaded_filename = uploaded_file.name

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Template"):
                UIComponents.download_template()

        with col2:
            # Show preview button for either newly uploaded file or preserved data
            show_preview_button = False
            preview_source = None

            if uploaded_file:
                show_preview_button = True
                preview_source = "uploaded"
            elif st.session_state.get('file_uploaded', False) and hasattr(st.session_state, 'csv_handler') and st.session_state.csv_handler.df is not None:
                show_preview_button = True
                preview_source = "preserved"

            if show_preview_button and st.button("🔍 Preview File"):
                try:
                    if preview_source == "uploaded":
                        # Preview from newly uploaded file
                        if uploaded_file.name.endswith('.csv'):
                            preview_df = pd.read_csv(uploaded_file, nrows=5)
                        else:
                            preview_df = pd.read_excel(uploaded_file, nrows=5)
                        st.write("Preview (first 5 rows):")
                    else:
                        # Preview from preserved session data
                        preview_df = st.session_state.csv_handler.df.head(5)
                        st.write(f"Preview of {st.session_state.uploaded_filename} (first 5 rows):")

                    st.dataframe(preview_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error previewing file: {str(e)}")

        return uploaded_file

    @staticmethod
    def render_column_mapping(original_columns: List[str]) -> Dict[str, str]:
        st.subheader("🔗 Column Mapping")
        st.write("Map your file columns to standard BOM fields:")

        # Get current column configuration
        column_config = UIComponents.get_current_column_config()
        required_columns = column_config['required']
        optional_columns = column_config['optional']

        # Initialize column mapping in session state if not exists
        if 'column_mapping' not in st.session_state:
            st.session_state.column_mapping = {}

        mapping = {}
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Required Fields:**")
            for field in required_columns:
                # Get previous selection or default to empty
                previous_selection = st.session_state.column_mapping.get(field, "")
                # Make sure the previous selection is still available
                if previous_selection not in original_columns:
                    previous_selection = ""

                default_index = 0
                options = [""] + original_columns
                if previous_selection and previous_selection in options:
                    default_index = options.index(previous_selection)

                mapping[field] = st.selectbox(
                    f"{field} *",
                    options,
                    index=default_index,
                    help=COLUMN_DESCRIPTIONS.get(field, "")
                )

        with col2:
            st.write("**Optional Fields:**")
            for field in optional_columns:
                # Get previous selection or default to empty
                previous_selection = st.session_state.column_mapping.get(field, "")
                # Make sure the previous selection is still available
                if previous_selection not in original_columns:
                    previous_selection = ""

                default_index = 0
                options = [""] + original_columns
                if previous_selection and previous_selection in options:
                    default_index = options.index(previous_selection)

                mapping[field] = st.selectbox(
                    f"{field}",
                    options,
                    index=default_index,
                    help=COLUMN_DESCRIPTIONS.get(field, "")
                )

        # Update session state with current mapping
        st.session_state.column_mapping = mapping.copy()

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

        # Get current column configuration
        column_config = UIComponents.get_current_column_config()
        all_columns = column_config['all']
        required_columns = column_config['required']
        optional_columns = column_config['optional']

        # Ensure all configured columns are present and in the right order
        for col in all_columns:
            if col not in display_df.columns:
                display_df[col] = ""

        # Reorder columns to show required ones first
        ordered_columns = [col for col in all_columns if col in display_df.columns]
        other_columns = [col for col in display_df.columns if col not in all_columns]
        display_df = display_df[ordered_columns + other_columns]

        if show_empty_only and not show_all:
            mask = pd.Series([False] * len(df), index=df.index)
            for col in df.columns:
                mask |= (df[col].isna() | (df[col] == ""))
            display_df = display_df[mask]

        if not show_all:
            display_df = display_df.head(max_rows)

        if display_df.empty:
            st.info("No rows match the current filter criteria")
            return df

        # Show column information for debugging
        st.caption(f"📊 Displaying {len(display_df)} rows with {len(display_df.columns)} columns: {', '.join(display_df.columns[:5])}{'...' if len(display_df.columns) > 5 else ''}")
        st.caption(f"📋 Required columns present: {[col for col in required_columns if col in display_df.columns]}")
        st.caption(f"📋 Optional columns present: {[col for col in optional_columns if col in display_df.columns]}")
        if len(required_columns) != len(column_config['required']) or len(optional_columns) != len(column_config['optional']):
            st.caption("⚙️ Using custom column configuration")

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=False,
            num_rows="dynamic"
        )

        # Merge the edited subset back into the full dataframe
        full_df = df.copy()
        if not edited_df.empty and not edited_df.equals(display_df):
            # Update the full dataframe with changes from the editor
            for idx in edited_df.index:
                if idx in full_df.index:
                    full_df.loc[idx] = edited_df.loc[idx]

        return full_df

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
            # Convert total_cost to numeric before grouping and filtering
            df_numeric = df.copy()
            df_numeric['total_cost'] = pd.to_numeric(df_numeric['total_cost'], errors='coerce').fillna(0)

            category_costs = df_numeric.groupby('category')['total_cost'].sum().reset_index()
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
            # Convert total_cost to numeric before grouping and filtering
            df_numeric = df.copy()
            df_numeric['total_cost'] = pd.to_numeric(df_numeric['total_cost'], errors='coerce').fillna(0)

            supplier_costs = df_numeric.groupby('supplier')['total_cost'].sum().reset_index()
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

    @staticmethod
    def render_column_configuration():
        """Render column configuration UI for customizing required/optional columns"""
        st.subheader("⚙️ Column Configuration")
        st.caption("Customize which columns are required vs optional for your BOM")

        from config import ALL_COLUMNS, COLUMN_DESCRIPTIONS

        # Initialize custom column configuration in session state
        if 'custom_required_columns' not in st.session_state:
            from config import REQUIRED_COLUMNS
            st.session_state.custom_required_columns = REQUIRED_COLUMNS.copy()

        if 'custom_optional_columns' not in st.session_state:
            from config import OPTIONAL_COLUMNS
            st.session_state.custom_optional_columns = OPTIONAL_COLUMNS.copy()

        # Create two lists for configuration
        all_available_columns = ALL_COLUMNS.copy()

        st.write("**Select Required Columns:**")
        st.caption("🔴 Required columns must be filled for complete BOM entries")

        required_columns = st.multiselect(
            "Required columns",
            options=all_available_columns,
            default=st.session_state.custom_required_columns,
            format_func=lambda x: f"{x} - {COLUMN_DESCRIPTIONS.get(x, 'No description')}",
            key="required_columns_multiselect"
        )

        # Optional columns are all remaining columns
        optional_columns = [col for col in all_available_columns if col not in required_columns]

        st.write("**Optional Columns:**")
        st.caption("🟡 Optional columns can be empty and will be suggested by AI")

        # Show optional columns as info (read-only)
        if optional_columns:
            optional_display = [f"{col} - {COLUMN_DESCRIPTIONS.get(col, 'No description')}" for col in optional_columns]
            st.info("\n".join([f"• {item}" for item in optional_display]))
        else:
            st.info("All columns are marked as required")

        # Update session state
        st.session_state.custom_required_columns = required_columns
        st.session_state.custom_optional_columns = optional_columns

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Apply Changes", key="apply_column_config"):
                # Update the global configuration
                UIComponents.apply_column_configuration(required_columns, optional_columns)
                st.success("✅ Column configuration applied!")
                st.session_state.show_column_config = False
                st.rerun()

        with col2:
            if st.button("🔄 Reset to Default", key="reset_column_config"):
                from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS
                st.session_state.custom_required_columns = REQUIRED_COLUMNS.copy()
                st.session_state.custom_optional_columns = OPTIONAL_COLUMNS.copy()
                st.success("🔄 Reset to default configuration!")
                st.rerun()

        with col3:
            if st.button("❌ Cancel", key="cancel_column_config"):
                st.session_state.show_column_config = False
                st.rerun()

    @staticmethod
    def apply_column_configuration(required_columns, optional_columns):
        """Apply the custom column configuration globally"""
        # Store in session state for use throughout the app
        st.session_state.app_required_columns = required_columns
        st.session_state.app_optional_columns = optional_columns
        st.session_state.app_all_columns = required_columns + optional_columns

        # Show current configuration
        st.info(f"📊 Applied: {len(required_columns)} required, {len(optional_columns)} optional columns")

    @staticmethod
    def get_current_column_config():
        """Get the current column configuration (custom or default)"""
        if 'app_required_columns' in st.session_state:
            return {
                'required': st.session_state.app_required_columns,
                'optional': st.session_state.app_optional_columns,
                'all': st.session_state.app_all_columns
            }
        else:
            # Use default configuration
            from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS, ALL_COLUMNS
            return {
                'required': REQUIRED_COLUMNS,
                'optional': OPTIONAL_COLUMNS,
                'all': ALL_COLUMNS
            }