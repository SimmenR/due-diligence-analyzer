import streamlit as st
import PyPDF2
import time
import google.generativeai as genai

st.set_page_config(page_title="M&A Due Diligence Agent", layout="wide")
st.title("Due Diligence & Risk Analyzer 📊")

st.sidebar.header("Settings")
# Dropdown to select the engine
model_choice = st.sidebar.selectbox("Select AI Engine", ["Google Gemini (Free)", "Demo Mode (Offline)"], index=0)

# Only enable the API key input if we aren't in Demo Mode
needs_key = model_choice != "Demo Mode (Offline)"
if needs_key:
    st.sidebar.markdown(
        "You can get a **free** Gemini API key from "
        "[Google AI Studio](https://aistudio.google.com/apikey): sign in with a Google account, "
        "open **Get API key**, and create a key for this app."
    )
api_key = st.sidebar.text_input("Enter API Key", type="password", disabled=not needs_key)

st.write("Upload a target company's financial report or pitch deck (PDF) to generate a Due Diligence summary.")

uploaded_file = st.file_uploader("Upload Target Company PDF", type="pdf")

# This is the strict template we force the AI to fill out
SYSTEM_PROMPT = """
You are a Senior M&A Transaction Services Director at a Big 4 firm. 
Analyze the provided financial document and extract insights strictly using the following Markdown format. 
Do NOT add introductory or concluding text. Be concise, professional, and focus on hard financial metrics, risks, and EBITDA adjustments.

### 1. Quality of Earnings (QoE)
* **Top-Line Quality & Revenue Mix:** [Analyze revenue growth vs volume, pricing power, and shift in business models e.g., Wholesale vs. Agency]
* **Reported vs. Adjusted EBITDA:** [Identify specific add-backs and non-recurring expenses to derive Normalized EBITDA]
* **Net Working Capital (NWC) Trends:** [Analyze DSO, DPO, inventory turnover, and cash conversion cycle]

### 2. Net Debt & Debt-Like Items
* **CapEx Requirements:** [Analyze Maintenance vs. Growth CapEx, and compare to D&A]
* **Adjusted Net Debt Position:** [Calculate total debt including hidden liabilities like operating leases, reverse factoring, and pension deficits, minus cash]
* **Covenant & Impairment Risks:** [Identify covenant headroom and risks of goodwill or asset impairment]

### 3. Deal Strategy & Valuation Implications
* **Enterprise Value (EV) to Equity Value Bridge:** [Explain how the adjusted debt and NWC positions will impact the final purchase price]
* **Phase 2 FDD Focus Areas:** [List the top 3 immediate red flags or areas requiring deep-dive forensic analysis in the next stage of due diligence]
"""


def pick_gemini_model():
    """Pick the best available Gemini model for text generation."""
    preferred = [
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash",
        "models/gemini-1.0-pro",
    ]
    available = [
        m.name
        for m in genai.list_models()
        if "generateContent" in getattr(m, "supported_generation_methods", [])
    ]
    for name in preferred:
        if name in available:
            return name, available
    return (available[0] if available else None), available


def list_gemini_generate_models():
    """Return Gemini models that support text generation."""
    return sorted(
        [
            m.name
            for m in genai.list_models()
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]
    )


selected_gemini_model = None
if model_choice == "Google Gemini (Free)" and api_key:
    try:
        genai.configure(api_key=api_key)
        gemini_models = list_gemini_generate_models()
        if gemini_models:
            default_model, _ = pick_gemini_model()
            default_index = gemini_models.index(default_model) if default_model in gemini_models else 0
            selected_gemini_model = st.sidebar.selectbox(
                "Gemini model",
                options=gemini_models,
                index=default_index,
                help="Models returned by list_models() that support generateContent.",
            )
        else:
            st.sidebar.warning("No compatible Gemini text-generation model was found for this key.")
    except Exception as e:
        st.sidebar.warning(f"Could not fetch Gemini model list: {e}")

if uploaded_file:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
        
    st.success(f"PDF loaded successfully! ({len(text)} characters read)")
    
    if st.button("Run Financial Due Diligence"):
        
        # --- DEMO MODE ---
        if model_choice == "Demo Mode (Offline)":
            with st.spinner("Demo Mode: Simulating financial extraction..."):
                time.sleep(2) 
                st.markdown("""
                ### 1. Quality of Earnings (QoE)
                * **Top-Line Quality & Revenue Mix:** Top-line growth of 8.4% YoY is driven entirely by price hikes, not volume. The shift from Wholesale to Agency models introduces margin volatility.
                * **Reported vs. Adjusted EBITDA:** Identified €4.2M in non-recurring legal expenses and severance packages to add back, deriving a higher Normalized EBITDA.
                * **Net Working Capital (NWC) Trends:** DSO improved to 38 days, but inventory turnover has slowed by 14%, tying up excess cash in operations.
                
                ### 2. Net Debt & Debt-Like Items
                * **CapEx Requirements:** Growth CapEx spiked 22% YoY due to delayed IT modernization, far exceeding historical D&A levels.
                * **Adjusted Net Debt Position:** Found €1.2M in unpaid holiday accruals and €3.5M in operating leases that must be treated as debt-like items.
                * **Covenant & Impairment Risks:** Operating dangerously close to the Net Debt/EBITDA covenant limit of 3.5x (currently 3.2x). No immediate goodwill impairment risk identified.
                
                ### 3. Deal Strategy & Valuation Implications
                * **Enterprise Value (EV) to Equity Value Bridge:** Normalizing EBITDA increases the initial Enterprise Value, but the €4.7M in combined debt-like items will be deducted dollar-for-dollar from the final Equity Value.
                * **Phase 2 FDD Focus Areas:** Urgent forensic focus needed on the aging inventory ledger and the sustainability of the recent pricing strategy.
                """)
                
        # --- GOOGLE GEMINI ---
        elif model_choice == "Google Gemini (Free)" and api_key:
            try:
                genai.configure(api_key=api_key)
                model_name = selected_gemini_model
                if not model_name:
                    model_name, _ = pick_gemini_model()
                if not model_name:
                    st.error("No Gemini text-generation model is available for this API key/project.")
                    st.stop()
                st.caption(f"Using Gemini model: `{model_name}`")
                model = genai.GenerativeModel(model_name)
                with st.spinner("Gemini is analyzing the document..."):
                    full_prompt = f"{SYSTEM_PROMPT}\n\nDocument Text:\n{text[:1000000]}"
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"API Error: {e}")

        else:
            st.warning("Please enter an API Key for live analysis, or select Demo Mode.")