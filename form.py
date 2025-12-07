import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from fpdf import FPDF
from io import BytesIO

# -------------------- GOOGLE SHEET CONNECTION --------------------
def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Coding_Club_Registrations").sheet1
    return sheet


# -------------------- HELPERS --------------------
def get_next_serial(sheet):
    """Serial No = number of existing data rows + 1 (skip header)."""
    records = sheet.get_all_records()
    return len(records) + 1


def is_duplicate_reg(sheet, reg_no):
    """Check if Register No already exists (col C = 3rd column)."""
    all_values = sheet.col_values(3)
    existing_regs = all_values[1:]   # skip header
    return reg_no in existing_regs


def fetch_df(sheet):
    """Get full sheet as DataFrame."""
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=[
            "Serial No", "Name", "Register No", "Email", "Mobile",
            "Gender", "Stay Type", "Department", "Interests", "Languages"
        ])
    return pd.DataFrame(data)


def get_excel_bytes(df: pd.DataFrame) -> BytesIO:
    """Convert DataFrame to Excel bytes for download."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Members")
    output.seek(0)
    return output


def get_pdf_bytes(df: pd.DataFrame) -> BytesIO:
    """Convert DataFrame to a simple PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Coding Club Members", ln=True, align="C")
    pdf.ln(5)

    # Table Header
    pdf.set_font("Arial", "B", 10)
    for col in df.columns:
        pdf.cell(40, 8, str(col)[:18], border=1)
    pdf.ln(8)

    # Rows
    pdf.set_font("Arial", "", 9)
    for _, row in df.iterrows():
        for item in row:
            text = str(item)
            if len(text) > 30:
                text = text[:27] + "..."
            pdf.cell(40, 8, text, border=1)
        pdf.ln(8)

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return BytesIO(pdf_bytes)


# -------------------- GLOBAL UI STYLING --------------------
st.set_page_config(page_title="Coding Club Registration", layout="centered")

st.markdown("""
<style>
.title{
    font-size:40px;
    font-weight:800;
    text-align:center;
    color:#00eaff;
    margin-bottom:-10px;
}
.subtitle{
    text-align:center;
    font-size:18px;
    color:#cccccc;
    margin-bottom:20px;
}
.stButton button{
    background-color:#00eaff;
    color:black;
    border-radius:8px;
    font-weight:600;
    padding:8px 16px;
}
</style>
""", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
mode = st.sidebar.radio("Mode", ["Registration Form", "Admin / Downloads"])


# -------------------- REGISTRATION FORM --------------------
if mode == "Registration Form":
    st.markdown("<p class='title'>CODING CLUB - Application Form</p>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Our Coding Club warmly welcomes You 🤝</p>", unsafe_allow_html=True)

    with st.form("Coding_Club_Form"):
        name = st.text_input("Name")
        reg_no = st.text_input("Register No.")
        email = st.text_input("Email ID")
        ph_no = st.text_input("Mobile Number")

        gen = st.radio("Gender", ["Male", "Female"])
        stay = st.radio("Stay Type", ["Hostel", "Day-Scholar"])
        dept = st.selectbox("Department", ["CSE", "AI"])

        interest = st.multiselect(
            "Interested Area",
            ["AI", "DSA Problem solving", "Full Stack", "I'm exploring.."]
        )

        language = st.multiselect(
            "Known Programming Languages",
            ["Python", "C", "C++", "Java", "HTML/CSS", "Others"]
        )

        submit = st.form_submit_button("Submit")

    if submit:
        if not name or not reg_no or not email or not ph_no:
            st.error("❌ Please complete all mandatory fields.")
        else:
            sheet = connect_sheet()

            if is_duplicate_reg(sheet, reg_no):
                st.error("❌ This Register Number is already registered.")
            else:
                serial_no = get_next_serial(sheet)

                sheet.append_row([
                    serial_no,
                    name,
                    reg_no,
                    email,
                    ph_no,
                    gen,
                    stay,
                    dept,
                    ", ".join(interest),
                    ", ".join(language)
                ])

                st.success("✅ Registration Successful! 🎉")
                st.info("Your details have been saved to Google Sheets.")

                st.markdown("### Applicant Summary")
                st.write(f"**Serial No:** {serial_no}")
                st.write(f"**Name:** {name}")
                st.write(f"**Register Number:** {reg_no}")
                st.write(f"**Email ID:** {email}")
                st.write(f"**Mobile Number:** {ph_no}")
                st.write(f"**Gender:** {gen}")
                st.write(f"**Stay Type:** {stay}")
                st.write(f"**Department:** {dept}")
                st.write(f"**Interests:** {', '.join(interest)}")
                st.write(f"**Languages Known:** {', '.join(language)}")


# -------------------- ADMIN / DOWNLOADS --------------------
else:
    st.markdown("<p class='title'>CODING CLUB - Admin Panel</p>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>View all members & download files 📊</p>", unsafe_allow_html=True)

    sheet = connect_sheet()
    df = fetch_df(sheet)

    if df.empty:
        st.warning("No registrations yet.")
    else:
        st.subheader("Members List")
        st.dataframe(df, use_container_width=True)
        st.write(f"**Total Members:** {len(df)}")

        # Excel Download
        excel_bytes = get_excel_bytes(df)
        st.download_button(
            "⬇️ Download Excel",
            data=excel_bytes,
            file_name="coding_club_members.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # PDF Download
        pdf_bytes = get_pdf_bytes(df)
        st.download_button(
            "⬇️ Download PDF",
            data=pdf_bytes,
            file_name="coding_club_members.pdf",
            mime="application/pdf"
        )
