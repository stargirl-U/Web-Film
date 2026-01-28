import streamlit as st
import sqlite3
from pathlib import Path

# =============================
# DATABASE
# =============================
DB_PATH = "film.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS film_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        film_id INTEGER,
        username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(film_id, username)
    )
""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS film (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT,
            genre TEXT,
            sinopsis TEXT,
            tahun INTEGER,
            rating REAL,
            durasi TEXT,
            durasi_episode TEXT,
            umur TEXT,
            poster TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            film_id INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    c.execute("INSERT OR IGNORE INTO user VALUES (NULL,'admin','admin123','admin')")
    c.execute("INSERT OR IGNORE INTO user VALUES (NULL,'user','user123','user')")

    conn.commit()
    conn.close()

init_db()

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="Web Rekomendasi Film", layout="wide")

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.role = ""
    st.session_state.username = ""

# =============================
# CSS
# =============================
st.markdown("""
<style>
.stApp { background-color:#40513B; }
section[data-testid="stSidebar"] { background-color:#6F8F72; }

h1,h2,h3,h4,h5,h6,p,label { color:white !important; }

input, textarea {
    background-color:#E8F0E8 !important;
    color:black !important;
    border-radius:8px !important;
}

div[data-baseweb="select"] > div {
    background-color:#E8F0E8 !important;
    color:black !important;
    border-radius:8px !important;
}

div[data-baseweb="select"] span {
    color:black !important;
}

button {
    background-color:#4F6F52 !important;
    color:white !important;
    border-radius:8px !important;
}
</style>
""", unsafe_allow_html=True)

# =============================
# LOGIN
# =============================
if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT role FROM user WHERE username=? AND password=?", (u,p))
        r = c.fetchone()
        conn.close()

        if r:
            st.session_state.login = True
            st.session_state.role = r[0]
            st.session_state.username = u
            st.rerun()
        else:
            st.error("Username atau password salah")

    st.markdown("""
    <div style="margin-top:60px;text-align:center;color:white">
    © 2026 — RekomFilm<br>
    Created by<br>
    Azza Ellasari Umayro (24.83.1106)<br>
    Dina Ayu Safitri (24.83.1070)<br>
    Sri Irsa Ramayani (24.83.1055)<br>
    Nayla Rachmddina (24.83.1099)<br>
    Academic Project — Pemrograman Dasar & Python
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# =============================
# SIDEBAR
# =============================
st.sidebar.success(f"Login sebagai: {st.session_state.username}")

genre_filter = st.sidebar.selectbox(
    "Filter Genre",
    ["All","Action","Drama","Comedy","Horor","Romance"]
)

menu = ["🏠 Semua Film", "🔍 Cari Film", "⭐ Watchlist"]
if st.session_state.role == "admin":
    menu.insert(1, "➕ Tambah Film")

menu = st.sidebar.radio("Menu", menu)

if st.sidebar.button("🚪 Logout"):
    st.session_state.login = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

# =============================
# SEMUA FILM
# =============================
if menu == "🏠 Semua Film":
    st.title("🎬 Web Rekomendasi Film")

    conn = get_conn()
    c = conn.cursor()

    if genre_filter == "All":
        c.execute("""
            SELECT id,judul,genre,sinopsis,tahun,rating,durasi,durasi_episode,umur,poster,
            (SELECT COUNT(*) FROM film_stats WHERE film_id=film.id)
            FROM film
        """)
    else:
        c.execute("""
            SELECT id,judul,genre,sinopsis,tahun,rating,durasi,durasi_episode,umur,poster,
            (SELECT COUNT(*) FROM film_stats WHERE film_id=film.id)
            FROM film WHERE genre=?
        """,(genre_filter,))

    films = c.fetchall()
    conn.close()

    for f in films:
        col1,col2 = st.columns([1,3])

        with col1:
            if f[9] and Path(f[9]).exists():
                st.image(f[9], width=150)
            else:
                st.write("🎞️ No Poster")

        with col2:
            # =============================
            # LOGIKA DURASI (FIX ERROR)
            # =============================
            durasi_tampil = "-"
            if f[7]:  # episode ada
                durasi_tampil = f"{f[7]} Episode"
            elif f[6]:  # durasi jam & menit ada
                durasi_tampil = f[6]

            st.markdown(f"""
**🎥 {f[1]}**  
Genre: {f[2]}  
Tahun: {f[4]}  
Rating: ⭐ {f[5]}  
Durasi: {durasi_tampil}  
Umur: {f[8]}  
📖 **Sinopsis:** {f[3]}  
❤️ {f[10]} Likes
""")

            if st.button("❤️ Like", key=f"like_{f[0]}"):
                conn=get_conn()
                c=conn.cursor()
                c.execute(
    "INSERT OR IGNORE INTO film_stats (film_id, username) VALUES (?,?)",
    (f[0], st.session_state.username)
)
                conn.commit()
                conn.close()
                st.rerun()

            if st.button("➕ Tambah ke Watchlist", key=f"wl_{f[0]}"):
                conn=get_conn(); c=conn.cursor()
                c.execute("SELECT 1 FROM user_watchlist WHERE username=? AND film_id=?",(st.session_state.username,f[0]))
                if not c.fetchone():
                    c.execute("INSERT INTO user_watchlist(username,film_id) VALUES (?,?)",(st.session_state.username,f[0]))
                conn.commit(); conn.close()
                st.success("Ditambahkan ke Watchlist")

            if st.session_state.role=="admin":
                if st.button("🗑️ Hapus Film", key=f"del_{f[0]}"):
                    conn=get_conn(); c=conn.cursor()
                    c.execute("DELETE FROM film WHERE id=?",(f[0],))
                    c.execute("DELETE FROM film_stats WHERE film_id=?",(f[0],))
                    c.execute("DELETE FROM user_watchlist WHERE film_id=?",(f[0],))
                    conn.commit(); conn.close()
                    st.rerun()

        st.markdown("---")

# =============================
# TAMBAH FILM
# =============================
elif menu=="➕ Tambah Film":
    st.title("➕ Tambah Film")

    judul = st.text_input("Judul Film")
    genre = st.selectbox("Genre",["Action","Drama","Comedy","Horor","Romance"])
    tahun = st.number_input("Tahun",1900,2100)

    rating = st.number_input("Rating",0.0,10.0,step=0.1)

    st.subheader("Durasi Film")
    col1,col2 = st.columns(2)
    with col1:
        jam = st.number_input("Jam",0,10)
    with col2:
        menit = st.number_input("Menit",0,59)

    durasi = None
    if jam > 0 or menit > 0:
        durasi = f"{jam} jam {menit} menit"

    durasi_episode = st.text_input("Episode (kosongkan jika film)")

    umur = st.selectbox("Batasan Umur",["10+","15+","18+","25+"])
    sinopsis = st.text_area("Sinopsis")
    poster = st.file_uploader("Poster",type=["jpg","png"])

    poster_path=None
    if poster:
        Path("poster").mkdir(exist_ok=True)
        poster_path=f"poster/{poster.name}"
        with open(poster_path,"wb") as f:
            f.write(poster.getbuffer())

    if st.button("💾 Simpan Film"):
        conn=get_conn(); c=conn.cursor()
        c.execute("""
            INSERT INTO film
            (judul,genre,sinopsis,tahun,rating,durasi,durasi_episode,umur,poster)
            VALUES (?,?,?,?,?,?,?,?,?)
        """,(judul,genre,sinopsis,tahun,rating,durasi,durasi_episode,umur,poster_path))
        conn.commit(); conn.close()
        st.success("Film berhasil ditambahkan")

# =============================
# CARI FILM
# =============================
elif menu=="🔍 Cari Film":
    st.title("🔍 Cari Film")
    key = st.text_input("Cari judul film")

    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT judul,genre,tahun FROM film WHERE judul LIKE ?",(f"%{key}%",))
    res=c.fetchall(); conn.close()

    if res:
        for r in res:
            st.write(f"🎬 **{r[0]}** ({r[1]}) - {r[2]}")
    else:
        st.warning("Film tidak ditemukan")

# =============================
# WATCHLIST
# =============================
elif menu=="⭐ Watchlist":
    st.title("⭐ Watchlist Saya")

    conn=get_conn(); c=conn.cursor()
    c.execute("""
        SELECT f.judul,f.genre,f.tahun,f.rating
        FROM film f
        JOIN user_watchlist w ON f.id=w.film_id
        WHERE w.username=?
    """,(st.session_state.username,))
    data=c.fetchall(); conn.close()

    if data:
        for f in data:
            st.write(f"🎬 **{f[0]}** | ⭐ {f[3]}")
    else:
        st.info("Watchlist masih kosong")
