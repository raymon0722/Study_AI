import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import io

st.set_page_config(
    page_title="Study AI",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# CSS 스타일링 (모바일 반응형 최적화)
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
.stApp { background: #f7f9fc; color: #182230; }
.block-container { max-width: 1180px; padding-top: 1.5rem; padding-bottom: 3rem; }

/* 헤더 카드 */
.hero {
    background: linear-gradient(120deg, #1e3a8a 0%, #3b82f6 100%);
    color: white;
    border-radius: 18px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
}
.hero h1 { color: white; font-size: 1.8rem; margin: .25rem 0 .35rem 0; font-weight: 800; }
.hero p { color: #dbeafe; margin: 0; font-size: 0.95rem; }

.section-title { font-size: 1.2rem; font-weight: 750; color: #1e3a8a; margin: 1.2rem 0 .8rem; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: #e2e8f0; padding: 6px; border-radius: 12px; }
.stTabs [data-baseweb="tab"] { height: 44px; border-radius: 8px; font-weight: 700; }
.stTabs [aria-selected="true"] { background: white !important; color: #1d4ed8 !important; }

/* 데스크톱 기준 달력 카드 스타일 */
.day-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px;
    min-height: 120px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    margin-bottom: 6px;
}
.day-header {
    font-weight: 700;
    font-size: 0.88rem;
    color: #334155;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 4px;
    margin-bottom: 6px;
}
.day-phase {
    font-size: 0.75rem;
    font-weight: 600;
    color: #2563eb;
    background: #eff6ff;
    padding: 2px 7px;
    border-radius: 5px;
    display: inline-block;
    margin-bottom: 6px;
}
.day-task {
    font-size: 0.8rem;
    color: #475569;
    line-height: 1.4;
}

/* 📱 모바일 반응형 미디어 쿼리 (768px 이하) */
@media (max-width: 768px) {
    .block-container { padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; }
    .hero { padding: 1.2rem; border-radius: 14px; }
    .hero h1 { font-size: 1.5rem; }
    
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    
    .day-card {
        min-height: auto !important;
        padding: 14px 16px !important;
        margin-bottom: 8px !important;
    }
    .day-header { font-size: 0.95rem !important; }
    .day-task { font-size: 0.88rem !important; }
}
</style>
""", unsafe_allow_html=True)

DEFAULT_SUBJECTS = ["국어", "수학", "영어", "한국사", "통합사회", "통합과학", "정보"]

DEFAULTS = {
    "국어":  {"score": 75.0, "hours": 3.0, "accuracy": 65.0, "reviews": 2, "error": "개념 혼동", "mastery": 3},
    "수학":  {"score": 78.0, "hours": 5.0, "accuracy": 62.0, "reviews": 2, "error": "문제 접근법을 모름", "mastery": 3},
    "영어":  {"score": 88.0, "hours": 3.0, "accuracy": 82.0, "reviews": 3, "error": "어휘·표현 부족", "mastery": 4},
    "한국사":{"score": 80.0, "hours": 2.0, "accuracy": 75.0, "reviews": 2, "error": "암기 후 망각", "mastery": 3},
    "통합사회":{"score": 76.0, "hours": 2.0, "accuracy": 68.0, "reviews": 1, "error": "개념 혼동", "mastery": 3},
    "통합과학":{"score": 85.0, "hours": 3.0, "accuracy": 84.0, "reviews": 3, "error": "자료 해석 실수", "mastery": 4},
    "정보":  {"score": 90.0, "hours": 2.0, "accuracy": 88.0, "reviews": 3, "error": "실수·계산 오류", "mastery": 4},
}
ERROR_TYPES = ["개념 혼동", "문제 접근법을 모름", "계산·풀이 실수", "시간 부족", "암기 후 망각", "어휘·표현 부족", "자료 해석 실수", "실수·계산 오류", "기타"]

# 세션 데이터 초기화
if "all_subjects" not in st.session_state:
    st.session_state.all_subjects = DEFAULT_SUBJECTS.copy()

if "subject_data" not in st.session_state:
    st.session_state.subject_data = {s: DEFAULTS[s].copy() for s in DEFAULT_SUBJECTS}

if "selected_subjects" not in st.session_state:
    st.session_state.selected_subjects = DEFAULT_SUBJECTS.copy()

def read_subject(s):
    return st.session_state.subject_data[s]

def set_subject(s, key, value):
    st.session_state.subject_data[s][key] = value

def estimate_score(d):
    score = float(d["score"])
    hours = float(d["hours"])
    accuracy = float(d["accuracy"])
    reviews = int(d["reviews"])

    hour_effect = max(-2.5, min(1.5, (hours - 3.0) * 0.35))
    accuracy_effect = max(-3.5, min(2.0, (accuracy - 70.0) * 0.10))
    review_effect = max(-2.0, min(1.5, (reviews - 2) * 0.55))
    consistency_effect = 0.4 if hours >= 3 and reviews >= 2 else -0.4 if hours < 1.5 and reviews == 0 else 0.0
    change = hour_effect + accuracy_effect + review_effect + consistency_effect
    change = max(-6.0, min(4.0, change))
    predicted = max(0.0, min(100.0, score + change))
    return predicted, change

def make_feedback(subject, d):
    acc, hours, reviews, error, mastery = d["accuracy"], d["hours"], d["reviews"], d["error"], d["mastery"]
    messages = []

    if acc < 50 or mastery <= 2:
        status_tag, status_msg = "🚨 취약 단계", "개념 이해 및 정답률 보완이 시급한 과목."
    elif acc < 75 or mastery == 3:
        status_tag, status_msg = "⚠️ 발전 단계", "기본 틀은 갖추었으나 특정 응용 문제에서 정체되는 과목."
    else:
        status_tag, status_msg = "✅ 안정 단계", "정답률과 이해도가 양호하여 유지가 중요한 과목."
    messages.append((f"진단 결과 [{status_tag}]", status_msg))

    if acc < 50:
        messages.append(("우선 과제", "정답률 저조에 따른 개념 재정립 필요."))
        messages.append(("실행 방법", "대표 개념 2~3개 정리 및 기본 문제 3개 풀이 후 풀이 근거 점검."))
    elif acc < 70:
        messages.append(("우선 과제", "문제 적용력 부족. 오답 유형별 분류 필요."))
        messages.append(("실행 방법", "최근 오답 5개 분류(개념/접근법/실수) 및 동일 유형 신규 문제 풀이 권장."))
    elif acc < 85:
        messages.append(("우선 과제", "기본 이해 완료. 특정 응용 유형 정확도 보완 필요."))
        messages.append(("실행 방법", "오답 조건 및 첫 단계 비교를 통한 공통 패턴 분석 권장."))
    else:
        messages.append(("우선 과제", "정답률 양호. 풀이 소요 시간 단축 및 응용력 유지 제안."))
        messages.append(("실행 방법", "풀이 시간이 길었던 문항의 간결한 풀이법 탐색 권장."))

    error_advice = {
        "개념 혼동": "대립되는 개념 간 차이점 비교 표 작성 권장.",
        "문제 접근법을 모름": "문제 조건·구하는 값·적용 개념을 3줄로 요약하는 연습 필요.",
        "계산·풀이 실수": "부호/단위/조건 검산 체크리스트 작성 및 적용 필요.",
        "시간 부족": "문항별 소요 시간 측정 및 쉬운 문제 우선 해결 순서 정립 필요.",
        "암기 후 망각": "1일/3일/7일 주기 회상 복습 진행 권장.",
        "어휘·표현 부족": "핵심 어휘 문맥 정리 및 예문 작성 연습 권장.",
        "자료 해석 실수": "그래프·표의 축/단위/범례 우선 확인 절차 준수 필요.",
        "실수·계산 오류": "자주 발생하는 실수 유형 오답 노트 작성 권장.",
        "기타": "막힌 지점에 대한 원인 단문 정리 권장."
    }
    messages.append(("오답 원인 처방", f"[{error}] {error_advice.get(error, error_advice['기타'])}"))

    if reviews == 0:
        messages.append(("복습 설계", "복습 기록 부재. 취침 전 및 익일 10분 회상 학습 필요."))
    elif reviews <= 2:
        messages.append(("복습 설계", "복습 빈도 미흡. 핵심 개념 중심 1~2일 간격 복습 권장."))
    else:
        messages.append(("복습 설계", "복습 양호. 백지 복습 또는 정답 은폐 후 회상 방식 권장."))

    if hours < 1.5:
        messages.append(("시간 배분", f"{subject} 학습 시간 부족. 주 3회 30분 단위 시간 확보 필요."))
    elif hours >= 6:
        messages.append(("시간 배분", "학습 시간 충분. 집중도 유지 여부 및 오답 분석 비중 점검 필요."))
    else:
        messages.append(("시간 배분", "현재 학습 시간 유지. 문제 풀이와 오답 분석 비율 균형 유지 권장."))

    return messages

# 헤더
st.markdown("""
<div class="hero">
  <h1>Study AI</h1>
  <p>학습 데이터 기반 성적 추정 및 모바일 맞춤 플래너 시스템</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# 1순위: 최상단 성적 및 학습 데이터 입력 (+ 과목 직접 추가)
# -----------------------------
st.markdown('<div class="section-title">📌 1. 성적 및 학습 데이터 입력</div>', unsafe_allow_html=True)

with st.container(border=True):
    c_add1, c_add2 = st.columns([4, 1])
    with c_add1:
        new_sub = st.text_input("새로운 과목 추가", placeholder="예: 물리학1, 제2외국어", label_visibility="collapsed")
    with c_add2:
        if st.button("➕ 과목 추가", use_container_width=True):
            if new_sub and new_sub not in st.session_state.all_subjects:
                st.session_state.all_subjects.append(new_sub)
                st.session_state.subject_data[new_sub] = {
                    "score": 70.0, "hours": 2.0, "accuracy": 70.0, "reviews": 2, "error": "개념 혼동", "mastery": 3
                }
                st.session_state.selected_subjects.append(new_sub)
                st.success(f"'{new_sub}' 과목이 추가되었습니다.")
                st.rerun()

    chosen = st.multiselect("분석 과목 선택", st.session_state.all_subjects, default=st.session_state.selected_subjects)
    if chosen:
        st.session_state.selected_subjects = chosen
    else:
        st.warning("분석할 과목을 최소 1개 이상 선택 필요.")

    for s in st.session_state.selected_subjects:
        d = read_subject(s)
        with st.expander(f"📝 {s} 데이터 입력", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                set_subject(s, "score", st.number_input("직전 점수", 0.0, 100.0, float(d["score"]), 1.0, key=f"{s}_score"))
                set_subject(s, "hours", st.number_input("주간 공부 시간(hr)", 0.0, 50.0, float(d["hours"]), 0.5, key=f"{s}_hours"))
            with c2:
                set_subject(s, "accuracy", st.number_input("정답률 (%)", 0.0, 100.0, float(d["accuracy"]), 1.0, key=f"{s}_accuracy"))
                set_subject(s, "reviews", st.number_input("주간 복습 횟수", 0, 20, int(d["reviews"]), 1, key=f"{s}_reviews"))
            with c3:
                set_subject(s, "mastery", st.slider("개념 이해도 (1~5)", 1, 5, int(d["mastery"]), key=f"{s}_mastery"))
                set_subject(s, "error", st.selectbox("주요 오답 원인", ERROR_TYPES, index=ERROR_TYPES.index(d["error"]), key=f"{s}_error"))

active_subjects = st.session_state.selected_subjects
results = {}
for s in active_subjects:
    d = read_subject(s)
    pred, delta = estimate_score(d)
    results[s] = {"pred": pred, "delta": delta, "data": d}

st.divider()

# -----------------------------
# 2순위: 탭 구성
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📈  성적 예상 & 역량 분석", "🧠  학습 전략 피드백", "🗓️  달력 스터디 플래너"])

with tab1:
    st.markdown('<div class="section-title">과목별 예상 점수</div>', unsafe_allow_html=True)
    if results:
        cols = st.columns(min(4, len(results)))
        for i, (s, r) in enumerate(results.items()):
            with cols[i % len(cols)]:
                st.metric(s, f"{r['pred']:.1f}점", f"{r['delta']:+.1f}점")
        
        col_bar, col_radar = st.columns([1, 1])
        
        with col_bar:
            st.markdown("##### 📊 직전 점수 vs 예상 점수")
            chart_df = pd.DataFrame({
                "과목": list(results.keys()),
                "직전 점수": [r["data"]["score"] for r in results.values()],
                "예상 점수": [r["pred"] for r in results.values()]
            }).set_index("과목")
            st.bar_chart(chart_df)
            
        with col_radar:
            st.markdown("##### 🕸️ 과목별 정답률 방사형(Radar) 비교")
            fig = go.Figure()
            categories = list(results.keys())
            accuracies = [r["data"]["accuracy"] for r in results.values()]
            masteries = [r["data"]["mastery"] * 20 for r in results.values()]
            
            fig.add_trace(go.Scatterpolar(
                r=accuracies, theta=categories, fill='toself', name='정답률 (%)'
            ))
            fig.add_trace(go.Scatterpolar(
                r=masteries, theta=categories, fill='toself', name='개념 이해도 환산 (100점 만점)'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                margin=dict(l=40, r=40, t=20, b=20),
                height=320
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("상단에서 과목을 선택 필요.")

with tab2:
    st.markdown('<div class="section-title">과목별 맞춤 전략 리포트</div>', unsafe_allow_html=True)
    if results:
        critical_cnt = sum(1 for r in results.values() if r["data"]["accuracy"] < 50 or r["data"]["mastery"] <= 2)
        warning_cnt = sum(1 for r in results.values() if 50 <= r["data"]["accuracy"] < 75 or r["data"]["mastery"] == 3)
        stable_cnt = len(results) - critical_cnt - warning_cnt

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("🚨 취약 과목", f"{critical_cnt}개")
        mc2.metric("⚠️ 발전 과목", f"{warning_cnt}개")
        mc3.metric("✅ 안정 과목", f"{stable_cnt}개")
        st.divider()

        for s, r in results.items():
            d = r["data"]
            with st.expander(f"📘 {s} 학습 진단 및 실행 지침", expanded=True):
                for title, message in make_feedback(s, d):
                    st.markdown(f"**• {title}**: {message}")
    else:
        st.info("상단에서 과목을 선택 필요.")

with tab3:
    st.markdown('<div class="section-title">달력형 시험 플래너</div>', unsafe_allow_html=True)
    st.caption("📱 스마트폰 접속 시 아래 일자별 카드가 세로로 깔끔하게 정렬됩니다.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        exam_date = st.date_input("시험 시작일", value=date.today() + timedelta(days=14), min_value=date.today())
    with c2:
        weekday_hours = st.number_input("평일 공부 시간(시간)", min_value=0.5, max_value=12.0, value=3.0, step=0.5)
    with c3:
        weekend_hours = st.number_input("주말 공부 시간(시간)", min_value=0.5, max_value=16.0, value=6.0, step=0.5)

    if results:
        priorities = {}
        for s, r in results.items():
            d = r["data"]
            weakness = (100 - d["accuracy"]) / 100 + (5 - d["mastery"]) / 5
            priorities[s] = {"weight": 3 * (1 + weakness), "error": d["error"]}

        days_left = max(1, (exam_date - date.today()).days)
        st.info(f"시험까지 남은 기간: 총 {days_left}일")

        total_weight = sum(v["weight"] for v in priorities.values()) or 1
        weeks = (days_left // 7) + (1 if days_left % 7 != 0 else 0)
        
        # 다운로드용 스케줄 데이터 프레임 생성
        export_rows = []
        
        for w in range(weeks):
            st.markdown(f"##### 📅 {w+1}주차 플랜")
            cols = st.columns(7)
            for day_idx in range(w * 7, min((w + 1) * 7, days_left)):
                col_idx = day_idx % 7
                current_date = date.today() + timedelta(days=day_idx)
                is_weekend = current_date.weekday() >= 5
                daily_hours = weekend_hours if is_weekend else weekday_hours
                
                phase_ratio = (day_idx + 1) / days_left
                if phase_ratio <= 0.45:
                    phase = "개념/진도"
                elif phase_ratio <= 0.8:
                    phase = "유형/오답"
                else:
                    phase = "파이널/회상"

                tasks = []
                for s, v in priorities.items():
                    h = daily_hours * v["weight"] / total_weight
                    if h >= 0.5:
                        tasks.append(f"• {s}({h:.1f}h)")

                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="day-card">
                        <div class="day-header">{current_date.strftime('%m/%d(%a)')} {'(주말)' if is_weekend else ''}</div>
                        <div class="day-phase">{phase}</div>
                        <div class="day-task">{'<br>'.join(tasks)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.checkbox("완료", key=f"chk_{current_date.strftime('%Y%m%d')}")
                
                # 데이터 저장
                export_rows.append({
                    "날짜": current_date.strftime('%Y-%m-%d (%a)'),
                    "구분": "주말" if is_weekend else "평일",
                    "학습 단계": phase,
                    "할 일 및 목표 시간": ", ".join([t.replace("• ", "") for t in tasks])
                })
            st.markdown("<br>", unsafe_allow_html=True)

        # -----------------------------
        # 스터디 플래너 파일 다운로드 버튼 (데이터 소실 방지)
        # -----------------------------
        st.markdown('<div class="section-title">💾 스터디 플래너 저장 (소실 방지)</div>', unsafe_allow_html=True)
        st.caption("생성된 학습 계획표를 CSV 파일로 저장하면 엑셀, 노션, 프린터로 보관하여 언제든 확인할 수 있습니다.")
        
        df_export = pd.DataFrame(export_rows)
        csv_bytes = df_export.to_csv(index=False).encode('utf-8-sig') # 한글 깨짐 방지
        
        st.download_button(
            label="📥 스터디 플래너 CSV 파일 다운로드",
            data=csv_bytes,
            file_name=f"Study_AI_시험플랜_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
