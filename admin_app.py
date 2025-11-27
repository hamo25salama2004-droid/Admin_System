import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import string
from datetime import datetime

# --- إعداد الصفحة ---
st.set_page_config(page_title="نظام الإدارة - Admin", layout="wide", page_icon="🏫")

# ----------------------------------------------------
# --- دالة الاتصال بجوجل شيت ---
# ----------------------------------------------------
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

# --- دوال مساعدة ---
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
# --- الواجهة الرئيسية للوحة التحكم ---
# ----------------------------------------------------

st.title("🏫 لوحة تحكم الإدارة")
sheet = get_database() 

menu = st.sidebar.selectbox("القائمة الرئيسية", [
    "تسجيل طالب جديد", 
    "بحث عن طالب", 
    "عرض بيانات المعلمين", # مضاف
    "الخزينة (دفع المصاريف)", 
    "تسجيل معلم", 
    "إضافة مواد دراسية"
])

# ----------------- وظيفة قراءة البيانات (لتحسين التحديث) -----------------
@st.cache_data(ttl=5) # تحديث البيانات كل 5 ثواني
def load_data(sheet_name):
    return pd.DataFrame(sheet.worksheet(sheet_name).get_all_records())

# ----------------- 1. تسجيل طالب -----------------
if menu == "تسجيل طالب جديد":
    st.header("📝 تسجيل طالب جديد")
    with st.form("student_reg"):
        # جميع بيانات الطالب
        name = st.text_input("اسم الطالب رباعي")
        phone = st.text_input("رقم الهاتف")
        total_fees = st.number_input("المصاريف الدراسية المستحقة", min_value=0)
        submitted = st.form_submit_button("تسجيل الطالب")
        
        if submitted and name:
            ws = sheet.worksheet("Students")
            existing_ids = ws.col_values(1)
            new_id = generate_unique_student_id(existing_ids)
            # الأعمدة: [StudentID, Name, Phone, TotalFees, PaidFees, Password, RegDate]
            row = [new_id, name, phone, total_fees, 0, "", str(datetime.now().date())]
            ws.append_row(row)
            st.success(f"✅ تم تسجيل الطالب بنجاح! كود الطالب هو: **{new_id}**")

# ----------------- 2. بحث عن طالب -----------------
elif menu == "بحث عن طالب":
    st.header("🔎 البحث عن طالب وعرض جميع بياناته")
    search_term = st.text_input("ابحث بالاسم أو الكود").strip()
    
    if search_term:
        df = load_data("Students") # قراءة البيانات من الكاش
        
        # فلترة النتائج لعرض جميع المعلومات الشخصية وغير الشخصية
        results = df[
            df['Name'].astype(str).str.contains(search_term, case=False) | 
            df['StudentID'].astype(str).str.contains(search_term, case=False)
        ]
        
        if not results.empty:
            st.dataframe(results, use_container_width=True) # عرض جميع الأعمدة
        else:
            st.warning("❌ لا توجد نتائج مطابقة لاسم أو كود الطالب.")

# ----------------- 3. عرض بيانات المعلمين -----------------
elif menu == "عرض بيانات المعلمين":
    st.header("🧑‍🏫 جميع بيانات المعلمين الشخصية")
    df = load_data("Teachers") # قراءة بيانات المعلمين
    if not df.empty:
        st.dataframe(df, use_container_width=True) # عرض جميع بيانات المعلمين الشخصية
    else:
        st.info("لا يوجد معلمين مسجلين حالياً.")


# ----------------- 4. الخزينة (دفع المصاريف) - (الكود كما هو) -----------------
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
            
            if len(row_values) < 6: 
                 st.error("بيانات الطالب غير مكتملة في الشيت. الرجاء التحقق.")
                 st.stop()
                 
            name = row_values[1]
            total = float(row_values[3]) if row_values[3] else 0.0
            paid_so_far = float(row_values[4]) if row_values[4] else 0.0
            current_pass = row_values[5]
            
            remaining = total - paid_so_far
            
            st.info(f"الطالب: **{name}** | المتبقي للاستحقاق: **{remaining}**")
            
            if remaining > 0:
                payment = st.number_input("المبلغ المدفوع (كاش)", min_value=1.0, max_value=remaining)
                
                if st.button("تأكيد عملية الدفع"):
                    new_paid = paid_so_far + payment
                    ws.update_cell(row_num, 5, new_paid)
                    
                    if not current_pass:
                        new_pass = generate_student_password()
                        ws.update_cell(row_num, 6, new_pass)
                        password_to_show = new_pass
                        st.success("✅ تم الدفع بنجاح! وتم إنشاء بيانات الدخول.")
                    else:
                        password_to_show = current_pass
                        st.success("✅ تم الدفع بنجاح! بيانات الدخول كانت موجودة مسبقاً.")
                    
                    st.code(f"كود الطالب: {st_code}\nالباسوورد: {password_to_show}", language="text")
            else:
                st.warning("هذا الطالب قام بسداد كامل المصروفات المستحقة.")

# ----------------- 5. تسجيل معلم -----------------
elif menu == "تسجيل معلم":
    st.header("🧑‍🏫 إضافة معلم جديد")
    with st.form("teacher_reg"):
        # جميع البيانات الشخصية للمعلم
        t_name = st.text_input("اسم المعلم")
        t_subject = st.text_input("المادة التي يدرسها")
        t_grade = st.selectbox("الصف الدراسي (المسؤول عنه)", ["الأول", "الثاني", "الثالث", "متعدد"])
        t_term = st.selectbox("الترم", ["الأول", "الثاني", "كل الأترام"])
        
        t_sub = st.form_submit_button("تسجيل المعلم")
        
        if t_sub and t_name and t_subject:
            ws = sheet.worksheet("Teachers")
            t_id = generate_teacher_id()
            t_pass = generate_student_password()
            # الأعمدة: [TeacherID, Name, Subject, Grade, Term, Password]
            ws.append_row([t_id, t_name, t_subject, t_grade, t_term, t_pass])
            st.success(f"✅ تم التسجيل. كود المعلم: **{t_id}** | الباسوورد: **{t_pass}**")

# ----------------- 6. إضافة مواد -----------------
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
