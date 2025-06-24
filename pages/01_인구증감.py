import streamlit as st
import pandas as pd
import altair as alt
import re

# Streamlit 페이지의 기본 설정을 지정합니다.
st.set_page_config(
    page_title="행정구역별 연령대 인구 분석",
    layout="wide"
)

@st.cache_data
def load_and_process_data(file_path):
    """
    EUC-KR로 인코딩된 CSV 파일을 로드하고 전처리하는 함수입니다.
    - 열 이름을 분석하기 쉽게 정리합니다. (예: '2025년05월_계_10~19세' -> 10)
    - 숫자 데이터에 포함된 쉼표(,)를 제거하고 정수형으로 변환합니다.
    """
    try:
        # EUC-KR 인코딩과 천 단위 쉼표를 인식하여 데이터 로드
        df = pd.read_csv(file_path, encoding='EUC-KR', thousands=',')
    except FileNotFoundError:
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다. 스크립트와 동일한 폴더에 파일이 있는지 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"파일을 로드하는 중 오류가 발생했습니다: {e}")
        st.info("파일 인코딩이 EUC-KR이 맞는지 확인해주세요.")
        return None

    # 원본 데이터프레임을 복사하여 전처리 진행
    df_processed = df.copy()

    # '총인구수' 열 이름 정리
    try:
        # '총인구수' 문자열을 포함하는 첫 번째 열을 찾아 '총인구수'로 이름을 변경
        total_pop_col = [col for col in df_processed.columns if '총인구수' in col][0]
        df_processed = df_processed.rename(columns={total_pop_col: '총인구수'})
    except IndexError:
        st.error("'총인구수'를 포함하는 열을 찾을 수 없습니다. CSV 파일의 열 이름을 확인해주세요.")
        return None

    # 연령 관련 열 이름에서 숫자만 추출하여 변경
    rename_dict = {}
    age_pattern = re.compile(r'(\d+)(~|\s*세)')  # '10~19세', '20세' 등에서 시작 숫자만 추출

    for col in df_processed.columns:
        if '계_' in col and '세' in col and '총인구수' not in col and '세대수' not in col:
            match = age_pattern.search(col)
            if match:
                age_start = int(match.group(1))
                rename_dict[col] = age_start

    df_processed = df_processed.rename(columns=rename_dict)

    # '행정구역' 열이 있는지 확인
    if '행정구역' not in df_processed.columns:
        st.error("'행정구역' 열을 찾을 수 없습니다. CSV 파일의 첫 번째 열이 행정구역 정보인지 확인해주세요.")
        return None

    # 분석에 필요한 열(행정구역, 총인구수, 연령별 인구수)만 선택
    age_cols = [col for col in df_processed.columns if isinstance(col, int)]
    required_cols = ['행정구역', '총인구수'] + age_cols
    df_final = df_processed[required_cols]

    # 숫자형 데이터 열들을 정수형으로 변환 (오류 발생 시 0으로 처리)
    for col in ['총인구수'] + age_cols:
        df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0).astype(int)

    return df_final

def main():
    """
    Streamlit 앱의 메인 로직을 실행하는 함수입니다.
    """
    st.title("📈 행정구역별 연령대 인구 분포 분석")
    st.write("주민등록인구 현황 데이터를 기반으로, 총인구수 상위 5개 행정구역의 연령대별 인구 분포를 시각화합니다.")

    # 사용자가 업로드한 파일 경로
    file_path = '202505_202505_주민등록인구기타현황(인구증감)_월간.csv'

    # 데이터 로드 및 전처리 실행
    data = load_and_process_data(file_path)

    if data is not None:
        # '총인구수' 기준으로 상위 5개 행정구역 데이터 추출
        df_top5 = data.nlargest(5, '총인구수').copy()
        
        # 시각화를 위해 데이터를 'long' 형태로 변환 (Melt)
        # wide format -> long format (열에 있던 연령 구분을 행으로 변환)
        age_cols = [col for col in df_top5.columns if isinstance(col, int)]
        df_melted = df_top5.melt(
            id_vars=['행정구역', '총인구수'],
            value_vars=age_cols,
            var_name='연령',
            value_name='인구수'
        )

        st.header("📊 연령대별 인구 분포 (상위 5개 행정구역)")

        # Altair 라이브러리를 사용해 라인 차트 생성
        chart = alt.Chart(df_melted).mark_line(point=True).encode(
            x=alt.X('인구수:Q', title='인구수', axis=alt.Axis(format='~s')), # Q: Quantitative
            y=alt.Y('연령:O', title='연령 (세)', sort='ascending'), # O: Ordinal
            color=alt.Color('행정구역:N', title='행정구역'), # N: Nominal
            tooltip=[
                alt.Tooltip('행정구역', title='행정구역'),
                alt.Tooltip('연령', title='연령'),
                alt.Tooltip('인구수', title='인구수', format=',')
            ]
        ).interactive()

        # 생성된 차트를 Streamlit에 표시
        st.altair_chart(chart, use_container_width=True)
        st.info("💡 그래프의 범례(오른쪽 행정구역 이름)를 클릭하여 특정 지역을 숨기거나 다시 볼 수 있습니다.")

        st.header("📄 원본 데이터 (상위 5개 행정구역)")
        # 데이터프레임의 숫자 서식을 쉼표로 지정하여 표시
        st.dataframe(df_top5.style.format('{:,}'))

    else:
        st.warning("데이터를 처리할 수 없습니다. 파일이 올바른지 다시 확인해주세요.")

if __name__ == "__main__":
    main()
