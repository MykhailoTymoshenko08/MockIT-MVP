import streamlit as st
import requests
import os

# getting backend address from env or defaulting to local for dev
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# setting up basic page layout and title
st.set_page_config(page_title="Recruitment Suite", layout="centered")

st.title("Recruitment Suite")
st.markdown("A single space for recruiting: from the first message to the technical interview.")

# splitting features into tabs for better ux
tab1, tab2 = st.tabs(["MockIT (Tech Interview)", "Speed-Dating Bot (Screening)"])

with tab1:
    st.subheader("Interview Plan Generation")
    with st.form("cv_form_mockit"):
        # inputs for role and resume file
        role_1 = st.text_input("Candidate Role", key="role_1")
        file_1 = st.file_uploader("Upload Resume (PDF)", type="pdf", key="file_1")
        submit_1 = st.form_submit_button("Generate Plan")

    if submit_1 and role_1 and file_1:
        with st.spinner("Analyzing..."):
            # preparing file for multipart/form-data request
            files = {"file": (file_1.name, file_1.getvalue(), "application/pdf")}
            # sending data to fastapi backend
            res = requests.post(f"{BACKEND_URL}/analyze/", data={"role": role_1}, files=files).json()
            
            if res.get("status") == "success":
                # iterating through ai-generated questions
                for i, q in enumerate(res["data"], 1):
                    st.markdown(f"{i}. {q.get('question')}")
                    # hidden details to keep the ui clean
                    with st.expander("Details"):
                        st.write(f"✅ Expected: {q.get('expected_answer')}")
                        st.write(f"🚩 Red flags: {q.get('red_flags')}")
            else:
                # feedback on backend or ai failure
                st.error(f"❌ Error: {res.get('message', 'Unknown error')}")

with tab2:
    st.subheader("Screening Message Generation")
    with st.form("cv_form_speed"):
        role_2 = st.text_input("Candidate Role", key="role_2")
        file_2 = st.file_uploader("Upload Resume (PDF)", type="pdf", key="file_2")
        submit_2 = st.form_submit_button("Generate Message")

    if submit_2 and role_2 and file_2:
        with st.spinner("Writing message..."):
            files = {"file": (file_2.name, file_2.getvalue(), "application/pdf")}
            res = requests.post(f"{BACKEND_URL}/screening/", data={"role": role_2}, files=files).json()
            
            if res.get("status") == "success":
                data = res["data"]
                st.success("Done! Ready to copy and send.")
                # displaying the generated message in a code block for easy copying
                st.markdown("### Message to Candidate:")
                st.code(data.get("message", "Text generation error"), language="markdown")
                # internal hr notes display
                st.markdown("### HR Note:")
                st.info(data.get("internal_notes", "No notes"))
            else:
                st.error(f"❌ Error: {res.get('message', 'Unknown error')}")