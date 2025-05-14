import streamlit as st
import openai
import json
import pandas as pd
import re
import fitz  # PyMuPDF

# --- OpenAI Setup ---
api_key = st.secrets["OPENAI_API_KEY"]
client = openai.OpenAI(api_key=api_key)

# --- Section Checklists ---
dpdpa_checklists = {
    "4": {
        "title": "Grounds for Processing Personal Data",
        "items": [
            "Personal data is processed only for a lawful purpose.",
            "Lawful purpose means a purpose not expressly forbidden by law.",
            "Lawful purpose must be backed by explicit consent from the Data Principal or fall under legitimate uses."
        ]
    },
    "5": {
        "title": "Notice",
        "items": [
            "Notice is provided in clear and plain language.",
            "Notice is made available before or at the time of data collection.",
            "Notice includes the purpose of processing personal data.",
            "Notice specifies the rights of the Data Principal.",
            "Notice includes details of the Data Fiduciary and means to contact them.",
            "Notice discloses the manner in which the Data Principal can exercise their rights.",
            "Notice is accessible in English or any language listed in the Eighth Schedule of the Constitution of India."
        ]
    },
    "6": {
        "title": "Consent",
        "items": [
            "Consent is free (voluntary, not coerced).",
            "Consent is specific to a clearly defined purpose.",
            "Consent is informed (based on full information provided beforehand).",
            "Consent is unambiguous (clearly understood and intentional).",
            "Consent is given via clear affirmative action.",
            "Consent is limited to the specified purpose only.",
            "Only personal data necessary for the purpose is processed.",
            "Consent is provided before data processing begins.",
            "Data Principal has the ability to withdraw consent easily and at any time.",
            "If consent is withdrawn, data processing stops and data is erased unless legally required."
        ]
    },
    "7": {
        "title": "Certain Legitimate Uses",
        "items": [
            "Processing is necessary for performance of any function under the law or in the interest of the sovereignty and integrity of India.",
            "Processing is necessary for compliance with any judgment, order, or decree of any court or tribunal in India.",
            "Processing is necessary for responding to a medical emergency involving a threat to life or health.",
            "Processing is necessary for taking measures to ensure safety during any disaster or breakdown of public order.",
            "Processing is necessary for purposes related to employment or provision of service.",
            "Processing is necessary for the purpose of public interest such as prevention of fraud, network and information security, or credit scoring.",
            "Processing is for purposes of corporate governance, mergers, or disclosures under legal obligations.",
            "Processing is necessary for any fair and reasonable purpose specified by the Data Protection Board."
        ]
    },
    "8": {
        "title": "General Obligations of Data Fiduciary",
        "items": [
            "Implements appropriate technical and organizational measures to ensure compliance with DPDPA.",
            "Maintains data accuracy and completeness to ensure it is up-to-date.",
            "Implements reasonable security safeguards to prevent personal data breaches.",
            "Notifies the Data Protection Board and affected Data Principals in the event of a breach.",
            "Erases personal data as soon as the purpose is fulfilled and retention is no longer necessary.",
            "Maintains records of processing activities in accordance with prescribed rules.",
            "Conducts periodic Data Protection Impact Assessments if required.",
            "Appoints a Data Protection Officer (DPO) if classified as a Significant Data Fiduciary.",
            "Publishes the business contact information of the DPO or person handling grievances."
        ]
    }
    }
    # Add similar checklist dicts for sections 5–8

# --- Block Splitter ---
def break_into_blocks(text):
    lines = text.splitlines()
    blocks, current_block = [], []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^([A-Z][A-Za-z\s]+|[0-9]+\.\s.*)$', stripped):
            if current_block:
                blocks.append(' '.join(current_block).strip())
                current_block = []
            current_block.append(stripped)
        else:
            current_block.append(stripped)
    if current_block:
        blocks.append(' '.join(current_block).strip())
    return blocks

# --- PDF Extractor ---
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

# --- Prompt Generator ---
def create_block_prompt(section_id, block_text, checklist):
    checklist_text = "\n".join(f"- {item}" for item in checklist)
    return f"""
    You are a compliance analyst evaluating whether the following privacy policy block meets DPDPA Section {section_id}: {dpdpa_checklists[section_id]['title']}.
    
    **Checklist:**
    {checklist_text}
    
    **Policy Block:**
    {block_text}
    
    Evaluate each checklist item as: Explicitly Mentioned / Partially Mentioned / Missing.
    Return output in this format:
    {{
      "Match Level": "...",
      "Compliance Score": 0.0,
      "Checklist Evaluation": [
        {{"Checklist Item": "...", "Status": "...", "Justification": "..."}}
      ],
      "Suggested Rewrite": "...",
      "Simplified Legal Meaning": "..."
    }}
    """

# --- GPT Call ---
def call_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return json.loads(response.choices[0].message.content)

# --- Scoring Logic ---
def compute_score_and_level(evaluations, total_items):
    matched = [e for e in evaluations if e["Status"].lower() == "explicitly mentioned"]
    partial = [e for e in evaluations if e["Status"].lower() == "partially mentioned"]
    score = (len(matched) + 0.5 * len(partial)) / total_items if total_items else 0.0
    if score >= 1.0:
        level = "Fully Compliant"
    elif score == 0:
        level = "Non-Compliant"
    else:
        level = "Partially Compliant"
    return round(score, 2), level

# --- Analyzer ---
def analyze_policy_section(section_id, checklist, policy_text):
    blocks = break_into_blocks(policy_text)
    all_results = []

    for block in blocks:
        prompt = create_block_prompt(section_id, block, checklist)
        try:
            result = call_gpt(prompt)
            result["Block"] = block
            all_results.append(result)
        except:
            continue

    matched_items = {}

    if section_id == "8":
        canonical_display_map = {
            "implements appropriate technical and organizational measures": "Implements appropriate technical and organizational measures to ensure compliance with DPDPA.",
            "maintains data accuracy and completeness": "Maintains data accuracy and completeness to ensure it is up-to-date.",
            "implements reasonable security safeguards": "Implements reasonable security safeguards to prevent personal data breaches.",
            "notifies the data protection board and affected data principals in case of breach": "Notifies the Data Protection Board and affected Data Principals in the event of a breach.",
            "erases personal data when purpose is fulfilled": "Erases personal data as soon as the purpose is fulfilled and retention is no longer necessary.",
            "maintains records of processing activities": "Maintains records of processing activities in accordance with prescribed rules.",
            "conducts data protection impact assessments": "Conducts periodic Data Protection Impact Assessments if required.",
            "appoints a data protection officer": "Appoints a Data Protection Officer (DPO) if classified as a Significant Data Fiduciary.",
            "publishes dpo contact information": "Publishes the business contact information of the DPO or person handling grievances."
        }
    else:
        canonical_display_map = {}

    for res in all_results:
        for item in res.get("Checklist Evaluation", []):
            key = item["Checklist Item"].strip().lower().replace(".", "")

            if section_id == "8":
                for match in canonical_display_map.keys():
                    if match in key:
                        key = match
                        break

            if "all other checklist items" in key:
                continue

            if key not in matched_items:
                item["Checklist Item"] = canonical_display_map.get(key, item["Checklist Item"])
                matched_items[key] = item

    evaluations = list(matched_items.values())
    score, level = compute_score_and_level(evaluations, len(checklist))

    return {
        "Section": section_id,
        "Title": dpdpa_checklists[section_id]['title'],
        "Match Level": level,
        "Compliance Score": score,
        "Checklist Items Matched": [item["Checklist Item"] for item in evaluations],
        "Matched Details": evaluations,
        "Suggested Rewrite": all_results[0].get("Suggested Rewrite", ""),
        "Simplified Legal Meaning": all_results[0].get("Simplified Legal Meaning", "")
    }
    
def set_custom_css():
    st.markdown("""
    <style>
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #2E2E38;
        color: white !important;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Main text and headers */
    section.main div.block-container {
        color: #2E2E38 !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #2E2E38 !important;
    }

    /* Fix for input text color */
    input, textarea, select, div[role="textbox"] {
        color: #2E2E38 !important;
        caret-color: #2E2E38
    }

    /* Fix for selectbox and dropdowns */
    .stSelectbox div, .stRadio div, .stCheckbox div, .stTextInput div, .stDownloadButton div {
        color: #2E2E38 !important;
    }

    /* Fix file uploader text inside black box */
    .stFileUploader div, .stFileUploader span {
    color: white !important;
    }
    /* --- Force white text in selectbox/multiselect dropdowns with dark bg --- */
    div[data-baseweb="select"] {
        color: white !important;
    }
    
    div[data-baseweb="select"] * {
        color: white !important;
    }


    /* Fix Browse files button text inside file uploader */
    .stFileUploader button,
    .stFileUploader label {
    color: black !important;
    font-weight: 500;
    }

    /* Fix download and regular buttons */
    .stButton > button, .stDownloadButton > button {
        color: white !important;
        background-color: #1a9afa;
        font-weight: 600;
        border-radius: 6px;
        border: none;
    }
    
        
    /* Only for actual input and textarea fields */
    input, textarea {
        background-color: #FFFFFF !important;
        color: #2E2E38 !important;
        border: 1px solid #2E2E38 !important;
        border-radius: 6px !important;
        caret-color: #2E2E38
    }
    /* Additional fix for Streamlit's internal markdown editor (if used) */
    div[contenteditable="true"] {
        caret-color: #2E2E38 !important;
        color: #2E2E38 !important;
    }

    
    /* For Streamlit selectboxes */
    div[data-baseweb="select"] {
        background-color: #2E2E38 !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
    }
    div[data-baseweb="select"] * {
        color: white !important;
    }

    /* === Fix Streamlit checkbox visibility === */
    div[data-baseweb="checkbox"] > label > div {
        background-color: white !important;
        border: 2px solid #2E2E38 !important;
        border-radius: 4px !important;
        width: 20px !important;
        height: 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-right: 10px !important;
    }
    
    /* Show checkmark when selected */
    div[data-baseweb="checkbox"] svg {
        stroke: #2E2E38 !important;
        stroke-width: 2.5px !important;
    }
    /* === FIX: Cursor visibility in text areas === */
    textarea,
    .stTextArea textarea,
    div[role="textbox"],
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #2E2E38 !important;
        caret-color: #2E2E38 !important;
        border: 1px solid #2E2E38 !important;
        border-radius: 6px !important;
    }
    
    /* Explicit caret fix for editable areas */
    div[contenteditable="true"] {
        caret-color: #2E2E38 !important;
        color: #2E2E38 !important;
    }

    /* Force DataFrame cell background and text to be readable */
.css-1r6slb0 .element-container {
        background-color: white !important;
        color: black !important;
    }


    </style>
    """, unsafe_allow_html=True)

# --- Sidebar Navigation ---
st.set_page_config(page_title="DPDPA Compliance Tool", layout="wide")
set_custom_css()
st.sidebar.markdown("<h1 style='font-size:42px; font-weight:700;'>Navigation</h1>", unsafe_allow_html=True)

menu = st.sidebar.radio("", [
    "Homepage",
    "Policy Compliance Checker",
    "Policy Generator",
    "Dashboard & Reports",
    "Knowledge Assistant",
    "Admin Settings"
])
st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
#st.sidebar.image(".images/EY-Parthenon_idpWq1a8hl_0.png", width=250)
st.sidebar.markdown("""
    <div style='padding: 0px 12px 0px 0px;'>
        <img src='https://i.postimg.cc/j2dv9kZ2/EY-Parthenon-idp-Wq1a8hl-0.png' width='200'>
    </div>
""", unsafe_allow_html=True)
# --- Homepage ---
if menu == "Homepage":
    st.title("DPDPA Compliance Tool")
    st.markdown("""
    Welcome to the Digital Personal Data Protection Act (DPDPA) Compliance Platform.
    Use the navigation panel to begin generating or matching your policy to India's latest data protection laws.
    """)

# --- Policy Generator ---
elif menu == "Policy Generator":
    st.title("Create a new Policy")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Full Policy Generator", "Section-wise Generator", "Lifecycle-wise Template", 
        "GPT Draft Assistant", "Saved Drafts"])

    with tab1:
        st.subheader("Full Policy Generator")
        st.text_area("Enter your complete policy draft:", height=300)
        st.button("Generate Suggestions with GPT")

    with tab2:
        st.subheader("Section-wise Generator")
        section = st.selectbox("Choose Section", ["Notice", "Consent", "Data Principal Rights", "Security"])
        st.text_area(f"Draft for {section}:", height=200)
        st.button("Suggest Completion")

    with tab3:
        st.subheader("Lifecycle-wise Template")
        st.markdown("Fill stage-specific privacy info:")
        stages = ["Collection", "Processing", "Storage", "Sharing", "Erasure"]
        for stage in stages:
            st.text_area(f"{stage} Stage", key=stage)

    with tab4:
        st.subheader("GPT-Assisted Draft Builder")
        prompt = st.text_input("Describe your need (e.g. privacy for HR data):")
        st.button("Generate Draft")

    with tab5:
        st.subheader("Saved Drafts")
        st.dataframe({"Draft": ["HR Policy", "Marketing Policy"], "Last Modified": ["2025-05-10", "2025-05-01"]})

# --- Policy Compliance Checker ---
elif menu == "Policy Compliance Checker":
    #st.title("Match Policy to DPDPA")
    st.markdown("<h1 style='font-size:38px; font-weight:800;'>Match Policy to DPDPA</h1>", unsafe_allow_html=True)
    
    #st.header("1. Upload Your Policy Document")
    st.markdown("<h3 style='font-size:24px; font-weight:700;'>1. Upload Your Policy Document</h3>", unsafe_allow_html=True)

    upload_option = st.radio("Choose input method:", ["Paste text", "Upload PDF"])
    if upload_option == "Paste text":
        policy_text = st.text_area("Paste your Privacy Policy text:", height=300)
    elif upload_option == "Upload PDF":
        uploaded_pdf = st.file_uploader("Upload PDF file", type="pdf")
        if uploaded_pdf:
            policy_text = extract_text_from_pdf(uploaded_pdf)
        else:
            policy_text = ""

    #st.header("2. Choose Matching Level")
    st.markdown("<h3 style='font-size:24px; font-weight:700;'>2. Choose Matching Level</h3>", unsafe_allow_html=True)
    match_level = st.radio("How do you want to match?", [
        "Document-level Match (default)", "Clause-level Match"], index=0)

    #st.header("3. Select Scope of Evaluation")
    st.markdown("<h3 style='font-size:24px; font-weight:700;'>3. Select Scope of Evaluation</h3>", unsafe_allow_html=True)
    scope = st.selectbox("", [
        "DPDP Act 2023 (default)", "DPDP Rules 2025", "DPDP Act + Rules", "Custom Sections"], index=0)
    if scope == "Custom Sections":
        custom_sections = st.multiselect("Select specific sections to match against", [
        "Section 4 — Grounds for Processing Personal Data", "Section 5 — Notice", "Section 6 — Consent", "Section 7 — Certain Legitimate Uses",
        "Section 8 — General Obligations of Data Fiduciary"])
    else:
        custom_sections = []

    #st.header("4. Industry Context (Optional)")
    st.markdown("<h3 style='font-size:24px; font-weight:700;'>4. Industry Context (Optional)</h3>", unsafe_allow_html=True)
    industry = st.selectbox("", ["General", "Automotive", "Healthcare", "Fintech", "Other"])
    if industry == "Other":
        custom_industry = st.text_input("Specify your industry")
    else:
        custom_industry = None

    section_options = list(dpdpa_checklists.keys()) + ["All Sections"]
    section_id = st.selectbox("Choose DPDPA Section", options=section_options)

    st.markdown("<h3 style='font-size:24px; font-weight:700;'>5. Run Compliance Check</h3>", unsafe_allow_html=True)
    if st.button("Run Compliance Check"):
        if policy_text:
            results = []
            with st.spinner("Running GPT-based compliance evaluation..."):
                if section_id == "All Sections":
                    for sid in dpdpa_checklists:
                        st.markdown(f"### Section {sid} — {dpdpa_checklists[sid]['title']}")
                        result = analyze_policy_section(sid, dpdpa_checklists[sid]['items'], policy_text)
                        with st.expander(f"Section {result['Section']} — {result['Title']}", expanded=True):
                            # Set color for Match Level badge
                            level_color = {
                                "Fully Compliant": "#198754",     # green
                                "Partially Compliant": "#FFC107", # yellow
                                "Non-Compliant": "#DC3545"        # red
                            }
                            match_level = result["Match Level"]
                            color = level_color.get(match_level, "#6C757D")  # fallback grey
                            
                            st.markdown(f"""
                            <div style="margin-bottom: 1rem;">
                              <b>Compliance Score:</b>
                              <span style="background-color:#0d6efd; color:white; padding:4px 10px; border-radius:5px; font-size:0.85rem;">
                                {result["Compliance Score"]}
                              </span><br>
                              <b>Match Level:</b>
                              <span style="background-color:{color}; color:black; padding:4px 10px; border-radius:5px; font-size:0.85rem;">
                                {match_level}
                              </span>
                            </div>

                        
                            st.markdown("### 📋 Checklist Items Matched:")
                            for i, item in enumerate(result["Checklist Items Matched"]):
                                st.markdown(f"- {item}")
                        
                            st.markdown("### 🔍 Matched Details:")
                            for detail in result["Matched Details"]:
                                st.markdown(f"** {detail['Checklist Item']}** — `{detail['Status']}`  \n> _{detail['Justification']}_")
                                status_color = {
                                    "explicitly mentioned": "#198754",  # green
                                    "partially mentioned": "#FFC107",   # yellow
                                    "missing": "#DC3545"                # red
                                }
                                
                                for detail in result["Matched Details"]:
                                    status = detail["Status"]
                                    status_key = status.lower()
                                    color = status_color.get(status_key, "#6C757D")  # fallback grey
                                
                                    st.markdown(f"""
                                    <div style="margin-bottom: 1rem;">
                                        <b>• {detail['Checklist Item']}</b>
                                        <span style="background-color:{color}; color:white; padding:2px 6px; border-radius:5px; font-size:0.85em;">
                                            {status}
                                        </span><br>
                                        <i style="color:#555;">{detail['Justification']}</i>
                                    </div>
                                    """, unsafe_allow_html=True)

                        
                            st.markdown("### ✏️ Suggested Rewrite:")
                            st.info(result["Suggested Rewrite"])
                        
                            st.markdown("### 🧾 Simplified Legal Meaning:")
                            st.success(result["Simplified Legal Meaning"])

                        st.markdown("---")
                else:
                    checklist = dpdpa_checklists[section_id]['items']
                    result = analyze_policy_section(section_id, checklist, policy_text)
                    with st.expander(f"Section {result['Section']} — {result['Title']}", expanded=True):
                        # Set color for Match Level badge
                        level_color = {
                            "Fully Compliant": "#198754",     # green
                            "Partially Compliant": "#FFC107", # yellow
                            "Non-Compliant": "#DC3545"        # red
                        }
                        match_level = result["Match Level"]
                        color = level_color.get(match_level, "#6C757D")  # fallback grey
                        
                        st.markdown(f"""
                        <div style="margin-bottom: 1rem;">
                          <b>Compliance Score:</b>
                          <span style="background-color:#0d6efd; color:white; padding:4px 10px; border-radius:5px; font-size:0.85rem;">
                            {result["Compliance Score"]}
                          </span><br>
                          <b>Match Level:</b>
                          <span style="background-color:{color}; color:black; padding:4px 10px; border-radius:5px; font-size:0.85rem;">
                            {match_level}
                          </span>
                        </div>

                    
                        st.markdown("### 📋 Checklist Items Matched:")
                        for i, item in enumerate(result["Checklist Items Matched"]):
                            st.markdown(f"- {item}")
                    
                        st.markdown("### 🔍 Matched Details:")
                        for detail in result["Matched Details"]:
                            status_color = {
                                "explicitly mentioned": "#198754",  # green
                                "partially mentioned": "#FFC107",   # yellow
                                "missing": "#DC3545"                # red
                            }
                            
                            for detail in result["Matched Details"]:
                                status = detail["Status"]
                                status_key = status.lower()
                                color = status_color.get(status_key, "#6C757D")  # fallback grey
                            
                                st.markdown(f"""
                                <div style="margin-bottom: 1rem;">
                                    <b>• {detail['Checklist Item']}</b>
                                    <span style="background-color:{color}; color:white; padding:2px 6px; border-radius:5px; font-size:0.85em;">
                                        {status}
                                    </span><br>
                                    <i style="color:#555;">{detail['Justification']}</i>
                                </div>
                                """, unsafe_allow_html=True)

                    
                        st.markdown("### ✏️ Suggested Rewrite:")
                        st.info(result["Suggested Rewrite"])
                    
                        st.markdown("### 🧾 Simplified Legal Meaning:")
                        st.success(result["Simplified Legal Meaning"])

