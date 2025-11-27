import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import string
from datetime import datetime

# --- إعداد الصفحة (شكل احترافي) ---
st.set_page_config(page_title="نظام الإدارة - Admin Pro", layout="wide", page_icon="🏫")

# ----------------------------------------------------
# --- دوال الثوابت والاتصال ---
# ----------------------------------------------------

# ثوابت لترتيب الأعمدة الجديدة في ورقة Students (تستخدم في قسم الخزينة)
TOTAL_FEES_INDEX = 21   # موقع العمود TotalFees في قائمة row_values (0-based)
PAID_FEES_INDEX = 22    # موقع العمود PaidFees في قائمة row_values
PASSWORD_INDEX = 23     # موقع العمود Password في قائمة row_values

# ثوابت لأرقام الأعمدة في GSpread (1-based)
PAID_FEES_COL_GS = 23   # العمود 23 (W) لتحديث PaidFees
PASSWORD_COL_GS = 24    # العمود 24 (X) لتحديث Password

def get_database():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("❌ خطأ: لم يتم العثور على مفتاح [gcp_service_account] في Streamlit Secrets.")
            st.stop()
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        sheet = client.open("School_System") 
        return sheet
    
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات. (الخطأ: {e})")
        st.stop()

@st.cache_data(ttl=5) # تحديث البيانات كل 5 ثواني
def load_data(sheet_name):
    return pd.DataFrame(sheet.worksheet(sheet_name).get_all_records())

# --- دوال مساعدة (كما هي) ---
def generate_unique_student_id(existing_ids):
    while True:
        new_id = random.choice(string.ascii_uppercase) + ''.join(random.choices(string.digits, k=7))
        if new_id not in existing_ids:
            return new_id

def generate_student_password():
    letters = ''.join(random.choices(string.ascii_letters, k=2))
    digits = ''.join(random.choices(string.digits, k=6))
    return letters + digits

def generate_teacher_id():
    return "T" + ''.join(random.choices(string.digits, k=6))

# ----------------------------------------------------
# --- الواجهة الرئيسية ---
# ----------------------------------------------------

st.title("🏫 لوحة تحكم الإدارة الشاملة")
sheet = get_database() 

menu = st.sidebar.selectbox("القائمة الرئيسية", [
    "تسجيل طالب جديد", 
    "بحث عن طالب", 
    "عرض بيانات المعلمين", 
    "الخزينة (دفع المصاريف)", 
    "تسجيل معلم", 
    "إضافة مواد دراسية"
])

# ----------------- 1. تسجيل طالب جديد (شامل وبتنسيق احترافي) -----------------
if menu == "تسجيل طالب جديد":
    st.header("📝 تسجيل طالب جديد (البيانات الجبارة)")
    
    with st.form("student_reg_full"):
        
        # استخدام expander لتنظيم النموذج الضخم بشكل احترافي
        with st.expander("بيانات الطالب الشخصية والاتصال (1 - 15)", expanded=True):
            
            st.subheader("البيانات الشخصية والتعريفية")
            name = st.text_input("1. الاسم كاملاً (الرباعي أو أكثر)")
            col1, col2, col3 = st.columns(3)
            with col1:
                date_of_birth = st.date_input("4. تاريخ الميلاد", datetime(2005, 1, 1))
                religion = st.selectbox("3. الديانة", ["مسلم", "مسيحي", "أخرى"])
            with col2:
                gender = st.selectbox("19. الجنس", ["ذكر", "أنثى"])
                nationality = st.text_input("16. الجنسية", value="مصري")
            with col3:
                country_of_birth = st.text_input("13. دولة الميلاد", value="مصر")
                photo_link = st.text_input("2. رابط صورة الطالب (اختياري)")

            st.subheader("بيانات الرقم القومي والعنوان")
            col4, col5 = st.columns(2)
            with col4:
                national_id = st.text_input("17. الرقم القومي (14 رقم)")
                id_issuer = st.text_input("18. جهة إصدار الرقم القومي")
            with col5:
                governorate = st.text_input("14. المحافظة")
                address = st.text_area("15. العنوان بالتفصيل")

            st.subheader("بيانات الاتصال")
            col6, col7, col8 = st.columns(3)
            with col6:
                student_mobile = st.text_input("10. موبايل الطالب")
            with col7:
                landline = st.text_input("11. التليفون الأرضي (اختياري)")
            with col8:
                parent_phone = st.text_input("12. تليفون ولي الأمر")
        
        with st.expander("بيانات المؤهل والالتحاق (16 - 20)", expanded=True):
            st.subheader("بيانات المؤهل السابق")
            col9, col10, col11 = st.columns(3)
            with col9:
                grad_cert = st.text_input("5. الشهادة الحاصل عليها (مثال: الثانوية العامة)")
                cert_seat_num = st.text_input("7. رقم جلوس الشهادة")
            with col10:
                cert_date = st.date_input("6. تاريخ الحصول على الشهادة", datetime.now())
                total_score = st.number_input("8. مجموع الطالب (رقماً)", min_value=0.0)
            with col11:
                percentage = st.number_input("9. النسبة المئوية (%)", min_value=0.0, max_value=100.0)
                grade_level = st.selectbox("20. الفرقة الدراسية", ["الأولى", "الثانية", "الثالثة"])

            st.subheader("بيانات الالتحاق")
            total_fees = st.number_input("المصاريف الدراسية المستحقة (للسنة الحالية)", min_value=0)
        
        submitted = st.form_submit_button("✅ تسجيل الطالب وإضافة جميع البيانات")
        
        if submitted and name:
            ws = sheet.worksheet("Students")
            existing_ids = ws.col_values(1)
            new_id = generate_unique_student_id(existing_ids)
            
            # --- الصف الذي سيتم إضافته (25 عنصراً) ---
            row = [
                new_id, str(name), str(photo_link), str(religion), str(date_of_birth), 
                str(grad_cert), str(cert_date), str(cert_seat_num), float(total_score), float(percentage), 
                str(student_mobile), str(landline), str(parent_phone), str(country_of_birth), str(governorate), 
                str(address), str(nationality), str(national_id), str(id_issuer), str(gender), 
                str(grade_level), 
                # البيانات المالية والدخول في النهاية (Indices 21, 22, 23, 24)
                float(total_fees), 0.0, "", str(datetime.now().date())
            ]
            
            ws.append_row(row)
            
            st.success(f"🎉 تم تسجيل الطالب بنجاح! كود الطالب: **{new_id}**")
            st.balloons()


# ----------------- 2. بحث عن طالب (عرض شامل) -----------------
elif menu == "بحث عن طالب":
    st.header("🔎 البحث عن طالب وعرض جميع بياناته الشاملة")
    search_term = st.text_input("ابحث بالاسم أو الكود").strip()
    
    if search_term:
        df = load_data("Students") 
        
        results = df[
            df['Name'].astype(str).str.contains(search_term, case=False) | 
            df['StudentID'].astype(str).str.contains(search_term, case=False)
        ]
        
        if not results.empty:
            st.dataframe(results, use_container_width=True) 
        else:
            st.warning("❌ لا توجد نتائج مطابقة لاسم أو كود الطالب.")

# ----------------- 3. عرض بيانات المعلمين (كما هي) -----------------
elif menu == "عرض بيانات المعلمين":
    st.header("🧑‍🏫 جميع بيانات المعلمين الشخصية")
    df = load_data("Teachers") 
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لا يوجد معلمين مسجلين حالياً.")


# ----------------- 4. الخزينة (دفع المصاريف) (مُعدل للأعمدة الجديدة) -----------------
elif menu == "الخزينة (دفع المصاريف)":
    st.header("💰 تحصيل المصروفات")
    st_code = st.text_input("أدخل كود الطالب للدفع").strip()
    
    if st_code:
        ws = sheet.worksheet("Students")
        try:
            cell = ws.find(st_code)
        except gspread.exceptions.CellNotFound:
            st.error("كود الطالب غير صحيح أو غير موجود.")
            st.stop() 

        if cell:
            row_num = cell.row
            row_values = ws.row_values(row_num)
            
            # التحقق من طول الصف الجديد (يجب أن يكون 25 عموداً على الأقل)
            if len(row_values) < 24: 
                 st.error("بيانات الطالب غير مكتملة في الشيت. الرجاء التحقق من ترتيب الأعمدة الجديدة.")
                 st.stop()
                 
            # استخدام الأعمدة الجديدة عبر الـ INDEX
            name = row_values[1]
            total = float(row_values[TOTAL_FEES_INDEX]) if row_values[TOTAL_FEES_INDEX] else 0.0
            paid_so_far = float(row_values[PAID_FEES_INDEX]) if row_values[PAID_FEES_INDEX] else 0.0
            current_pass = row_values[PASSWORD_INDEX]
            
            remaining = total - paid_so_far
            
            st.info(f"الطالب: **{name}** | المتبقي للاستحقاق: **{remaining}**")
            
            if remaining > 0:
                payment = st.number_input("المبلغ المدفوع (كاش)", min_value=1.0, max_value=remaining)
                
                if st.button("تأكيد عملية الدفع"):
                    new_paid = paid_so_far + payment
                    
                    # تحديث المبلغ (استخدام GSpread 1-based index)
                    ws.update_cell(row_num, PAID_FEES_COL_GS, new_paid) 
                    
                    if not current_pass:
                        new_pass = generate_student_password()
                        # تحديث الباسورد (استخدام GSpread 1-based index)
                        ws.update_cell(row_num, PASSWORD_COL_GS, new_pass) 
                        password_to_show = new_pass
                        st.success("✅ تم الدفع بنجاح! وتم إنشاء بيانات الدخول.")
                    else:
                        password_to_show = current_pass
                        st.success("✅ تم الدفع بنجاح! بيانات الدخول كانت موجودة مسبقاً.")
                    
                    st.code(f"كود الطالب: {st_code}\nالباسوورد: {password_to_show}", language="text")
            else:
                st.warning("هذا الطالب قام بسداد كامل المصروفات المستحقة.")

# ----------------- 5. تسجيل معلم (كما هو) -----------------
elif menu == "تسجيل معلم":
    st.header("🧑‍🏫 إضافة معلم جديد (البيانات الشخصية كاملة)")
    with st.form("teacher_reg"):
        t_name = st.text_input("اسم المعلم")
        t_subject = st.text_input("المادة التي يدرسها")
        
        col1, col2 = st.columns(2)
        with col1:
            t_grade = st.selectbox("الصف الدراسي (المسؤول عنه)", ["الأول", "الثاني", "الثالث", "متعدد"])
        with col2:
            t_term = st.selectbox("الترم", ["الأول", "الثاني", "كل الأترام"])

        t_phone = st.text_input("رقم الهاتف الشخصي")
        t_address = st.text_input("العنوان بالتفصيل")
        
        t_sub = st.form_submit_button("تسجيل المعلم")
        
        if t_sub and t_name and t_subject:
            ws = sheet.worksheet("Teachers")
            t_id = generate_teacher_id()
            t_pass = generate_student_password()
            
            # الترتيب: ID, Name, Subject, Grade, Term, Phone, Address, Password
            ws.append_row([t_id, t_name, t_subject, t_grade, t_term, t_phone, t_address, t_pass])
            
            st.success(f"✅ تم التسجيل. كود المعلم: **{t_id}** | الباسوورد: **{t_pass}**")

# ----------------- 6. إضافة مواد (كما هي) -----------------
elif menu == "إضافة مواد دراسية":
    st.header("🔗 نشر الروابط والمواد")
    
    type_mat = st.radio("من سيشاهد هذه المادة؟", ["عام (لكل الطلاب)", "خاص بمادة معينة"])
    
    with st.form("mat_form"):
        title = st.text_input("عنوان المادة/الامتحان (مثل: رابط امتحان الوحدة الأولى)")
        link = st.text_input("الرابط (رابط جوجل درايف، يوتيوب، إلخ...)")
        
        teacher_id_input = ""
        if type_mat == "خاص بمادة معينة":
             teacher_id_input = st.text_input("كود المعلم صاحب المادة (Txxxxxx)")
             
        submit_mat = st.form_submit_button("نشر المادة")
        
        if submit_mat and title and link:
            ws = sheet.worksheet("Materials")
            m_type = "Global" if type_mat == "عام (لكل الطلاب)" else "Subject"
            ws.append_row([m_type, title, link, teacher_id_input, str(datetime.now())])
            st.success(f"✅ تم نشر المادة بنجاح")
