import html

import altair as alt
import pandas as pd
import requests
import streamlit as st

try:
    API = st.secrets["API_URL"].rstrip("/")
except Exception:
    API = "http://localhost:8000"

st.set_page_config(
    page_title="CampusConnect | Complaint Management",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

ss = st.session_state
ss.setdefault("token", None)
ss.setdefault("user", None)

STATUSES = ["pending", "in_progress", "resolved", "rejected"]
STATUS_LABELS = {"pending": "Pending", "in_progress": "In Progress",
                 "resolved": "Resolved", "rejected": "Rejected"}
STATUS_COLORS = {"pending": "#F59E0B", "in_progress": "#3B82F6",
                 "resolved": "#22C55E", "rejected": "#EF4444"}
PILL_STYLE = {
    "pending": ("#FEF3C7", "#92400E"),
    "in_progress": ("#DBEAFE", "#1E40AF"),
    "resolved": ("#DCFCE7", "#166534"),
    "rejected": ("#FEE2E2", "#991B1B"),
}
BADGE = {"pending": "🟡", "in_progress": "🔵", "resolved": "🟢", "rejected": "🔴"}
ROLE_LABELS = {"student": "Student", "dept_admin": "Department Administrator",
               "super_admin": "Super Administrator"}


def h(s):
    """Collapse HTML/CSS into one line so Markdown never mangles it."""
    return " ".join(line.strip() for line in s.splitlines() if line.strip())


def esc(text):
    return html.escape(str(text or "")).replace("\n", "<br>")


# ======================================================================
# STYLES
# ======================================================================
CSS = h("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}
.stApp { background: #F4F6FB; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1180px; }

/* ---------- hero (login page) ---------- */
.cc-hero {
  background: linear-gradient(145deg, #0B1F4B 0%, #1D4ED8 100%);
  border-radius: 20px; padding: 40px 38px; color: #fff;
  box-shadow: 0 18px 40px rgba(29,78,216,.28); min-height: 520px;
}
.cc-hero .brand { font-size: 1.05rem; font-weight: 700; letter-spacing: .02em; opacity: .95; }
.cc-hero h1 { color: #fff; font-size: 2.5rem; line-height: 1.15; font-weight: 800; margin: 26px 0 12px; padding: 0; }
.cc-hero .lead { font-size: 1.02rem; line-height: 1.6; color: #DBE7FF; margin-bottom: 26px; }
.cc-feature { display: flex; gap: 14px; align-items: flex-start; margin: 16px 0; }
.cc-feature .ic { width: 38px; height: 38px; border-radius: 10px; background: rgba(255,255,255,.14);
  display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex: none; }
.cc-feature b { display: block; color: #fff; font-size: .98rem; }
.cc-feature span { color: #C7D8FF; font-size: .87rem; line-height: 1.45; }
.cc-depts { margin-top: 26px; display: flex; flex-wrap: wrap; gap: 8px; }
.cc-depts span { background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2);
  padding: 5px 13px; border-radius: 999px; font-size: .78rem; color: #fff; font-weight: 500; }

/* ---------- page header ---------- */
.cc-top { background: #fff; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 24px;
  margin-bottom: 18px; border-left: 5px solid #1D4ED8; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.cc-title { font-size: 1.45rem; font-weight: 800; color: #0F172A; letter-spacing: -.01em; }
.cc-sub { color: #64748B; font-size: .92rem; margin-top: 2px; }

/* ---------- KPI cards ---------- */
.kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin: 4px 0 18px; }
.kpi { background: #fff; border: 1px solid #E2E8F0; border-top: 4px solid var(--c); border-radius: 14px;
  padding: 16px 18px; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.kpi .l { font-size: .72rem; text-transform: uppercase; letter-spacing: .07em; color: #64748B; font-weight: 700; }
.kpi .v { font-size: 2.1rem; font-weight: 800; color: #0F172A; line-height: 1.25; }
@media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

/* ---------- pills + stepper ---------- */
.pill { display: inline-block; padding: 4px 13px; border-radius: 999px; font-size: .76rem; font-weight: 700; letter-spacing: .02em; }
.stepper { display: flex; align-items: center; margin: 12px 0 6px; flex-wrap: wrap; row-gap: 8px; }
.step { display: flex; align-items: center; gap: 8px; font-size: .8rem; color: #94A3B8; font-weight: 500; }
.step.done { color: #0F172A; font-weight: 600; }
.dot { width: 22px; height: 22px; border-radius: 50%; background: #E2E8F0; color: #64748B; display: flex;
  align-items: center; justify-content: center; font-size: .68rem; font-weight: 700; }
.step.done .dot { background: var(--c); color: #fff; }
.bar { flex: 1; height: 3px; background: #E2E8F0; margin: 0 10px; min-width: 28px; border-radius: 2px; }
.bar.done { background: var(--c); }

/* ---------- department reply ---------- */
.reply { background: #F0F6FF; border-left: 4px solid #1D4ED8; border-radius: 8px; padding: 12px 16px;
  margin-top: 12px; color: #1E293B; font-size: .92rem; line-height: 1.5; }
.reply .rh { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: #1D4ED8; margin-bottom: 4px; }
.reply.muted { background: #F8FAFC; border-left-color: #CBD5E1; color: #64748B; }

/* ---------- Streamlit widgets ---------- */
[class*="st-key-card"] { background: #fff; border: 1px solid #E2E8F0 !important; border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(15,23,42,.05); padding: 10px 14px 16px; margin-bottom: 6px; }
[data-testid="stForm"] { background: #fff; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px 22px;
  box-shadow: 0 1px 3px rgba(15,23,42,.05); }
[data-testid="stExpander"] { background: #fff; border: 1px solid #E2E8F0 !important; border-radius: 12px; margin-bottom: 8px; }
[data-testid="stExpander"] summary { font-weight: 600; }
.stButton > button, [data-testid="stFormSubmitButton"] > button { border-radius: 10px; font-weight: 600; padding: .5rem 1.3rem; }
button[data-baseweb="tab"] { font-weight: 600; font-size: .95rem; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { border-radius: 10px; }
[data-testid="stDataFrame"] { border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; }
h5 { font-weight: 700; color: #0F172A; margin-bottom: .2rem; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: #0B1F4B; }
[data-testid="stSidebar"] .stButton > button { width: 100%; background: rgba(255,255,255,.08); color: #fff;
  border: 1px solid rgba(255,255,255,.25); }
[data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,.18); color: #fff; border-color: #fff; }
.sb-brand { color: #fff; font-weight: 800; font-size: 1.15rem; margin: 4px 0 18px; }
.sb-card { display: flex; gap: 12px; align-items: center; background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.15); border-radius: 14px; padding: 14px; margin-bottom: 14px; }
.sb-avatar { width: 42px; height: 42px; border-radius: 50%; background: #3B82F6; color: #fff; font-weight: 800;
  display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex: none; }
.sb-name { color: #fff; font-weight: 700; font-size: .95rem; word-break: break-word; }
.sb-role { color: #A9C1F5; font-size: .76rem; margin-top: 1px; }
.sb-dept { display: inline-block; margin-top: 6px; background: rgba(59,130,246,.35); color: #fff; font-size: .72rem;
  padding: 2px 10px; border-radius: 999px; font-weight: 600; }
.sb-foot { color: #7F9CD6; font-size: .72rem; margin-top: 26px; line-height: 1.5; }

.cc-footer { text-align: center; color: #94A3B8; font-size: .78rem; margin-top: 34px; }
/* ---------- insights + alerts ---------- */
.ins { display: flex; gap: 12px; align-items: flex-start; padding: 10px 0; border-bottom: 1px solid #EEF2F7;
  font-size: .93rem; color: #1E293B; line-height: 1.45; }
.ins:last-child { border-bottom: none; }
.ins .ic { font-size: 1.05rem; width: 26px; flex: none; text-align: center; }
.alert-red { background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; border-radius: 10px;
  padding: 10px 14px; font-weight: 700; font-size: .92rem; margin-bottom: 8px; }
.alert-green { background: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; border-radius: 10px;
  padding: 12px 14px; font-weight: 600; font-size: .92rem; }
.ovd { display: flex; justify-content: space-between; gap: 10px; padding: 9px 0; border-bottom: 1px solid #EEF2F7; }
.ovd:last-child { border-bottom: none; }
.ovd .t { font-weight: 600; color: #0F172A; font-size: .9rem; }
.ovd .m { color: #64748B; font-size: .78rem; margin-top: 1px; }
.ovd .age { background: #FEE2E2; color: #991B1B; font-weight: 700; border-radius: 999px; padding: 3px 11px;
  font-size: .76rem; white-space: nowrap; align-self: center; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] label p { color: #C7D8FF !important; font-size: .82rem; }
.sb-sec { color: #7F9CD6; font-size: .7rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin: 6px 0 2px; }
</style>
""")
st.markdown(CSS, unsafe_allow_html=True)


# ======================================================================
# HELPERS
# ======================================================================
def api(method, path, body=None, params=None):
    headers = {"Authorization": f"Bearer {ss.token}"} if ss.token else {}
    try:
        r = requests.request(method, f"{API}{path}", json=body, params=params,
                             headers=headers, timeout=40)
    except requests.RequestException as e:
        st.error(f"Cannot reach the server: {e}")
        return None
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except Exception:
            detail = r.text
        if isinstance(detail, list):  # pydantic validation errors
            detail = "; ".join(d.get("msg", "") for d in detail)
        st.error(f"{r.status_code}: {detail}")
        return None
    return r.json()


def pill(status):
    bg, fg = PILL_STYLE[status]
    return (f'<div style="text-align:right"><span class="pill" '
            f'style="background:{bg};color:{fg}">{STATUS_LABELS[status]}</span></div>')


def stepper(status):
    color = STATUS_COLORS[status]
    last = "Rejected" if status == "rejected" else "Resolved"
    labels = ["Submitted", "In Progress", last]
    reached = {"pending": 1, "in_progress": 2, "resolved": 3, "rejected": 3}[status]
    parts = []
    for i, label in enumerate(labels, start=1):
        done = i <= reached
        cls = "step done" if done else "step"
        mark = "✓" if done else str(i)
        parts.append(f'<div class="{cls}"><span class="dot">{mark}</span>{label}</div>')
        if i < 3:
            bar_cls = "bar done" if i < reached else "bar"
            parts.append(f'<div class="{bar_cls}"></div>')
    return f'<div class="stepper" style="--c:{color}">' + "".join(parts) + "</div>"


def reply_box(remarks):
    if remarks:
        return (f'<div class="reply"><div class="rh">Department response</div>'
                f'{esc(remarks)}</div>')
    return '<div class="reply muted">Awaiting a response from the department.</div>'


def page_header(title, subtitle):
    st.markdown(h(f'<div class="cc-top"><div class="cc-title">{esc(title)}</div>'
                  f'<div class="cc-sub">{esc(subtitle)}</div></div>'),
                unsafe_allow_html=True)


def kpi_cards(total, by_status):
    items = [
        ("Total complaints", total, "#1D4ED8"),
        ("Pending", by_status["pending"], STATUS_COLORS["pending"]),
        ("In progress", by_status["in_progress"], STATUS_COLORS["in_progress"]),
        ("Resolved", by_status["resolved"], STATUS_COLORS["resolved"]),
        ("Rejected", by_status["rejected"], STATUS_COLORS["rejected"]),
    ]
    cells = "".join(
        f'<div class="kpi" style="--c:{c}"><div class="l">{l}</div><div class="v">{v}</div></div>'
        for l, v, c in items)
    st.markdown(f'<div class="kpi-grid">{cells}</div>', unsafe_allow_html=True)


def bar_chart_h(data, color="#2563EB"):
    """Horizontal bars: readable labels, value shown at the end of each bar."""
    df = pd.DataFrame({"label": list(data.keys()), "count": list(data.values())})
    base = alt.Chart(df).encode(
        y=alt.Y("label:N", sort="-x", title=None,
                axis=alt.Axis(labelLimit=340, labelFontSize=13, ticks=False, domain=False)),
        x=alt.X("count:Q", title="Number of complaints",
                axis=alt.Axis(tickMinStep=1, format="d", gridColor="#EEF2F7", domain=False)),
    )
    bars = base.mark_bar(color=color, cornerRadiusEnd=5, size=22)
    labels = base.mark_text(align="left", dx=6, fontSize=14, fontWeight=600,
                            color="#0F172A").encode(text="count:Q")
    return (bars + labels).properties(height=max(170, 46 * len(df))).configure(background="#FFFFFF").configure_view(strokeWidth=0)


def status_donut(by_status):
    df = pd.DataFrame({
        "Status": [STATUS_LABELS[k] for k in by_status],
        "Complaints": list(by_status.values()),
    })
    df = df[df["Complaints"] > 0]
    return alt.Chart(df).mark_arc(innerRadius=62, outerRadius=112, stroke="#fff", strokeWidth=2).encode(
        theta="Complaints:Q",
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(domain=list(STATUS_LABELS.values()),
                            range=list(STATUS_COLORS.values())),
            legend=alt.Legend(title=None, orient="bottom", labelFontSize=13, symbolType="circle"),
        ),
        tooltip=["Status", "Complaints"],
    ).properties(height=290).configure(background="#FFFFFF").configure_view(strokeWidth=0)


def footer():
    st.markdown('<div class="cc-footer">CampusConnect · Smart Campus Complaint &amp; Feedback '
                'Management · BIIT Software Engineering Society</div>', unsafe_allow_html=True)



# ======================================================================
# INSIGHTS, OVERDUE ALERTS AND REPORT EXPORT
# ======================================================================
LOCAL_TZ = "Asia/Karachi"


def get_sla():
    return int(ss.get("sla_hours", 48))


def to_ts(value):
    return pd.to_datetime(value, utc=True)


def age_hours(c):
    return (pd.Timestamp.now(tz="UTC") - to_ts(c["created_at"])).total_seconds() / 3600


def fmt_hours(hours):
    hours = max(0, int(hours))
    days, rem = divmod(hours, 24)
    return f"{days}d {rem}h" if days else f"{rem}h"


def is_overdue(c):
    return c["status"] == "pending" and age_hours(c) > get_sla()


def local_time(value):
    return to_ts(value).tz_convert(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")


def safe_cell(value):
    """Stops spreadsheet formula injection in exported CSV files."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def report_df(rows):
    return pd.DataFrame([{
        "Ticket": c["id"][:8],
        "Title": safe_cell(c["title"]),
        "Category": c["category"],
        "Department": c["department"],
        "Student": safe_cell(c["student_name"]),
        "Status": STATUS_LABELS[c["status"]],
        "Overdue": "Yes" if is_overdue(c) else "No",
        "Department response": safe_cell(c.get("remarks")),
        "Submitted": local_time(c["created_at"]),
        "Last update": local_time(c["updated_at"]) if c.get("updated_at") else "",
    } for c in rows])


def report_button(rows, key, label="⬇️ Download report (CSV)"):
    if not rows:
        return
    csv = report_df(rows).to_csv(index=False).encode("utf-8-sig")
    stamp = pd.Timestamp.now(tz=LOCAL_TZ).strftime("%Y%m%d_%H%M")
    st.download_button(label, csv, file_name=f"campusconnect_report_{stamp}.csv",
                       mime="text/csv", key=key)


def insight_items(s, rows, is_super):
    total = s["total"]
    resolved = s["by_status"]["resolved"]
    items = []
    if s["by_category"]:
        cat, n = max(s["by_category"].items(), key=lambda kv: kv[1])
        plural = "s" if n != 1 else ""
        items.append(("📌", f"Most reported issue: <b>{esc(cat)}</b> "
                            f"({n} complaint{plural}, {round(100 * n / total)}% of all)."))
    if is_super and s["by_department"]:
        dept, n = max(s["by_department"].items(), key=lambda kv: kv[1])
        plural = "s" if n != 1 else ""
        items.append(("🏢", f"Busiest department: <b>{esc(dept)}</b> with {n} complaint{plural}."))
    pending = s["by_status"]["pending"]
    if pending:
        items.append(("⏳", f"<b>{pending}</b> complaint(s) are still waiting for a first response."))
    items.append(("✅", f"Resolution rate: <b>{round(100 * resolved / total)}%</b> "
                        f"({resolved} of {total} resolved)."))
    spans = [(to_ts(c["updated_at"]) - to_ts(c["created_at"])).total_seconds() / 3600
             for c in rows if c["status"] == "resolved" and c.get("updated_at")]
    if spans:
        items.append(("⏱️", f"Average time to resolve: <b>{fmt_hours(sum(spans) / len(spans))}</b>."))
    return items


def attention_html(rows):
    overdue = sorted([c for c in rows if is_overdue(c)], key=age_hours, reverse=True)
    if not overdue:
        return (f'<div class="alert-green">✅ No overdue complaints. Every pending complaint is '
                f'younger than {get_sla()} hours.</div>')
    top = "".join(
        f'<div class="ovd"><div><div class="t">{esc(c["title"])}</div>'
        f'<div class="m">{esc(c["department"])} · {esc(c["student_name"])}</div></div>'
        f'<div class="age">Waiting {fmt_hours(age_hours(c))}</div></div>'
        for c in overdue[:5])
    more = len(overdue) - 5
    tail = f'<div class="m" style="margin-top:6px">+ {more} more overdue</div>' if more > 0 else ""
    return (f'<div class="alert-red">🚨 {len(overdue)} complaint(s) pending for more than '
            f'{get_sla()} hours</div>{top}{tail}')


def trend_chart(rows):
    ts = pd.to_datetime([c["created_at"] for c in rows], utc=True).tz_convert(LOCAL_TZ)
    days = ts.tz_localize(None).normalize()
    counts = pd.Series(1, index=days).groupby(level=0).sum()
    full = pd.date_range(counts.index.min(), counts.index.max(), freq="D")
    df = pd.DataFrame({"Day": full, "Complaints": counts.reindex(full, fill_value=0).values})
    base = alt.Chart(df).encode(
        x=alt.X("Day:T", title=None,
                axis=alt.Axis(format="%d %b", labelFontSize=12, grid=False, labelOverlap=True,
                              tickCount={"interval": "day", "step": max(1, len(full) // 8)})),
        y=alt.Y("Complaints:Q", title="Complaints submitted",
                axis=alt.Axis(tickMinStep=1, format="d", gridColor="#EEF2F7", domain=False)),
        tooltip=[alt.Tooltip("Day:T", format="%d %b %Y"), "Complaints"],
    )
    chart = (base.mark_area(color="#2563EB", opacity=0.12)
             + base.mark_line(color="#2563EB", strokeWidth=3)
             + base.mark_point(color="#2563EB", filled=True, size=70))
    return chart.properties(height=240).configure(background="#FFFFFF").configure_view(strokeWidth=0)


# ======================================================================
# AUTH SCREEN
# ======================================================================
def auth_screen():
    left, right = st.columns([1.1, 1], gap="large")

    with left:
        st.markdown(h("""
        <div class="cc-hero">
          <div class="brand">🏫 CampusConnect</div>
          <h1>Your campus voice,<br>heard and tracked.</h1>
          <div class="lead">A single place to report problems with campus facilities and services,
          follow every step of the resolution and get a clear answer from the responsible department.</div>
          <div class="cc-feature"><div class="ic">📝</div><div><b>Report in seconds</b>
            <span>Pick a category, describe the issue and attach an image if needed.</span></div></div>
          <div class="cc-feature"><div class="ic">🧭</div><div><b>Automatic routing</b>
            <span>Every complaint goes straight to the right department. No manual forwarding.</span></div></div>
          <div class="cc-feature"><div class="ic">📍</div><div><b>Live status tracking</b>
            <span>See whether your complaint is pending, in progress, resolved or rejected.</span></div></div>
          <div class="cc-feature"><div class="ic">💬</div><div><b>Transparent responses</b>
            <span>Read the department's remarks directly on your complaint.</span></div></div>
          <div class="cc-depts"><span>Cafeteria</span><span>Library</span>
            <span>Laboratories &amp; IT</span><span>Teaching &amp; Academic Affairs</span></div>
        </div>
        """), unsafe_allow_html=True)

    with right:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["Sign in", "Create student account"])

        with tab_login:
            with st.form("login"):
                st.markdown("##### Welcome back")
                email = st.text_input("Email address", placeholder="name@biit.edu")
                pw = st.text_input("Password", type="password", placeholder="Your password")
                if st.form_submit_button("Sign in", type="primary"):
                    d = api("POST", "/auth/login", {"email": email, "password": pw})
                    if d:
                        ss.token, ss.user = d["access_token"], d["user"]
                        st.rerun()
            with st.expander("Demo administrator accounts"):
                st.markdown("Password for all accounts: `admin123`")
                st.code("super@biit.edu      (Super Administrator)\n"
                        "cafeteria@biit.edu  (Cafeteria)\n"
                        "library@biit.edu    (Library)\n"
                        "lab@biit.edu        (Laboratory / IT)\n"
                        "academic@biit.edu   (Teaching / Academic)")

        with tab_reg:
            with st.form("reg"):
                st.markdown("##### Create your account")
                n = st.text_input("Full name", placeholder="Your full name")
                e = st.text_input("Email address ", placeholder="name@example.com")
                p = st.text_input("Password (min. 6 characters)", type="password")
                if st.form_submit_button("Create account", type="primary"):
                    d = api("POST", "/auth/register", {"name": n, "email": e, "password": p})
                    if d:
                        ss.token, ss.user = d["access_token"], d["user"]
                        st.rerun()
    footer()


# ======================================================================
# STUDENT
# ======================================================================
def student_view():
    page_header("Student Portal", "Submit complaints and follow their progress.")
    t1, t2 = st.tabs(["📝  New Complaint", "📂  My Complaints"])

    with t1:
        cats = api("GET", "/complaints/categories") or []
        with st.form("new_complaint", clear_on_submit=True):
            st.markdown("##### Describe your issue")
            st.caption("Your complaint is routed automatically to the responsible department.")
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Category", cats)
            title = c2.text_input("Title", placeholder="Short summary of the problem")
            desc = st.text_area("Details", height=150,
                                placeholder="What happened, where and when? (min. 10 characters)")
            img = st.text_input("Supporting image link (optional)", placeholder="https://...")
            if st.form_submit_button("Submit complaint", type="primary"):
                d = api("POST", "/complaints", {
                    "category": cat, "title": title,
                    "description": desc, "image_url": img or None})
                if d:
                    st.success(f"Complaint submitted and routed to **{d['department']}**. "
                               f"Ticket #{d['id'][:8]}")

    with t2:
        top = st.columns([4, 1.4, 1])
        flt = top[1].selectbox("Show", ["All"] + [STATUS_LABELS[s] for s in STATUSES],
                               label_visibility="collapsed")
        if top[2].button("Refresh"):
            st.rerun()
        rows = api("GET", "/complaints/mine") or []
        open_n = sum(1 for c in rows if c["status"] in ("pending", "in_progress"))
        done_n = sum(1 for c in rows if c["status"] == "resolved")
        top[0].caption(f"{len(rows)} complaint(s)  ·  {open_n} open  ·  {done_n} resolved")
        if flt != "All":
            rows = [c for c in rows if STATUS_LABELS[c["status"]] == flt]
        if not rows:
            st.info("No complaints to show.")
        for c in rows:
            with st.container(border=True, key=f"card_mine_{c['id']}"):
                head, tag = st.columns([5, 1.4])
                head.markdown(f"#### {c['title']}")
                tag.markdown(pill(c["status"]), unsafe_allow_html=True)
                st.caption(f"📂 {c['category']}   ·   🏢 {c['department']}   ·   "
                           f"🕒 {c['created_at'][:16].replace('T', ' ')}   ·   Ticket #{c['id'][:8]}")
                st.write(c["description"])
                if c.get("image_url"):
                    st.image(c["image_url"], width=320)
                st.markdown(stepper(c["status"]), unsafe_allow_html=True)
                st.markdown(reply_box(c.get("remarks")), unsafe_allow_html=True)
    footer()


# ======================================================================
# ADMIN
# ======================================================================
def admin_view():
    is_super = ss.user["role"] == "super_admin"
    if is_super:
        page_header("Administration Console", "Complaints and analytics across all departments.")
    else:
        page_header(f"{ss.user.get('department')} Administration",
                    "Complaints assigned to your department.")
    t1, t2 = st.tabs(["📊  Dashboard & Reports", "🗂️  Manage Complaints"])

    with t1:
        s = api("GET", "/admin/stats")
        all_rows = api("GET", "/admin/complaints") or []
        if s:
            kpi_cards(s["total"], s["by_status"])
            if s["total"] == 0 or not all_rows:
                st.info("No complaints yet. Insights and charts appear as soon as students submit complaints.")
            else:
                st.caption(f"Scope: {s['scope']}")
                ins_col, att_col = st.columns(2)
                with ins_col:
                    with st.container(border=True, key="card_insights"):
                        st.markdown("##### 💡 Smart insights")
                        st.markdown("".join(
                            f'<div class="ins"><span class="ic">{ic}</span><div>{txt}</div></div>'
                            for ic, txt in insight_items(s, all_rows, is_super)),
                            unsafe_allow_html=True)
                with att_col:
                    with st.container(border=True, key="card_attention"):
                        st.markdown("##### 🚨 Needs attention")
                        st.markdown(attention_html(all_rows), unsafe_allow_html=True)

                left, right = st.columns(2)
                with left:
                    with st.container(border=True, key="card_chart_a"):
                        if is_super:
                            st.markdown("##### Complaints by department")
                            st.altair_chart(bar_chart_h(s["by_department"], "#2563EB"))
                        else:
                            st.markdown("##### Complaints by category")
                            st.altair_chart(bar_chart_h(s["by_category"], "#7C3AED"))
                with right:
                    with st.container(border=True, key="card_chart_b"):
                        st.markdown("##### Complaints by status")
                        st.altair_chart(status_donut(s["by_status"]))
                with st.container(border=True, key="card_trend"):
                    st.markdown("##### Complaints over time")
                    st.altair_chart(trend_chart(all_rows))
                if is_super and s["by_category"]:
                    with st.container(border=True, key="card_chart_c"):
                        st.markdown("##### Most common issues (by category)")
                        st.altair_chart(bar_chart_h(s["by_category"], "#7C3AED"))
                report_button(all_rows, "dl_dashboard", "⬇️ Download full report (CSV)")

    with t2:
        cats = api("GET", "/complaints/categories") or []
        with st.container(border=True, key="card_filters"):
            f = st.columns(4 if is_super else 3)
            status = f[0].selectbox("Status", ["All"] + STATUSES)
            q = f[1].text_input("Search", placeholder="Title or description")
            cat = f[2].selectbox("Category", ["All"] + cats)
            dept = None
            if is_super:
                dept = f[3].selectbox("Department", ["All", "Cafeteria", "Library",
                                                     "Laboratory/IT", "Teaching/Academic"])
            only_overdue = st.checkbox(f"Show overdue only (pending for more than {get_sla()} hours)")
        params = {}
        if status != "All":
            params["status"] = status
        if cat != "All":
            params["category"] = cat
        if q:
            params["q"] = q
        if dept and dept != "All":
            params["department"] = dept

        rows = api("GET", "/admin/complaints", params=params) or []
        if only_overdue:
            rows = [c for c in rows if is_overdue(c)]
        info, dl = st.columns([4, 1.6])
        info.caption(f"{len(rows)} complaint(s)")
        with dl:
            report_button(rows, "dl_manage")
        if rows:
            table = pd.DataFrame([{
                "Status": f"{BADGE[c['status']]} {STATUS_LABELS[c['status']]}"
                          + ("  ⚠️ Overdue" if is_overdue(c) else ""),
                "Title": c["title"],
                "Department": c["department"],
                "Student": c["student_name"],
                "Waiting": fmt_hours(age_hours(c)) if c["status"] in ("pending", "in_progress") else "—",
                "Submitted": local_time(c["created_at"]),
            } for c in rows])
            st.dataframe(table, hide_index=True)
            st.markdown("##### Open a complaint to respond")
        else:
            st.info("No complaints match these filters.")
        for c in rows:
            icon = "⚠️" if is_overdue(c) else BADGE[c["status"]]
            head = f"{icon}  {c['title']}   ·   {c['department']}   ·   {c['student_name']}"
            with st.expander(head):
                st.caption(f"📂 {c['category']}   ·   🕒 {local_time(c['created_at'])}"
                           f"   ·   Ticket #{c['id'][:8]}")
                st.write(c["description"])
                if c.get("image_url"):
                    st.image(c["image_url"], width=320)
                st.markdown(stepper(c["status"]), unsafe_allow_html=True)
                with st.form(f"upd_{c['id']}"):
                    a, b = st.columns([1, 2])
                    ns = a.selectbox("New status", STATUSES,
                                     index=STATUSES.index(c["status"]))
                    rm = b.text_area("Response to the student (required for resolved or rejected)",
                                     value=c.get("remarks") or "", height=100)
                    if st.form_submit_button("Save update", type="primary"):
                        if api("PATCH", f"/admin/complaints/{c['id']}",
                               {"status": ns, "remarks": rm or None}):
                            st.success("Updated")
                            st.rerun()
    footer()


# ======================================================================
# SIDEBAR + ROUTER
# ======================================================================
def sidebar():
    u = ss.user
    initial = esc((u.get("name") or "?")[:1].upper())
    dept = u.get("department")
    dept_html = f'<div class="sb-dept">{esc(dept)}</div>' if dept else ""
    with st.sidebar:
        st.markdown(h(
            f'<div class="sb-brand">🏫 CampusConnect</div>'
            f'<div class="sb-card"><div class="sb-avatar">{initial}</div><div>'
            f'<div class="sb-name">{esc(u.get("name"))}</div>'
            f'<div class="sb-role">{ROLE_LABELS.get(u["role"], u["role"])}</div>{dept_html}'
            f'</div></div>'), unsafe_allow_html=True)
        if u["role"] != "student":
            st.markdown('<div class="sb-sec">Alert settings</div>', unsafe_allow_html=True)
            st.selectbox("Flag pending complaints as overdue after", [1, 6, 24, 48, 72],
                         index=3, key="sla_hours", format_func=lambda x: f"{x} hours")
        if st.button("Sign out"):
            ss.token = ss.user = None
            st.rerun()
        st.markdown('<div class="sb-foot">BIIT Software Engineering Society<br>'
                    'Application Development Competition</div>', unsafe_allow_html=True)


if not ss.token:
    auth_screen()
else:
    sidebar()
    if ss.user["role"] == "student":
        student_view()
    else:
        admin_view()