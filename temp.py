import streamlit as st

# Define the pages with corresponding labels
options_with_labels = {
    "Learn": ['a', 'b', 'c'],
    "Prepare": ['d', 'e'],
    "Validate": ['f']
}

# Flatten the list and include group names for visual effect in the radio options
def format_option(option):
    for group, items in options_with_labels.items():
        if option in items:
            return f"{group}: {option}"
    return option

# List of all options without group labels
allowed_pages = [item for sublist in options_with_labels.values() for item in sublist]

# Display the radio button with a custom format
selected_option = st.radio(
    "Select a Page:",
    options=allowed_pages,
    format_func=format_option,
)

# Update the session state
st.session_state.page = selected_option
