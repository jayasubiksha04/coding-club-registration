import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from io import BytesIO

# ....................................................
# 🔗 CONNECT TO GOOGLE SHEET USING STREAMLIT SECRETS
# ....................................................
def connect_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("Coding Club Registrations").sheet1
    return sheet


sheet = connect_sheet()


# ....................................................
# 📌 GET DATA AS DATAFRAME
# ....................................................
def get_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)


# ....................................................
# 🔢 GENERATE SERIAL NUMBER
# ....................................................
def get_next_serial():
    df = get_data()
    if df.empty:
        return 1
    return int(df["Serial No"].max()) + 1


# ....................................................
# ❌ CHECK DUPLICATE REGISTER NUMBER
# ....................................................
def is_duplicate(register_no):
    df = get_data()
    return register_no in df["Register No"].astype(str).values


# ....................................................
# 📝 SAVE NEW RESPONSE
# ....................................................
def save_form(data):
    sheet.append_row(data)


# ....................................................
# 📄 DOWNLOAD AS PDF
# ....................................................
def generate_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for i, row in df.iterrows():
        text = f"{row['Serial No']}. {row['Name']} | {row['Register No']} | {row['Email']} | {row['Department']}"
        pdf.multi_cell(0, 10, txt=text)

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer


# ====================================================
# 🖥️ STREAMLIT UI
# ====================================================
st.sidebar.title("Mode")
mode = st.sidebar.radio("", ["Registration Form", "Admin / Downloads"])

# ....................................................
# 🧾 REGISTRATION FORM
# ....................................................
if mode == "Registration Form":
    st.title("CODING CLUB - Application Form")
    st.markdown("Our Coding Club warmly welcomes you 🤝")

    name = st.text_input("Name")
    register_no = st.text_input("Register No")
    email = st.text_input("Email ID")
    mobile = st.text_input("Mobile Number")

    gender = st.radio("Gender", ["Male", "Female"])

    department = st.selectbox("Department", ["CSE", "AI&DS", "IT", "ECE", "EEE", "MECH", "CIVIL"])

    skills = st.text_area("Skills (AI, Python, DSA, Web, etc.)")

    if st.button("Submit"):
        if not name or not register_no or not email:
            st.error("Please fill all required fields!")
        else:
            if is_duplicate(register_no):
                st.error("❌ Register Number already exists!")
            else:
                serial = get_next_serial()
                row = [serial, name, register_no, email, mobile, gender, department, skills]
                save_form(row)
                st.success("🎉 Successfully Registered!")


# ....................................................
# 🔐 ADMIN PAGE
# ....................................................
else:
    st.title("Admin Panel")

    password = st.text_input("Enter Admin Password", type="password")

    if password == "admin123":   # CHANGE your password here
        st.success("Logged in!")

        df = get_data()
        st.dataframe(df)

        # Download Excel
        excel_file = df.to_excel(index=False)
        st.download_button("Download Excel", excel_file, file_name="coding_club.xlsx")

        # Download PDF
        pdf_file = generate_pdf(df)
        st.download_button("Download PDF", pdf_file, file_name="coding_club.pdf")

    elif password:
        st.error("Incorrect password!")
