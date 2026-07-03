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
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #E3ECE8;
        color: #8A8F94;
        font-size: 0.78rem;
        line-height: 1.55;
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
    if ctx["clinic_logo_uri"]:
        clinic_logo_html = f'<img src="{ctx["clinic_logo_uri"]}" alt="clinic" style="max-height:26pt; max-width:150pt;" />'
    else:
        clinic_logo_html = f'<div class="clinic-name">{ctx["clinic_name"]}</div>'

    font_face = ""
    font_family = "sans-serif"
    if ctx["font_uri"]:
        font_face = f"""
        @font-face {{
            font-family: 'NanumGothic';
            src: url('{ctx["font_uri"]}') format('truetype');
            font-weight: normal;
        }}"""
        if ctx.get("font_bold_uri"):
            font_face += f"""
        @font-face {{
            font-family: 'NanumGothic';
            src: url('{ctx["font_bold_uri"]}') format('truetype');
            font-weight: bold;
        }}"""
        font_family = "'NanumGothic', sans-serif"

    if ctx["straumann_logo_uri"]:
        straumann_html = f'<img src="{ctx["straumann_logo_uri"]}" alt="Straumann" />'
    else:
        straumann_html = '<div style="font-size:16pt; font-weight:700; color:#3C3C3B;">straumann</div>'

    if ctx["implant_uri"]:
        product_panel = f'<div class="product-panel"><img src="{ctx["implant_uri"]}" alt="implant" /></div>'
    else:
        product_panel = ''

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
.headline {{ font-size: 22pt; font-weight: 700; line-height: 1.25; letter-spacing: -0.02em; color: #36393A; }}
.headline small {{ display: block; font-size: 12.5pt; font-weight: 400; color: #5F5E5A; margin-top: 6pt; }}
.product-panel {{ width: 78mm; background: transparent; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.product-panel img {{ width: 100%; height: auto; display: block; }}

.summary-grid {{ margin-top: 16pt; display: grid; grid-template-columns: 1fr 1fr; gap: 12pt; }}
.summary-box {{ background: #F5FBF8; border: 1px solid #D6ECE3; border-radius: 12pt; padding: 14pt 16pt; }}
.summary-cap {{ font-size: 7.5pt; color: #2D7662; letter-spacing: 0.12em; margin-bottom: 5pt; }}
.summary-main {{ font-size: 23pt; font-weight: 800; color: #169B74; letter-spacing: -0.03em; line-height: 1.12; }}
.summary-sub {{ font-size: 7.5pt; color: #5F5E5A; margin-top: 4pt; line-height: 1.5; }}

.item-table {{ margin-top: 16pt; }}
.item-header {{ display: grid; grid-template-columns: 1fr 90pt 110pt; gap: 14pt; font-size: 7pt; color: #595850; letter-spacing: 0.12em; padding-bottom: 5pt; border-bottom: 0.6px solid #9A988E; }}
.item-header > div:nth-child(2), .item-header > div:nth-child(3) {{ text-align: right; }}
.item-row {{ display: grid; grid-template-columns: 1fr 90pt 110pt; gap: 14pt; font-size: 9.5pt; padding: 8pt 0; border-bottom: 0.5px solid #E5E4DF; }}
.item-row > div:nth-child(1) {{ font-weight: 700; }}
.item-row > div:nth-child(2) {{ color: #5F5E5A; text-align: right; }}
.item-row > div:nth-child(3) {{ text-align: right; font-weight: 700; }}

.daily-box {{ margin-top: 18pt; background: #F8F9FA; border-left: 7pt solid #46B98C; border-radius: 0 12pt 12pt 0; padding: 20pt 22pt 18pt 20pt; }}
.daily-title {{ font-size: 12pt; color: #555; text-align: center; }}
.daily-value {{ margin-top: 8pt; font-size: 38pt; font-weight: 800; color: #46B98C; text-align: center; line-height: 1; }}
.daily-note {{ margin-top: 12pt; font-size: 7.4pt; color: #70757A; line-height: 1.65; text-align: left; }}

.footer {{ margin-top: auto; padding-top: 10pt; border-top: 0.6px solid #9A988E; display: flex; justify-content: space-between; align-items: flex-end; gap: 14pt; }}
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
        <div class="headline">임플란트 치료<br>예상 치료비 안내서</div>
      </div>
    </div>
    {product_panel}
  </div>

  <div class="summary-grid">
    <div class="summary-box">
      <div class="summary-cap">예상 치료비 / ESTIMATED COST</div>
      <div class="summary-main">{ctx["consult_price"]:,}원</div>
      <div class="summary-sub">임플란트 총비용: {ctx["total_price"]:,}원</div>
    </div>
    <div class="summary-box">
      <div class="summary-cap">예상 사용기간 기준 / 하루 평균</div>
      <div class="summary-main">{ctx["daily_cost"]:,}원</div>
      <div class="summary-sub">예상 사용기간 {ctx["years"]}년 기준 단순 환산 금액</div>
    </div>
  </div>

  <div class="item-table">
    <div class="item-header"><div>ITEM</div><div>BRAND</div><div>AMOUNT</div></div>
    <div class="item-row"><div>임플란트 식립</div><div>Straumann</div><div>{ctx["consult_price"]:,}원</div></div>
  </div>

  <div class="daily-box">
    <div class="daily-title">예상 사용기간 기준 하루 평균 환산 금액</div>
    <div class="daily-value">{ctx["daily_cost"]:,}원</div>
    <div class="daily-note">
      입력한 금액과 예상 사용기간을 기준으로 단순 환산한 참고 금액입니다.<br>
      실제 사용기간, 치료 결과 및 유지 상태는 환자의 구강 상태, 시술 조건 및 사후 관리에 따라 달라질 수 있습니다.
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
            <div class="sidebar-evidence-disclaimer">*해당 수치는 특정 연구 대상, 조건 및 기간에서 보고된 결과이며, 모든 환자에게 동일하게 적용되지 않습니다.</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="sidebar-evidence-card">
            <div class="sidebar-evidence-label">Domestic long-term data</div>
            <div class="sidebar-evidence-value">98.23%</div>
            <div class="sidebar-evidence-title">국내 장기 추적 연구에서 보고된<br>10년 누적 생존율</div>
            <div class="sidebar-evidence-body">국내 장기 추적 연구에서, Straumann tissue-level 임플란트의 10년 누적 생존율은 임플란트 기준 98.23%로 보고되었습니다.*</div>
            <div class="sidebar-mini-link">{tooltip_link('연구 조건 보기', tooltip_2)}</div>
            <div class="sidebar-evidence-disclaimer">*해당 수치는 특정 연구 대상, 조건 및 기간에서 보고된 결과이며, 모든 환자에게 동일하게 적용되지 않습니다.</div>
        </div>
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
            표시된 금액은 입력값을 기준으로 단순 환산한 예시이며, 실제 치료비, 치료 결과 및 사용기간은 환자의 상태, 치료계획, 시술 조건 및 사후 관리에 따라 달라질 수 있습니다.<br>
            본 자료는 외부 배포, SNS, 블로그, 광고물 등에 사용할 수 없습니다.<br>
            환자의 식별 정보는 저장되지 않으며, 상담 종료 시 삭제됩니다.
        </div>
    """, unsafe_allow_html=True)

with tab2:
    st.subheader("오래 쓰는 선택, 스트라우만")
    detail_images = [
        os.path.join(APP_DIR, "#상세페이지 1.png"),
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
