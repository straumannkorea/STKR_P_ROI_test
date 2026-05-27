import streamlit as st
import os
import base64
from datetime import datetime, time, timedelta
from weasyprint import HTML

# ==========================================================
# CSS 주입: 액티브 툴팁 및 보안 문구 스타일링
# ==========================================================
st.markdown("""
<style>
    .active-tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        font-weight: bold;
        border-bottom: 2px dashed #46B98C;
    }
    .active-tooltip a {
        text-decoration: none;
        color: #46B98C !important;
    }
    .active-tooltip .tooltip-content {
        visibility: hidden;
        width: 300px;
        background-color: #36393A;
        color: #fff;
        text-align: center;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 999;
        bottom: 150%;
        left: 50%;
        transform: translateX(-50%) translateY(10px);
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        font-size: 0.85rem;
        box-shadow: 0px 10px 15px rgba(0,0,0,0.2);
        line-height: 1.4;
        pointer-events: none;
    }
    .active-tooltip:hover .tooltip-content {
        visibility: visible;
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }
    .footer-disclaimer {
        color: #A9A9A9;
        font-size: 0.8rem;
        text-align: center;
        margin-top: 50px;
        border-top: 1px solid #eee;
        padding-top: 20px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================================
# 헬퍼: 파일을 base64 data URI로 변환 (PDF에 이미지/폰트 임베드용)
# ==========================================================
def to_data_uri(path: str, mime: str) -> str:
    """파일이 있으면 data URI 문자열을, 없으면 빈 문자열을 반환."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def bytes_to_data_uri(raw: bytes, mime: str) -> str:
    """업로드된 바이트를 data URI로 변환."""
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
.headline strong {{ font-weight: 800; color: #46B98C; }}

.product-panel {{ width: 78mm; background: transparent; border-radius: 4pt; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.product-panel img {{ width: 100%; height: auto; display: block; }}

.price-box {{ margin-top: 14pt; background: #E1F5EE; padding: 13pt 16pt; border-radius: 3pt; display: flex; justify-content: space-between; align-items: flex-end; }}
.price-cap {{ font-size: 7.5pt; color: #0F6E56; letter-spacing: 0.12em; margin-bottom: 4pt; }}
.price-main {{ font-size: 19pt; font-weight: 800; color: #0F6E56; letter-spacing: -0.02em; line-height: 1.1; }}
.price-unit {{ font-size: 10pt; margin-left: 3pt; }}
.price-sub {{ font-size: 7pt; color: #0F6E56; margin-top: 4pt; opacity: 0.75; }}

.item-table {{ margin-top: 12pt; }}
.item-header {{ display: grid; grid-template-columns: 1fr auto auto; gap: 14pt; font-size: 7pt; color: #595850; letter-spacing: 0.12em; padding-bottom: 5pt; border-bottom: 0.6px solid #9A988E; }}
.item-header > div:last-child {{ text-align: right; }}
.item-row {{ display: grid; grid-template-columns: 1fr auto auto; gap: 14pt; font-size: 9.5pt; padding: 7pt 0; border-bottom: 0.5px solid #E5E4DF; }}
.item-row > div:nth-child(1) {{ font-weight: 700; }}
.item-row > div:nth-child(2) {{ color: #5F5E5A; }}
.item-row > div:nth-child(3) {{ text-align: right; font-weight: 700; }}

.brand-section {{ margin-top: auto; padding-top: 14pt; border-top: 1px solid #2C2C2A; }}
.brand-grid {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 18pt; }}
.brand-label {{ font-size: 7.5pt; color: #1D9E75; letter-spacing: 0.12em; margin-bottom: 6pt; }}
.brand-copy {{ font-size: 8.5pt; line-height: 1.7; color: #444441; }}
.stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5pt; }}
.stat-card {{ border: 0.6px solid #9A988E; padding: 7pt 8pt; border-radius: 2pt; }}
.stat-value {{ font-size: 13pt; font-weight: 700; color: #0F6E56; line-height: 1.1; }}
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
        <div class="headline-eyebrow">임플란트, 그 이상의 가치</div>
        <div class="headline"><strong>70년의 헤리티지</strong>를<br>매일 <strong>{ctx["daily_cost"]:,}원</strong>에.</div>
      </div>
    </div>
    {product_panel}
  </div>

  <div class="price-box">
    <div>
      <div class="price-cap">상담가 / CONSULTATION PRICE</div>
      <div class="price-main">{ctx["consult_price"]:,}<span class="price-unit">원</span></div>
      <div class="price-sub">원내 공식 비급여 고찰가격: {ctx["total_price"]:,}원</div>
    </div>
    <div style="text-align: right;">
      <div class="price-cap">하루 평균 / {ctx["years"]}년 기준</div>
      <div class="price-main">{ctx["daily_cost"]:,}<span class="price-unit">원/일</span></div>
    </div>
  </div>

  <div class="item-table">
    <div class="item-header"><div>ITEM</div><div>BRAND</div><div>AMOUNT</div></div>
    <div class="item-row"><div>임플란트 식립</div><div>Straumann</div><div>{ctx["consult_price"]:,}원</div></div>
  </div>

  <div class="brand-section">
    <div class="brand-grid">
      <div>
        <div class="brand-label">WHY STRAUMANN</div>
        <div class="brand-copy">스트라우만은 70년 이상 임플란트 분야의 연구와 임상 경험을 통해 전 세계 100여 개국에서 신뢰받는 1위 브랜드입니다. 10년 후 임플란트 생존율 99.7%의 임상데이터를 보유하고 있습니다.</div>
      </div>
      <div class="stat-grid">
        <div class="stat-card"><div class="stat-value">70<span class="stat-unit">YEARS</span></div><div class="stat-label">스위스 헤리티지</div></div>
        <div class="stat-card"><div class="stat-value">99.7<span class="stat-unit">%</span><span class="stat-sup">1</span></div><div class="stat-label">10년 생존율</div></div>
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
      <div>※ 본 안내서는 환자 상담용 참고자료로, 정확한 비용은 수술 계획에 따라 변경될 수 있으며 무단 전재 및 온라인 게시를 금지합니다.</div>
      <div>※ 임플란트는 관리 여하에 따라 사용기간이 상이합니다.</div>
      <div>※ 환자의 식별 정보는 저장되지 않고, 상담 종료 시 삭제됩니다.</div>
      <div style="margin-top:4pt;">문의: {ctx["contact_info"]}</div>
    </div>
    {qr_html}
  </div>

</div>
</body>
</html>"""


# ==========================================================
# 사이드바: 데이터 및 견적 정보
# ==========================================================
with st.sidebar:
    st.header("🏆 스트라우만 임상 데이터")

    st.markdown("""
        <table style="width:100%; border-collapse: collapse; font-size: 0.9rem;">
            <tr style="border-bottom: 1px solid #ddd; text-align: left;">
                <th style="padding: 8px;">브랜드</th>
                <th style="padding: 8px;">장기생존률</th>
                <th style="padding: 8px;">근거</th>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px;"><b>스트라우만</b></td>
                <td style="padding: 8px;"><b>99.7%</b></td>
                <td style="padding: 8px;">
                    <span class="active-tooltip">
                        <a href="https://pubmed.ncbi.nlm.nih.gov/25370914/" target="_blank">10년이상의 연구논문</a>
                        <span class="tooltip-content">van Velzen FJ, et al. J Clin Periodontal. 2015; 374 implants, 177 patients, 10-year follow-up</span>
                    </span>
                </td>
            </tr>
            <tr>
                <td style="padding: 8px;">임플란트 평균</td>
                <td style="padding: 8px;">약 93~96%</td>
                <td style="padding: 8px;">
                    <span class="active-tooltip">
                        <a href="https://www.sciencedirect.com/science/article/abs/pii/S0300571219300491" target="_blank">메타분석 데이터</a>
                        <span class="tooltip-content">Howe MS, Keys W, Richards D. J Dent. 2019;84:9-21.</span>
                    </span>
                </td>
            </tr>
        </table>
    """, unsafe_allow_html=True)

    st.caption("개인별 차이가 있을 수 있습니다.")

    st.markdown("""
        <div style="background-color: #36393A; color: white; padding: 15px; border-radius: 8px; margin-top: 5px;">
            <b>🎓 연세대 조규성 교수팀 10년 연구</b><br>
            <span style="font-size: 0.9em;">- 1,692건 추적 결과 98.2% 이상의 장기생존율 입증</span>
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📄 안내서 정보 입력")
    clinic_name = st.text_input("치과명", value="")
    contact_info = st.text_input("연락처", value="")
    patient_name = st.text_input("환자명", value="")

    # ▼▼▼ 새로 추가된 부분: 치과 로고 업로드 ▼▼▼
    clinic_logo_file = st.file_uploader(
        "치과 로고 (선택사항 · PNG/JPG)",
        type=["png", "jpg", "jpeg"],
        help="로고를 올리면 안내서 상단에 들어갑니다. 올리지 않으면 치과명이 텍스트로 표시됩니다."
    )
    # ▲▲▲ 여기까지 ▲▲▲

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
        discount = st.number_input("조정 금액 (원)", value=0, step=10000)
        final_p = total_p - discount
        st.markdown(f"**상담 가격 : {final_p:,.0f}원**")
        st.caption(f"(원내 공식 비급여 고찰가격 : {total_p:,.0f}원)")
    with c2:
        years = st.slider("예상 사용 기간 (년)", 5, 50, 20)
        st.markdown(f"**견적 유효기간:** {full_validity_dt}")
        st.markdown("""
            <div style="color: #A9A9A9; font-size: 0.85rem; margin-top: 10px; line-height: 1.4;">
                * 의사 판단하에 측정된 수치입니다.<br>
                * 환자분의 건강상태 / 관리 여하에 따라 상이할 수 있습니다. <br>
                * 해당 계산결과는 이해를 돕기위한 단순환산 예시입니다.
            </div>
        """, unsafe_allow_html=True)

    daily_roi = final_p / (years * 365)
    st.markdown(f"""
        <div style='background-color:#f8f9fa; padding:40px; border-radius:15px; border-left: 10px solid #46B98C; text-align:center; margin-top: 20px;'>
            <p style='font-size:1.2rem; color:#555;'>환자분의 하루 평균 투자 비용은</p>
            <h2 style='margin:0; color:#46B98C; font-size:4.5rem;'>{int(daily_roi):,}원</h2>
            <p style='font-size:1.1rem; color:#333; margin-top:10px;'>
                <b>하루 {int(daily_roi):,}원으로 {years}년 동안 건강한 미소를 유지하세요.</b>
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="footer-disclaimer">
            본 상담툴은 의료진의 상담 참고용이며, 외부(SNS, 블로그 등)으로 유출을 금지합니다.<br>
            환자의 식별 정보는 저장되지 않고, 상담 종료 시 삭제됩니다.
        </div>
    """, unsafe_allow_html=True)

with tab2:
    st.subheader("신뢰의 브랜드, 스트라우만. 그 이유는?")
    detail_images = ["상세페이지 1.png", "상세페이지 2.png", "상세페이지 3.png"]
    for img in detail_images:
        if os.path.exists(img):
            st.image(img, use_container_width=True)
        else:
            st.warning(f"이미지 파일 '{img}'이 폴더에 없습니다. 확인해 주세요.")

    st.divider()
    st.subheader("🎥 스트라우만이 알려드리는 임플란트 빠르게 이해하기!")
    st.write("스트라우만의 기술력과 전통으로, 건강하게 오래쓰는 임플란트. 진짜 나를 위한 선택.")
    st.video("https://www.youtube.com/watch?v=WHcWT5BRTCA")


# ==========================================================
# PDF 생성 로직 (weasyprint 디자인 버전)
# ==========================================================
if generate_pdf:
    if not patient_name or not clinic_name:
        st.sidebar.warning("치과명과 환자명을 입력해주세요.")
    else:
        try:
            # 업로드된 치과 로고 처리
            clinic_logo_uri = ""
            if clinic_logo_file is not None:
                raw = clinic_logo_file.getvalue()
                mime = "image/png" if clinic_logo_file.type in ("image/png",) else "image/jpeg"
                clinic_logo_uri = bytes_to_data_uri(raw, mime)

            # 컨텍스트 구성
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
                "straumann_logo_uri": to_data_uri("straumann_logo.png", "image/png"),
                "implant_uri": to_data_uri("implant_new.png", "image/png"),
                "qr_uri": to_data_uri("qrcode.png", "image/png"),
                "font_uri": to_data_uri("NanumGothic.ttf", "font/ttf"),
                "font_bold_uri": to_data_uri("NanumGothicBold.ttf", "font/ttf"),
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
