import streamlit as st
import pandas as pd

def confirm_table(default_table):
    # Initialize session state variables
                
    # Only display the form if it hasn't been submitted yet
    if not st.session_state['form_submitted']:
        st.write("Please confirm the table below:")
        st.write(default_table)
        
        # List of tables to choose from
        tables = ['foo', 'bar', 'baz']
        
        # Use a form to capture user input
        with st.form(key='table_form'):
            selected_table = st.selectbox('Select a table', tables, index=tables.index(default_table))
            submit_button = st.form_submit_button(label='Confirm')

        if submit_button:
            if selected_table:
                # Update session state variables
                st.session_state['form_submitted'] = True
                st.session_state['selected_table'] = selected_table
                st.write(f'You selected {selected_table}')
                st.rerun()
    else:
        pass 
        # Form has been submitted, you can display the result or proceed further
        # st.write(f"You have already selected: {st.session_state['selected_table']}")
        # Proceed with the selected table
        # Add further processing here

# Example usage
default_table = 'foo'
st.session_state['selected_table'] = default_table
st.session_state['form_submitted'] = st.session_state.get('form_submitted') or  False
confirm_table(default_table)
