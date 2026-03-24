import streamlit as st
import os
from datetime import datetime
from supabase import create_client, Client
import hashlib

# ==================== إعدادات Supabase ====================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "your-anon-key")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    st.error("⚠️ يرجى إعداد بيانات Supabase في Secrets")
    st.stop()

# ==================== الإعدادات العامة ====================
st.set_page_config(
    page_title="تام الثقافية 2026 | منصة الإرث اليمني الذكية",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CSS مخصص ====================
css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;800&family=Noto+Naskh+Arabic:wght@400;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
        font-family: 'Cairo', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    h1, h2, h3 {
        font-family: 'Noto Naskh Arabic', serif !important;
        color: #c9a961 !important;
        text-align: center;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #c9a961 0%, #00d4ff 100%) !important;
        color: #0a0a0a !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 1rem 2rem !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        width: 100% !important;
    }
    
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div {
        background: rgba(26, 26, 26, 0.8) !important;
        border: 1px solid rgba(201, 169, 97, 0.3) !important;
        border-radius: 10px !important;
        color: #f5f0e3 !important;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .content-card {
        background: rgba(26, 26, 26, 0.9);
        border: 1px solid rgba(201, 169, 97, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: transform 0.3s;
    }
    
    .content-card:hover {
        transform: translateY(-5px);
        border-color: #c9a961;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ==================== البيانات ====================
GOVERNORATES = [
    "صنعاء", "عدن", "تعز", "الحديدة", "إب", "ذمار", "البيضاء", 
    "مأرب", "الجوف", "حجة", "عمران", "صعدة", "حضرموت", "سقطرى",
    "المهرة", "شبوة", "أبين", "لحج", "الضالع", "ريمة", "المحويت"
]

CATEGORIES = {
    "poetry": "الشعر",
    "stories": "القصة والرواية", 
    "proverbs": "الأمثال الشعبية",
    "theater": "المسرح",
    "children": "أدب الأطفال",
    "art": "الفن التشكيلي",
    "studies": "الدراسات النقدية",
    "audio": "صوتيات",
    "video": "مرئيات",
    "books": "كتب"
}

# ==================== دوال المصادقة ====================
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, full_name, governorate):
    try:
        existing = supabase.table("users").select("*").eq("username", username).execute()
        if existing.data:
            return False, "اسم المستخدم موجود مسبقاً"
        
        data = {
            "username": username,
            "password": hash_pw(password),
            "full_name": full_name,
            "governorate": governorate
        }
        result = supabase.table("users").insert(data).execute()
        return True, "تم إنشاء الحساب بنجاح"
    except Exception as e:
        return False, str(e)

def login_user(username, password):
    try:
        result = supabase.table("users").select("*").eq("username", username).eq("password", hash_pw(password)).execute()
        if result.data:
            user = result.data[0]
            return {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'governorate': user['governorate']
            }
        return None
    except:
        return None

# ==================== دوال المشاركات ====================
def save_submission(data):
    try:
        result = supabase.table("submissions").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"خطأ في الحفظ: {e}")
        return None

def get_submissions(category=None, governorate=None, search_query=None, user_id=None):
    try:
        query = supabase.table("submissions").select("*")
        
        if category:
            query = query.eq("category", category)
        if governorate:
            query = query.eq("governorate", governorate)
        if user_id:
            query = query.eq("user_id", user_id)
        if search_query:
            query = query.or_(f"title.ilike.%{search_query}%,content.ilike.%{search_query}%")
        
        query = query.order("created_at", desc=True)
        result = query.execute()
        return result.data if result.data else []
    except:
        return []

def delete_submission(sub_id, user_id):
    try:
        submission = supabase.table("submissions").select("*").eq("id", sub_id).eq("user_id", user_id).execute()
        if submission.data:
            supabase.table("submissions").delete().eq("id", sub_id).execute()
            return True
        return False
    except:
        return False

# ==================== رفع الملفات على Supabase Storage ====================
def upload_file_to_storage(file_bytes, file_name, bucket_name="files"):
    try:
        result = supabase.storage.from_(bucket_name).upload(file_name, file_bytes)
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        return public_url
    except Exception as e:
        st.error(f"خطأ في رفع الملف: {e}")
        return None

# ==================== عرض الصفحات ====================
def show_home():
    header = """
    <div style='text-align: center; padding: 3rem 0; background: linear-gradient(135deg, rgba(10,10,10,0.95) 0%, rgba(26,26,26,0.95) 100%); border-bottom: 2px solid rgba(201,169,97,0.3); margin-bottom: 2rem;'>
        <div style='font-size: 5rem; color: #c9a961; text-shadow: 0 0 20px rgba(201,169,97,0.5); direction: ltr;'>𐩩𐩱𐩣</div>
        <div style='font-size: 1.5rem; color: #00d4ff; letter-spacing: 0.5rem; direction: ltr;'>TAM</div>
        <div style='font-size: 4rem; color: #f5f0e3; font-weight: 800;'>تام</div>
        <p style='color: #f5f0e3; font-size: 1.3rem; opacity: 0.9;'>
            أول منصة عربية تجمع بين الإرث الثقافي اليمني الأصيل<br>وقوة الذكاء الاصطناعي والتخزين السحابي
        </p>
        <span style='background: linear-gradient(135deg, #c9a961, #00d4ff); color: #0a0a0a; padding: 0.5rem 1.5rem; border-radius: 20px; font-weight: bold;'>⚡ 2026</span>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)
    
    cols = st.columns(4)
    portals = [
        ('poetry', '🪶 الشعر'),
        ('stories', '📖 القصة'),
        ('proverbs', '💬 الأمثال'),
        ('theater', '🎭 المسرح'),
        ('children', '🧒 أدب الأطفال'),
        ('art', '🎨 الفن'),
        ('studies', '🎓 الدراسات'),
        ('books', '📚 المكتبات')
    ]
    
    for i, (key, title) in enumerate(portals):
        with cols[i % 4]:
            if st.button(title, key=f'btn_{key}', use_container_width=True):
                st.session_state.page = 'gallery'
                st.session_state.filter_category = key
                st.rerun()

def show_gallery():
    category = st.session_state.get('filter_category', None)
    cat_name = CATEGORIES.get(category, 'جميع المجالات')
    
    header = f"""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(10,10,10,0.95) 0%, rgba(26,26,26,0.95) 100%); border-bottom: 2px solid rgba(201,169,97,0.3); margin-bottom: 2rem;'>
        <h1 style='color: #c9a961; font-size: 3rem;'>{cat_name}</h1>
        <p style='color: #f5f0e3;'>استعرض الإبداعات اليمنية الأصيلة</p>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        gov_filter = st.selectbox('تصفية حسب المحافظة', ['الكل'] + GOVERNORATES, index=0)
    with col2:
        sort_by = st.selectbox('الترتيب', ['الأحدث', 'الأقدم', 'الأبجدي'])
    with col3:
        if st.button('🔄 تحديث', use_container_width=True):
            st.rerun()
    
    gov_param = None if gov_filter == 'الكل' else gov_filter
    submissions = get_submissions(category=category, governorate=gov_param)
    
    if not submissions:
        st.info('📭 لا توجد مشاركات في هذا القسم بعد. كن أول من يشارك!')
        if st.button('➕ إضافة مشاركة', use_container_width=True):
            st.session_state.page = 'upload'
            st.rerun()
    else:
        st.write(f"📊 **{len(submissions)}** مشاركة")
        
        for sub in submissions:
            card = f"""
            <div class="content-card">
                <h3 style="color: #c9a961; margin-bottom: 0.5rem;">{sub['title']}</h3>
                <p style="color: #00d4ff; font-size: 0.9rem;">
                    ✍️ {sub['author_name']} | 📍 {sub['governorate']} | 🏷️ {sub.get('subcategory', CATEGORIES.get(sub['category'], sub['category']))}
                </p>
                <p style="color: #f5f0e3; opacity: 0.8; font-size: 0.8rem;">
                    📅 {sub['created_at'][:10] if sub.get('created_at') else ''}
                </p>
            </div>
            """
            st.markdown(card, unsafe_allow_html=True)
            
            if sub.get('content') and not sub.get('file_url'):
                with st.expander("📖 قراءة المحتوى"):
                    st.write(sub['content'])
            
            if sub.get('file_url'):
                if sub.get('file_type') == 'audio':
                    st.audio(sub['file_url'])
                elif sub.get('file_type') == 'video':
                    st.video(sub['file_url'])
                elif sub.get('file_type') == 'document':
                    st.markdown(f"[📥 تحميل الملف]({sub['file_url']})")

def show_search():
    header = """
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(10,10,10,0.95) 0%, rgba(26,26,26,0.95) 100%); border-bottom: 2px solid rgba(201,169,97,0.3); margin-bottom: 2rem;'>
        <h1 style='color: #c9a961; font-size: 3rem;'>🔍 البحث في المنصة</h1>
        <p style='color: #f5f0e3;'>ابحث في آلاف المشاركات الثقافية اليمنية</p>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)
    
    search_query = st.text_input('', placeholder='ابحث بعنوان المشاركة، المحتوى، أو اسم المؤلف...')
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button('🔍 بحث', use_container_width=True):
            st.session_state.search_query = search_query
            st.rerun()
    
    if search_query:
        results = get_submissions(search_query=search_query)
        st.write(f"📊 **{len(results)}** نتيجة")
        
        if not results:
            st.warning('❌ لم يتم العثور على نتائج')
        else:
            for sub in results:
                card = f"""
                <div class="content-card">
                    <h3 style="color: #c9a961;">{sub['title']}</h3>
                    <p style="color: #00d4ff;">✍️ {sub['author_name']} | 📍 {sub['governorate']} | 🏷️ {CATEGORIES.get(sub['category'], sub['category'])}</p>
                    <p style="color: #f5f0e3; opacity: 0.7;">{sub.get('content', '')[:200]}...</p>
                </div>
                """
                st.markdown(card, unsafe_allow_html=True)

def show_upload():
    header = """
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(10,10,10,0.95) 0%, rgba(26,26,26,0.95) 100%); border-bottom: 2px solid rgba(201,169,97,0.3); margin-bottom: 2rem;'>
        <h1 style='color: #c9a961; font-size: 3rem;'>رفع المشاركات</h1>
        <p style='color: #f5f0e3;'>سيتم توجيه مشاركتك تلقائياً لمجالك ومحافظتك</p>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)
    
    is_logged_in = 'user' in st.session_state
    
    with st.form('upload_form'):
        st.markdown('<h3 style="color: #c9a961;">📝 معلومات المشاركة</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if is_logged_in:
                author = st.text_input('الاسم', value=st.session_state.user['full_name'], disabled=True)
            else:
                author = st.text_input('الاسم *', placeholder='أدخل اسمك الكامل')
        
        with col2:
            if is_logged_in:
                gov = st.selectbox('المحافظة', GOVERNORATES, 
                                 index=GOVERNORATES.index(st.session_state.user['governorate']),
                                 disabled=True)
                gov = st.session_state.user['governorate']
            else:
                gov = st.selectbox('المحافظة *', GOVERNORATES)
        
        col3, col4 = st.columns(2)
        with col3:
            cat = st.selectbox('المجال', list(CATEGORIES.keys()), format_func=lambda x: CATEGORIES[x])
        with col4:
            subcat = st.text_input('التصنيف الفرعي', placeholder='مثال: الشعر العمودي')
        
        title = st.text_input('عنوان المشاركة *', placeholder='أدخل عنواناً مميزاً')
        
        upload_type = st.radio('نوع المشاركة', ['نص', 'ملف', 'صوت', 'فيديو'], horizontal=True)
        
        content = ''
        file_url = None
        file_type = None
        
        if upload_type == 'نص':
            content = st.text_area('المحتوى', height=200)
        else:
            if upload_type == 'ملف':
                uploaded_file = st.file_uploader('اختر الملف', type=['pdf', 'doc', 'docx'])
                file_type = 'document'
            elif upload_type == 'صوت':
                uploaded_file = st.file_uploader('اختر ملف الصوت', type=['mp3', 'wav'])
                file_type = 'audio'
            else:
                uploaded_file = st.file_uploader('اختر ملف الفيديو', type=['mp4', 'avi'])
                file_type = 'video'
            
            if uploaded_file:
                file_bytes = uploaded_file.getvalue()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_title = ''.join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(' ', '_') if title else 'untitled'
                file_name = f"{cat}/{gov}/{safe_title}_{timestamp}_{uploaded_file.name}"
                
                with st.spinner('جاري رفع الملف على السحابة...'):
                    file_url = upload_file_to_storage(file_bytes, file_name)
                    if file_url:
                        st.success('✅ تم رفع الملف')
                        content = f'ملف: {uploaded_file.name}'
        
        if is_logged_in:
            st.info(f"📍 سيتم نشر المشاركة باسم: **{st.session_state.user['full_name']}**")
        else:
            st.warning('⚠️ سيتم نشر المشاركة كـ "زائر". [سجل الدخول](#) لربط المشاركة بحسابك')
        
        submitted = st.form_submit_button('🚀 إرسال المشاركة', use_container_width=True)
        
        if submitted:
            if not title or not author or not gov:
                st.error('❌ العنوان والاسم والمحافظة مطلوبة!')
            else:
                data = {
                    'author_name': author,
                    'governorate': gov,
                    'category': cat,
                    'subcategory': subcat,
                    'title': title,
                    'content': content,
                    'file_url': file_url,
                    'file_type': file_type,
                    'user_id': st.session_state.user['id'] if is_logged_in else None
                }
                
                result = save_submission(data)
                if result:
                    st.success('✅ تم رفع المشاركة بنجاح!')
                    if is_logged_in:
                        st.balloons()
                        st.session_state.page = 'home'
                        st.rerun()

def show_register():
    header = """
    <div style='text-align: center; padding: 2rem;'>
        <h1 style='color: #c9a961;'>إنشاء حساب جديد</h1>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)
    
    with st.form('register_form'):
        username = st.text_input('اسم المستخدم *')
        full_name = st.text_input('الاسم الكامل *')
        password = st.text_input('كلمة المرور *', type='password')
        confirm = st.text_input('تأكيد كلمة المرور *', type='password')
        governorate = st.selectbox('المحافظة *', GOVERNORATES)
        
        if st.form_submit_button('📝 إنشاء الحساب', use_container_width=True):
            if not all([username, full_name, password, confirm]):
                st.error('❌ جميع الحقول مطلوبة')
            elif password != confirm:
                st.error('❌ كلمتا المرور غير متطابقتين')
            elif len(password) < 6:
                st.error('❌ كلمة المرور قصيرة جداً')
            else:
                success, msg = register_user(username, password, full_name, governorate)
                if success:
                    st.success('✅ تم إنشاء الحساب! يمكنك الآن تسجيل الدخول')
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(f'❌ {msg}')

def show_login():
    header = """
    <div style='text-align: center; padding: 2rem;'>
        <h1 style='color: #c9a961;'>تسجيل الدخول</h1>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)
    
    with st.form('login_form'):
        username = st.text_input('اسم المستخدم')
        password = st.text_input('كلمة المرور', type='password')
        
        if st.form_submit_button('🔐 دخول', use_container_width=True):
            user = login_user(username, password)
            if user:
                st.session_state.user = user
                st.success(f"✅ أهلاً {user['full_name']}!")
                st.session_state.page = 'home'
                st.rerun()
            else:
                st.error('❌ بيانات الدخول غير صحيحة')

def show_profile():
    if 'user' not in st.session_state:
        st.session_state.page = 'login'
        st.rerun()
        return
    
    user = st.session_state.user
    
    header = f"""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(10,10,10,0.95) 0%, rgba(26,26,26,0.95) 100%); border-bottom: 2px solid rgba(201,169,97,0.3); margin-bottom: 2rem;'>
        <div style='font-size: 4rem;'>👤</div>
        <h1 style='color: #c9a961; font-size: 2.5rem;'>{user['full_name']}</h1>
        <p style='color: #00d4ff;'>📍 {user['governorate']}</p>
    </div>
    """
    st.markdown(header, unsafe_allow_html=True)
    
    my_submissions = get_submissions(user_id=user['id'])
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📊 إحصائياتك")
        st.write(f"- **عدد المشاركات:** {len(my_submissions)}")
        st.write(f"- **اسم المستخدم:** {user['username']}")
    with col2:
        if st.button('➕ مشاركة جديدة', use_container_width=True):
            st.session_state.page = 'upload'
            st.rerun()
    
    if my_submissions:
        st.markdown("### 📝 مشاركاتك")
        for sub in my_submissions:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div class="content-card">
                        <h4 style="color: #c9a961;">{sub['title']}</h4>
                        <p style="color: #00d4ff; font-size: 0.8rem;">
                            {CATEGORIES.get(sub['category'], sub['category'])} | {sub.get('created_at', '')[:10]}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button('🗑️ حذف', key=f"del_{sub['id']}"):
                        if delete_submission(sub['id'], user['id']):
                            st.success('✅ تم الحذف')
                            st.rerun()
                        else:
                            st.error('❌ فشل الحذف')
    else:
        st.info("📭 لم تقم بإضافة أي مشاركات بعد")

def show_nav():
    cols = st.columns([2, 1, 1, 1, 1])
    
    with cols[0]:
        if st.button('⚡ تام', key='nav_home'):
            st.session_state.page = 'home'
            st.rerun()
    
    with cols[1]:
        if st.button('➕ رفع', key='nav_upload'):
            st.session_state.page = 'upload'
            st.rerun()
    
    with cols[2]:
        if 'user' in st.session_state:
            if st.button('👤 ' + st.session_state.user['full_name'][:10], key='nav_profile'):
                st.session_state.page = 'profile'
                st.rerun()
    
    with cols[3]:
        if st.button('🔍 بحث', key='nav_search'):
            st.session_state.page = 'search'
            st.rerun()
    
    with cols[4]:
        if 'user' in st.session_state:
            if st.button('🚪 خروج', key='nav_logout'):
                del st.session_state.user
                st.session_state.page = 'home'
                st.rerun()
        else:
            if st.button('🔐 دخول', key='nav_login'):
                st.session_state.page = 'login'
                st.rerun()

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
    show_nav()
    
    page = st.session_state.page
    if page == 'home':
        show_home()
    elif page == 'upload':
        show_upload()
    elif page == 'login':
        show_login()
    elif page == 'register':
        show_register()
    elif page == 'search':
        show_search()
    elif page == 'gallery':
        show_gallery()
    elif page == 'profile':
        show_profile()
    else:
        show_home()

if __name__ == '__main__':
    main()
