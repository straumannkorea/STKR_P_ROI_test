import streamlit as st
import os
import base64
from datetime import datetime, time, timedelta
from weasyprint import HTML

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================================
# 공통 CSS
# ==========================================================
st.set_page_config(page_title="스트라우만 가치 계산기", layout="centered")

st.markdown("""
<style>
    .active-tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        font-weight: 700;
        color: #169B74;
        border-bottom: 1px dashed #169B74;
        text-decoration: none;
    }
    .active-tooltip .tooltip-content {
        visibility: hidden;
        width: 320px;
        background-color: #36393A;
        color: #fff;
        text-align: left;
        border-radius: 10px;
        padding: 12px 14px;
        position: absolute;
        z-index: 999;
        bottom: 135%;
        left: 0;
        opacity: 0;
        transition: all 0.2s ease;
        font-size: 0.82rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        line-height: 1.55;
        pointer-events: none;
    }
    .active-tooltip:hover .tooltip-content {
        visibility: visible;
        opacity: 1;
    }
    .sidebar-evidence-card {
        background: #F5FBF8;
        border: 1px solid #D6ECE3;
        border-radius: 18px;
        padding: 18px 18px 16px 18px;
        margin: 14px 0;
    }
    .sidebar-evidence-label {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        color: #169B74;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .sidebar-evidence-value {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1;
        color: #169B74;
        margin-bottom: 10px;
    }
    .sidebar-evidence-title {
        font-size: 1rem;
        font-weight: 800;
        color: #2D3134;
        line-height: 1.45;
        margin-bottom: 8px;
    }
    .sidebar-evidence-body {
        font-size: 0.95rem;
        color: #485057;
        line-height: 1.65;
        margin-bottom: 10px;
    }
    .sidebar-evidence-disclaimer {
        color: #8A8F94;
        font-size: 0.76rem;
        line-height: 1.55;
        margin: -2px 4px 16px 4px;
        padding: 0 2px;
    }
    .sidebar-mini-link {
        font-size: 0.9rem;
        font-weight: 700;
        color: #169B74;
    }
    .footer-disclaimer {
        color: #8A8F94;
        font-size: 0.78rem;
        text-align: center;
        margin-top: 42px;
        border-top: 1px solid #eee;
        padding-top: 18px;
        line-height: 1.7;
    }
</style>
""", unsafe_allow_html=True)


def tooltip_link(label: str, content: str) -> str:
    return f'''
    <span class="active-tooltip">{label}
        <span class="tooltip-content">{content}</span>
    </span>
    '''


# ==========================================================
# 헬퍼: 파일을 base64 data URI로 변환 (PDF용)
# ==========================================================
def to_data_uri(path: str, mime: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def bytes_to_data_uri(raw: bytes, mime: str) -> str:
    b64 = base64.b64encode(raw).decode()
    return f"data:{mime};base64,{b64}"


# ==========================================================
# 견적 PDF HTML 템플릿 생성 함수
# ==========================================================
def build_estimate_html(ctx: dict) -> str:
    """
    ctx 안에 들어가는 값:
      clinic_name, contact_info, patient_name, issue_date, expiry_date,
      consult_price, total_price, daily_cost, years,
      clinic_logo_uri (str | ""), straumann_logo_uri, implant_uri, qr_uri, font_uri
    """
    # 치과 로고: 업로드된 게 있으면 이미지, 없으면 치과명 텍스트
    if ctx["clinic_logo_uri"]:
        clinic_logo_html = f'<img src="{ctx["clinic_logo_uri"]}" alt="clinic" style="max-height:26pt; max-width:150pt;" />'
    else:
        clinic_logo_html = f'<div class="clinic-name">{ctx["clinic_name"]}</div>'

    # 폰트 @font-face (레포의 NanumGothic.ttf 임베드)
    # normal + bold 두 굵기를 등록해야 font-weight:700이 진짜 굵은 폰트로 렌더됨
    font_face = ""
    font_family = "sans-serif"
    if ctx["font_uri"]:
        font_face = f"""
        @font-face {{
            font-family: 'NanumGothic';
            src: url('{ctx["font_uri"]}') format('truetype');
            font-weight: normal;
        }}"""
        # Bold 폰트가 있으면 추가 등록
        if ctx.get("font_bold_uri"):
            font_face += f"""
        @font-face {{
            font-family: 'NanumGothic';
            src: url('{ctx["font_bold_uri"]}') format('truetype');
            font-weight: bold;
        }}"""
        font_family = "'NanumGothic', sans-serif"

    # 스트라우만 로고 (없으면 텍스트 폴백)
    if ctx["straumann_logo_uri"]:
        straumann_html = f'<img src="{ctx["straumann_logo_uri"]}" alt="Straumann" />'
    else:
        straumann_html = '<div style="font-size:16pt; font-weight:700; color:#3C3C3B;">straumann</div>'

    # 임플란트 제품 패널 (없으면 패널 숨김)
    if ctx["implant_uri"]:
        product_panel = f'<div class="product-panel"><img src="{ctx["implant_uri"]}" alt="implant" /></div>'
    else:
        product_panel = ''

    # QR (없으면 숨김)
    if ctx["qr_uri"]:
        qr_html = f'''<div class="qr-block">
              <img src="{ctx["qr_uri"]}" alt="QR" />
              <div class="qr-label">스트라우만<br>공식영상</div>
            </div>'''
    else:
        qr_html = ''

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
{font_face}
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ font-family: {font_family}; color: #2C2C2A; margin: 0; padding: 0; }}

.page {{ width: 210mm; height: 297mm; padding: 16mm 14mm; display: flex; flex-direction: column; }}

.header {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid #2C2C2A; padding-bottom: 10pt; }}
.label-cap {{ font-size: 7pt; letter-spacing: 0.15em; color: #595850; margin-bottom: 4pt; }}
.clinic-name {{ font-size: 18pt; font-weight: 700; letter-spacing: -0.02em; white-space: nowrap; }}
.header-right {{ text-align: right; }}
.header-right img {{ height: 20pt; display: block; margin-left: auto; }}

.title-row {{ margin-top: 14pt; display: flex; justify-content: space-between; align-items: stretch; gap: 18pt; }}
.title-left {{ flex: 1; display: flex; flex-direction: column; justify-content: space-between; }}
.estimate-label {{ font-size: 7pt; letter-spacing: 0.2em; color: #1D9E75; margin-bottom: 6pt; }}
.patient-info {{ font-size: 9pt; color: #5F5E5A; line-height: 1.6; }}
.headline-wrap {{ margin-top: 14pt; }}
.headline-eyebrow {{ font-size: 8.5pt; color: #1D9E75; letter-spacing: 0.1em; margin-bottom: 6pt; }}
.headline {{ font-size: 22pt; font-weight: 400; line-height: 1.2; letter-spacing: -0.02em; color: #36393A; }}
.headline strong {{ font-weight: 800; color: #2D7662; }}

.product-panel {{ width: 78mm; background: transparent; border-radius: 4pt; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.product-panel img {{ width: 100%; height: auto; display: block; }}

.price-box {{ margin-top: 14pt; background: #E1F5EE; padding: 13pt 16pt; border-radius: 3pt; display: flex; justify-content: space-between; align-items: flex-end; }}
.price-box-note {{ margin-top: 3pt; font-size: 6pt; color: #5F5E5A; line-height: 1.3; padding-left: 2pt; }}
.price-cap {{ font-size: 7.5pt; color: #2D7662; letter-spacing: 0.12em; margin-bottom: 4pt; }}
.price-main {{ font-size: 19pt; font-weight: 800; color: #2D7662; letter-spacing: -0.02em; line-height: 1.1; }}
.price-unit {{ font-size: 10pt; margin-left: 3pt; }}
.price-sub {{ font-size: 7pt; color: #2D7662; margin-top: 4pt; opacity: 0.75; }}

.item-table {{ margin-top: 14pt; }}
.item-header {{ display: grid; grid-template-columns: 1fr 90pt 110pt; gap: 14pt; font-size: 7pt; color: #595850; letter-spacing: 0.12em; padding-bottom: 5pt; border-bottom: 0.6px solid #9A988E; }}
.item-header > div:nth-child(2) {{ text-align: right; }}
.item-header > div:nth-child(3) {{ text-align: right; }}
.item-row {{ display: grid; grid-template-columns: 1fr 90pt 110pt; gap: 14pt; font-size: 9.5pt; padding: 7pt 0; border-bottom: 0.5px solid #E5E4DF; }}
.item-row > div:nth-child(1) {{ font-weight: 700; }}
.item-row > div:nth-child(2) {{ color: #5F5E5A; text-align: right; }}
.item-row > div:nth-child(3) {{ text-align: right; font-weight: 700; }}

.brand-section {{ margin-top: auto; padding-top: 14pt; border-top: 1px solid #2C2C2A; }}
.brand-grid {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 18pt; }}
.brand-label {{ font-size: 7.5pt; color: #1D9E75; letter-spacing: 0.12em; margin-bottom: 6pt; }}
.brand-copy {{ font-size: 8.5pt; line-height: 1.7; color: #444441; }}
.stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5pt; }}
.stat-card {{ border: 0.6px solid #9A988E; padding: 7pt 8pt; border-radius: 2pt; }}
.stat-value {{ font-size: 13pt; font-weight: 700; color: #2D7662; line-height: 1.1; }}
.stat-unit {{ font-size: 7.5pt; color: #595850; margin-left: 2pt; font-weight: 400; }}
.stat-sup {{ font-size: 6pt; color: #595850; margin-left: 1pt; vertical-align: super; }}
.stat-label {{ font-size: 7.5pt; color: #5F5E5A; margin-top: 2pt; }}

.citations {{ margin-top: 10pt; padding-top: 8pt; border-top: 0.5px solid #E5E4DF; font-size: 6.5pt; color: #4A4945; line-height: 1.55; }}
.citations sup {{ margin-right: 2pt; font-size: 5pt; }}
.citations > div + div {{ margin-top: 2pt; }}

.footer {{ margin-top: 10pt; padding-top: 10pt; border-top: 0.6px solid #9A988E; display: flex; justify-content: space-between; align-items: center; gap: 14pt; }}
.notice {{ font-size: 6.8pt; color: #4A4945; line-height: 1.7; flex: 1; }}
.notice > div + div {{ margin-top: 2pt; }}
.qr-block {{ display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; }}
.qr-block img {{ width: 36pt; height: 36pt; display: block; }}
.qr-label {{ font-size: 6pt; color: #595850; margin-top: 4pt; letter-spacing: 0.05em; text-align: center; line-height: 1.4; }}
</style>
</head>
<body>
<div class="page">

  <div class="header">
    <div>
      <div class="label-cap">DENTAL CLINIC</div>
      {clinic_logo_html}
    </div>
    <div class="header-right">
      <div class="label-cap">PARTNER BRAND</div>
      {straumann_html}
    </div>
  </div>

  <div class="title-row">
    <div class="title-left">
      <div>
        <div class="estimate-label">ESTIMATE / 견적안내서</div>
        <div class="patient-info">
          발행일: {ctx["issue_date"]} &nbsp;·&nbsp; 유효기간: {ctx["expiry_date"]}<br>
          {ctx["patient_name"]} 귀하
        </div>
      </div>
      <div class="headline-wrap">
        <div class="headline-eyebrow">ESTIMATE</div>
        <div class="headline">임플란트 치료<br><strong>예상 치료비 안내서</strong></div>
      </div>
    </div>
    {product_panel}
  </div>

  <div class="price-box">
    <div>
      <div class="price-cap">예상 치료비 / ESTIMATED COST</div>
      <div class="price-main">{ctx["consult_price"]:,}<span class="price-unit">원</span></div>
      <div class="price-sub">임플란트 총비용: {ctx["total_price"]:,}원</div>
    </div>
    <div style="text-align: right;">
      <div class="price-cap">하루 평균 / {ctx["years"]}년 기준</div>
      <div class="price-main">{ctx["daily_cost"]:,}<span class="price-unit">원/일</span></div>
    </div>
  </div>
  <div class="price-box-note">
    *환자의 상태에 따라 달라질 수 있으며, 입력된 수치를 기반으로 단순 계산된 예시입니다.
  </div>
  <div class="item-table">
    <div class="item-header"><div>ITEM</div><div>BRAND</div><div>AMOUNT</div></div>
    <div class="item-row"><div>임플란트 식립</div><div>Straumann</div><div>{ctx["consult_price"]:,}원</div></div>
  </div>

  <div class="brand-section">
    <div class="brand-grid">
      <div>
        <div class="brand-label">WHY STRAUMANN</div>
        <div class="brand-copy">스트라우만은 70년 이상 임플란트 분야의 연구와 임상 경험을 통해 전 세계 100여 개국에서 신뢰받는 세계 임플란트 시장 점유율 1위 브랜드입니다.<sup>2</sup></div>
      </div>
      <div class="stat-grid">
        <div class="stat-card"><div class="stat-value">70<span class="stat-unit">YEARS</span></div><div class="stat-label">스위스 헤리티지</div></div>
        <div class="stat-card"><div class="stat-value">99.7<span class="stat-unit">%</span><span class="stat-sup">1</span></div><div class="stat-label">10년 implant-level<br>survival rate (보고치)</div></div>
        <div class="stat-card"><div class="stat-value">#1<span class="stat-unit">GLOBAL</span><span class="stat-sup">2</span></div><div class="stat-label">세계 시장 점유율</div></div>
        <div class="stat-card"><div class="stat-value">100<span class="stat-unit">+</span></div><div class="stat-label">국가 사용</div></div>
      </div>
    </div>
    <div class="citations">
      <div><sup>1</sup>van Velzen FJ, et al. J Clin Periodontol. 2015; 374 implants, 177 patients, 10-year follow-up</div>
      <div><sup>2</sup>Fortune Business Insights, Dental Implants – Global Market Analysis, Insights and Forecast, 2021–2028 (2021년 기준)</div>
    </div>
  </div>

  <div class="footer">
    <div class="notice">
      <div>※ 표시된 금액은 입력값을 기준으로 단순 환산한 예시이며, 실제 치료비, 치료 결과 및 사용기간은 환자의 상태, 치료계획, 시술 조건 및 사후 관리에 따라 달라질 수 있습니다.</div>
      <div>※ 본 자료는 외부 배포, SNS, 블로그, 광고물 등에 사용할 수 없습니다.</div>
      <div>※ 환자의 식별 정보는 저장되지 않으며, 상담 종료 시 삭제됩니다.</div>
      <div style="margin-top:4pt;">문의: {ctx["contact_info"]}</div>
    </div>
    {qr_html}
  </div>

</div>
</body>
</html>"""


# ==========================================================
# 사이드바: 핵심 근거 + PDF 생성
# ==========================================================
with st.sidebar:
    st.header("🏆 스트라우만 핵심 근거")

    tooltip_1 = (
        "van Velzen FJ, et al. J Clin Periodontol. 2015. "
        "177명 환자, 374개 Straumann SLA surface implant 대상 10년 전향적 코호트 연구입니다. "
        "10년 생존율은 implant-level 99.7%, patient-level 99.4%로 보고되었습니다."
    )
    tooltip_2 = (
        "Kim S, Jung U-W, Cho K-S, Lee J-S. Clin Implant Dent Relat Res. 2018. "
        "881명 환자, 1,692개 Straumann tissue-level 임플란트를 분석한 국내 장기 추적 연구입니다. "
        "10년 누적 생존율은 implant-level 98.23%, patient-level 95.70%로 보고되었습니다."
    )

    st.markdown(f"""
        <div class="sidebar-evidence-card">
            <div class="sidebar-evidence-label">10-year follow-up</div>
            <div class="sidebar-evidence-value">99.7%</div>
            <div class="sidebar-evidence-title">10년 추적 연구에서 보고된<br>10년 생존율</div>
            <div class="sidebar-evidence-body">10년 추적 연구에서 Straumann SLA 표면 임플란트는 특정 연구 조건하에 10년 생존율 99.7%가 보고되었습니다.*</div>
            <div class="sidebar-mini-link">{tooltip_link('연구 조건 보기', tooltip_1)}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="sidebar-evidence-card">
            <div class="sidebar-evidence-label">Domestic long-term data</div>
            <div class="sidebar-evidence-value">98.23%</div>
            <div class="sidebar-evidence-title">국내 장기 추적 연구에서 보고된<br>10년 누적 생존율</div>
            <div class="sidebar-evidence-body">국내 장기 추적 연구에서, Straumann tissue-level 임플란트의 10년 누적 생존율은 임플란트 기준 98.23%로 보고되었습니다.*</div>
            <div class="sidebar-mini-link">{tooltip_link('연구 조건 보기', tooltip_2)}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="sidebar-evidence-disclaimer">*해당 수치는 특정 연구 대상, 조건 및 기간에서 보고된 결과이며, 모든 환자에게 동일하게 적용되지 않습니다.</div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📄 안내서 정보 입력")
    clinic_name = st.text_input("치과명", value="")
    contact_info = st.text_input("연락처", value="")
    patient_name = st.text_input("환자명", value="")

    clinic_logo_file = st.file_uploader(
        "치과 로고 (선택사항 · PNG/JPG)",
        type=["png", "jpg", "jpeg"],
        help="로고를 올리면 안내서 상단에 들어갑니다. 올리지 않으면 치과명이 텍스트로 표시됩니다."
    )

    col_d, col_t = st.columns(2)
    with col_d:
        validity_date = st.date_input("견적 유효기간", datetime.now() + timedelta(days=30))
    with col_t:
        surgery_time = st.time_input("상담 시간", value=time(14, 0))

    full_validity_dt = f"{validity_date.strftime('%Y-%m-%d')} 까지 유효"

    st.divider()
    generate_pdf = st.button("📥 PDF 안내서 생성", use_container_width=True)


# ==========================================================
# 메인 화면
# ==========================================================
st.title("👨‍⚕️ 스트라우만 가치 계산기")
tab1, tab2 = st.tabs(["💰 장기 가치 분석 (ROI)", "🌟 오래쓰는 스트라우만"])

with tab1:
    st.subheader("실질 투자 가치 확인")
    c1, c2 = st.columns(2)
    with c1:
        total_p = st.number_input("임플란트 총 비용 (원)", value=1500000, step=10000)
        discount = st.number_input("조정 금액 (원)", value=0, min_value=0, max_value=int(total_p), step=10000)
        final_p = max(total_p - discount, 0)
        st.markdown(f"**예상 치료비 : {final_p:,.0f}원**")
        st.caption(f"(임플란트 총비용 : {total_p:,.0f}원)")
    with c2:
        years = st.slider("예상 사용 기간 (년)", 5, 50, 20)
        st.markdown(f"**견적 유효기간:** {full_validity_dt}")
        st.markdown("""
            <div style="color: #A9A9A9; font-size: 0.85rem; margin-top: 10px; line-height: 1.4;">
                * 환자분의 건강상태 / 관리 여하에 따라 상이할 수 있습니다. <br>
                * 해당 계산결과는 이해를 돕기위한 단순환산 예시입니다.
            </div>
        """, unsafe_allow_html=True)

    daily_roi = final_p / (years * 365)
    st.markdown(f"""
        <div style='background-color:#f8f9fa; padding:40px; border-radius:15px; border-left: 10px solid #46B98C; text-align:center; margin-top: 20px;'>
            <p style='font-size:1.2rem; color:#555; margin:0 0 12px 0;'>예상 사용기간 기준 하루 평균 환산 금액</p>
            <h2 style='margin:0; color:#46B98C; font-size:4.5rem;'>{int(daily_roi):,}원</h2>
            <div style='max-width:680px; margin:16px auto 0; text-align:left; font-size:0.82rem; color:#7A7A7A; line-height:1.7;'>
                입력한 금액과 예상 사용기간을 기준으로 단순 환산한 참고 금액입니다.<br>
                실제 사용기간, 치료 결과 및 유지 상태는 환자의 구강 상태, 시술 조건 및 사후 관리에 따라 달라질 수 있습니다.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="footer-disclaimer">
            본 자료는 외부 배포, SNS, 블로그, 광고물 등에 사용할 수 없습니다.<br>
            환자의 식별 정보는 저장되지 않으며, 상담 종료 시 삭제됩니다.
        </div>
    """, unsafe_allow_html=True)

with tab2:
    st.subheader("오래 쓰는 선택, 스트라우만")
    detail_images = [
        os.path.join(APP_DIR, "상세페이지 1.png"),
        os.path.join(APP_DIR, "#상세페이지 2.png"),
        os.path.join(APP_DIR, "#상세페이지 3.png"),
    ]
    for img in detail_images:
        if os.path.exists(img):
            st.image(img, use_container_width=True)
        else:
            st.warning(f"이미지 파일 '{os.path.basename(img)}'이 폴더에 없습니다. 확인해 주세요.")


# ==========================================================
# PDF 생성 로직
# ==========================================================
if generate_pdf:
    if not patient_name or not clinic_name:
        st.sidebar.warning("치과명과 환자명을 입력해주세요.")
    else:
        try:
            clinic_logo_uri = ""
            if clinic_logo_file is not None:
                raw = clinic_logo_file.getvalue()
                mime = "image/png" if clinic_logo_file.type in ("image/png",) else "image/jpeg"
                clinic_logo_uri = bytes_to_data_uri(raw, mime)

            ctx = {
                "clinic_name": clinic_name,
                "contact_info": contact_info if contact_info else "-",
                "patient_name": patient_name,
                "issue_date": datetime.now().strftime("%Y-%m-%d"),
                "expiry_date": full_validity_dt,
                "consult_price": int(final_p),
                "total_price": int(total_p),
                "daily_cost": int(daily_roi),
                "years": years,
                "clinic_logo_uri": clinic_logo_uri,
                "straumann_logo_uri": to_data_uri(os.path.join(APP_DIR, "straumann_logo.png"), "image/png"),
                "implant_uri": to_data_uri(os.path.join(APP_DIR, "implant_new.png"), "image/png"),
                "qr_uri": to_data_uri(os.path.join(APP_DIR, "qrcode.png"), "image/png"),
                "font_uri": to_data_uri(os.path.join(APP_DIR, "NanumGothic.ttf"), "font/ttf"),
                "font_bold_uri": to_data_uri(os.path.join(APP_DIR, "NanumGothicBold.ttf"), "font/ttf"),
            }

            html_str = build_estimate_html(ctx)
            pdf_bytes = HTML(string=html_str).write_pdf()

            st.sidebar.success("✅ 안내서가 생성되었습니다!")
            st.sidebar.download_button(
                label="📄 PDF 안내서 다운로드",
                data=pdf_bytes,
                file_name=f"{clinic_name}_Estimate_{patient_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF 생성 중 오류가 발생했습니다: {e}")
