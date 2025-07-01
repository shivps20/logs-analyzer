import streamlit as st


# Function to create a file uploader widget
def file_uploader(key=None):
    return st.file_uploader(
        "📂 Upload one or more 3DEXPERIENCE Log/Dump Files (stderr.log / mxtrace.log / any)",
        type=["log", "txt", "tdump"],
        accept_multiple_files=True,
        key=key
    )

# def file_uploader():
#     # If clear_files is set, reset the flag (the uploader will show empty)
#     if st.session_state.get("clear_files", False):
#         st.session_state["clear_files"] = False
#         # No early return here

#     return st.file_uploader(
#         "📂 Upload one or more 3DEXPERIENCE Log Files (stderr.log / mxtrace.log / any)",
#         type=["log", "txt"],
#         accept_multiple_files=True,
#         key="uploaded_files"
#     )

# def show_clear_all_files_button():
#     # Button to clear all files
#     if st.button("🗑️ Clear All Files"):
#         st.session_state["clear_files"] = True
#         st.rerun()