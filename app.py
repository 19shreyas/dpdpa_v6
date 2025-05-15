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
    "4 - Grounds for Processing Personal Data": {
        "title": "Grounds for Processing Personal Data",
        "items": [
            "The policy must state that personal data is processed **only as per the provisions of the Digital Personal Data Protection Act, 2023**.",
            "The policy must confirm that personal data is processed **only for a lawful purpose**.",
            "The policy must define **lawful purpose** as any purpose **not expressly forbidden by law**.",
            "The policy must include a statement that personal data is processed **only with the consent of the Data Principal**.",
            "Alternatively, the policy must specify that personal data is processed **for certain legitimate uses**, as defined under the Act."
        ]
    },
    "5 - Notice": {
        "title": "Notice",
        "items": [
            section_5_checklist = [
            "The policy must state that **every request for consent** is accompanied or preceded by a **notice from the Data Fiduciary to the Data Principal**.",
            "The notice must clearly specify the **personal data proposed to be processed**.",
            "The notice must clearly specify the **purpose for which the personal data is proposed to be processed**.",
            "The notice must explain the **manner in which the Data Principal can exercise her rights under Section 6(4)** (withdrawal of consent).",
            "The notice must explain the **manner in which the Data Principal can exercise her rights under Section 13** (grievance redressal).",
            "The notice must specify the **manner in which a complaint can be made to the Data Protection Board**.",
            "If consent was obtained **before the commencement of the Act**, the policy must state that a notice will be sent **as soon as reasonably practicable**.",
            "The post-commencement notice must mention the **personal data that has been processed**.",
            "The post-commencement notice must mention the **purpose for which the personal data has been processed**.",
            "The post-commencement notice must mention the **manner in which the Data Principal can exercise her rights under Section 6(4)**.",
            "The post-commencement notice must mention the **manner in which the Data Principal can exercise her rights under Section 13**.",
            "The post-commencement notice must mention the **manner in which a complaint can be made to the Board**.",
            "The policy must mention that the Data Fiduciary **may continue to process personal data** until the Data Principal **withdraws her consent**.",
            "The policy must provide the Data Principal an **option to access the contents of the notice** in **English or any language listed in the Eighth Schedule of the Constitution**."
        ]
    },
    "6 - Consent": {
        "title": "Consent",
        "items": [
            "The policy must state that **consent is free, specific, informed, unconditional, and unambiguous**, given through a **clear affirmative action**.",
            "The policy must specify that **consent signifies agreement to process personal data only for the specified purpose**.",
            "The policy must state that **consent is limited to such personal data as is necessary for the specified purpose**.",
            "The policy must mention that **any part of the consent that violates this Act, rules under it, or any other law in force is invalid to that extent**.",
            "The request for consent must be presented in **clear and plain language**.",
            "The request for consent must allow the Data Principal to access it in **English or any language listed in the Eighth Schedule of the Constitution**.",
            "The request for consent must provide **contact details of a Data Protection Officer** or **another authorised person** responsible for handling Data Principal queries.",
            "The policy must clearly state that the **Data Principal has the right to withdraw consent at any time**.",
            "The **ease of withdrawing consent** must be comparable to the **ease with which consent was given**.",
            "The policy must mention that **consequences of withdrawal shall be borne by the Data Principal**.",
            "The policy must state that **withdrawal does not affect the legality of data processing done before withdrawal**.",
            "The policy must mention that upon withdrawal of consent, the **Data Fiduciary and its Data Processors must cease processing** the personal data **within a reasonable time**, unless permitted by law.",
            "The policy must state that consent **can be managed, reviewed, or withdrawn through a Consent Manager**.",
            "The policy must specify that the **Consent Manager is accountable to the Data Principal** and acts on her behalf.",
            "The policy must specify that **every Consent Manager is registered with the Board** under prescribed conditions.",
            "The policy must mention that, in case of dispute, the **Data Fiduciary must prove that proper notice was given and valid consent was obtained** as per the Act and its rules."
        ]
    },
    "7 - Certain Legitimate Uses": {
        "title": "Certain Legitimate Uses",
        "items": [
            "The policy must allow personal data to be processed for the **specified purpose for which the Data Principal voluntarily provided the data**, if she has **not indicated non-consent** to such use.",
            "The policy must permit personal data to be processed by the State or its instrumentalities for providing or issuing **subsidy, benefit, service, certificate, licence, or permit**, as prescribed, where the Data Principal has **previously consented** to such processing.",
            "The policy must allow personal data to be processed by the State or its instrumentalities if the data is **already available in digital or digitised form in notified government databases**, subject to prescribed standards and government policies.",
            "The policy must allow personal data to be processed by the State or its instrumentalities for performing any **legal function** under existing Indian laws or **in the interest of sovereignty and integrity of India or State security**.",
            "The policy must allow personal data to be processed to **fulfil a legal obligation** requiring any person to disclose information to the State or its instrumentalities, as per applicable laws.",
            "The policy must permit personal data to be processed for **compliance with any judgment, decree, or order** issued under Indian law, or for **contractual or civil claims under foreign laws**.",
            "The policy must allow personal data to be processed to **respond to a medical emergency** involving a **threat to life or immediate health risk** of the Data Principal or any individual.",
            "The policy must allow personal data to be processed to **provide medical treatment or health services** during an **epidemic, outbreak, or other threat to public health**.",
            "The policy must permit processing of personal data to **ensure safety of or provide assistance/services to individuals** during any **disaster or breakdown of public order**.",
            "The policy must define 'disaster' in accordance with the **Disaster Management Act, 2005 (Section 2(d))**.",
            "The policy must allow personal data to be processed for purposes related to **employment**, or to **safeguard the employer from loss or liability**, including prevention of corporate espionage, confidentiality of trade secrets or IP, and enabling services/benefits to employee Data Principals."
        ]
    },
    "8 - General Obligations of Data Fiduciary": {
        "title": "General Obligations of Data Fiduciary",
        "items": [
            "The policy must state that the Data Fiduciary is responsible for complying with the Act and its rules, even if the Data Principal fails to perform her duties.",
            "The policy must state that the Data Fiduciary may engage or involve a Data Processor **only under a valid contract** to process personal data for offering goods or services.",
            "The policy must ensure that if personal data is used to make a decision affecting the Data Principal, the data must be **complete, accurate, and consistent**.",
            "The policy must ensure that if personal data is disclosed to another Data Fiduciary, the data must be **complete, accurate, and consistent**.",
            "The policy must require the Data Fiduciary to implement **appropriate technical and organisational measures** to ensure compliance with the Act and its rules.",
            "The policy must mandate **reasonable security safeguards** to protect personal data from breaches, including breaches by its Data Processors.",
            "The policy must state that in the event of a **personal data breach**, the Data Fiduciary shall **inform both the Board and each affected Data Principal** in the prescribed manner.",
            "The policy must mandate that personal data be **erased upon withdrawal of consent** or as soon as it is reasonable to assume that the **specified purpose is no longer being served**, whichever is earlier.",
            "The policy must mandate that the Data Fiduciary must **cause its Data Processors to erase the data** when retention is no longer justified.",
            "The policy must define that the specified purpose is deemed no longer served if the Data Principal has neither **approached the Data Fiduciary for the purpose** nor **exercised her rights** within the prescribed time period.",
            "The policy must require publishing the **business contact details** of the Data Protection Officer (if applicable) or of an authorised person able to respond to questions about personal data processing.",
            "The policy must provide an **effective grievance redressal mechanism** for Data Principals.",
            "The policy must clarify that a Data Principal is considered as **not having approached** the Data Fiduciary if she has not initiated contact in person, or through physical or electronic communication, for the purpose within a prescribed period."
        ]
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
                            level_color = {
                                "Fully Compliant": "#198754",
                                "Partially Compliant": "#FFC107",
                                "Non-Compliant": "#DC3545"
                            }
                            match_level = result["Match Level"]
                            color = level_color.get(match_level, "#6C757D")
    
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
                            """, unsafe_allow_html=True)
    
                            st.markdown("### 📋 Checklist Items Matched:")
                            for i, item in enumerate(result["Checklist Items Matched"]):
                                st.markdown(f"- {item}")
    
                            st.markdown("### 🔍 Matched Details:")
                            status_color = {
                                "explicitly mentioned": "#198754",
                                "partially mentioned": "#FFC107",
                                "missing": "#DC3545"
                            }
                            for detail in result["Matched Details"]:
                                status = detail["Status"]
                                status_key = status.lower()
                                color = status_color.get(status_key, "#6C757D")
                                text_color = "white" if color.strip().lower() in ["#198754", "#dc3545"] else "black"
    
                                st.markdown(f"""
                                <div style="margin-bottom: 1rem;">
                                    <b>• {detail['Checklist Item']}</b>
                                    <span style="background-color:{color}; color:{text_color}; padding:2px 6px; border-radius:5px; font-size:0.85rem;">
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
                        level_color = {
                            "Fully Compliant": "#198754",
                            "Partially Compliant": "#FFC107",
                            "Non-Compliant": "#DC3545"
                        }
                        match_level = result["Match Level"]
                        color = level_color.get(match_level, "#6C757D")
    
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
                        """, unsafe_allow_html=True)
    
                        st.markdown("### 📋 Checklist Items Matched:")
                        for i, item in enumerate(result["Checklist Items Matched"]):
                            st.markdown(f"- {item}")
    
                        st.markdown("### 🔍 Matched Details:")
                        status_color = {
                            "explicitly mentioned": "#198754",
                            "partially mentioned": "#FFC107",
                            "missing": "#DC3545"
                        }
                        for detail in result["Matched Details"]:
                            status = detail["Status"]
                            status_key = status.lower()
                            color = status_color.get(status_key, "#6C757D")
                            text_color = "white" if color.strip().lower() in ["#198754", "#dc3545"] else "black"
    
    
                            st.markdown(f"""
                            <div style="margin-bottom: 1rem;">
                                <b>• {detail['Checklist Item']}</b>
                                <span style="background-color:{color}; color:{text_color}; padding:2px 6px; border-radius:5px; font-size:0.85rem;">
                                    {status}
                                </span><br>
                                <i style="color:#555;">{detail['Justification']}</i>
                            </div>
                            """, unsafe_allow_html=True)
    
                        st.markdown("### ✏️ Suggested Rewrite:")
                        st.info(result["Suggested Rewrite"])
                        
                        st.markdown("### 🧾 Simplified Legal Meaning:")
                        st.success(result["Simplified Legal Meaning"])
