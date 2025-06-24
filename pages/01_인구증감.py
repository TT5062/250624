import streamlit as st
import pandas as pd
import altair as alt
import re

# Streamlit 페이지 설정
st.set_page_config(
    page_title="행정구역별 연령대 인구 분석",
    layout="wide"
)

@st.cache_data
def load_and_process_data(file_path):
    """
    EUC-KR로 인코딩된 CSV 파일을 로드하고 전처리합니다.
    - 열 이름 정리 (연령 숫자만 추출)
    - 데이터 타입을 정수로 변환
    - 불필요한 열 제거
    """
    try:
        # EUC-KR 인코딩으로 데이터 로드
        df = pd.read_csv(file_path, encoding='EUC-KR', thousands=',')
    except Exception as e:
        st.error(f"파일을 로드하는 중 오류가 발생했습니다: {e}")
        st.info("파일 인코딩이 EUC-KR이 맞는지 확인해주세요.")
        return None

    # 원본 데이터 복사하여 전처리 진행
    df_processed = df.copy()

    # '총인구수' 열 이름 변경
    try:
        total_pop_col = [col for col in df_processed.columns if '총인구수' in col][0]
        df_processed = df_processed.rename(columns={total_pop_col: '총인구수'})
    except IndexError:
        st.error("'총인구수'를 포함하는 열을 찾을 수 없습니다. CSV 파일의 열 이름을 확인해주세요.")
        return None

    # 연령 관련 열 이름 변경 (예: '2025년05월_계_10~19세' -> 10)
    rename_dict = {}
    age_pattern = re.compile(r'(\d+)(~|\s*세)') # 숫자만 추출하기 위한 정규표현식

    for col in df_processed.columns:
        if '계_' in col and '세' in col and '총인구수' not in col and '세대수' not in col:
            match = age_pattern.search(col)
            if match:
                age_start = int(match.group(1))
                rename_dict[col] = age_start

    df_processed = df_processed.rename(columns=rename_dict)

    # 행정구역 열 이름 확인 및 설정
    if '행정구역' not in df_processed.columns:
        st.error("'행정구역' 열을 찾을 수 없습니다. CSV 파일의 첫 번째 열이 행정구역 정보인지 확인해주세요.")
        return None

    # 필요한 열만 선택 (행정구역, 총인구수, 연령 열)
    age_cols = [col for col in df_processed.columns if isinstance(col, int)]
    required_cols = ['행정구역', '총인구수'] + age_cols
    df_final = df_processed[required_cols]

    # 숫자형 데이터 کل럼들의 타입을 정수로 변환
    for col in ['총인구수'] + age_cols:
        df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0).astype(int)

    return df_final

def main():
    """
    Streamlit 앱의 메인 함수
    """
    st.title("📈 행정구역별 연령대 인구 분포 분석")
    st.write("EUC-KR로 인코딩된 주민등록인구 현황 CSV 파일을 분석하여, 상위 5개 행정구역의 연령대별 인구 분포를 시각화합니다.")

    # 파일 경로 설정 (사용자가 업로드한 파일 이름)
    file_path = '202505_202505_주민등록인구기타현황(인구증감)_월간.csv'

    # 데이터 로드 및 전처리
    data = load_and_process_data(file_path)

    if data is not None:
        # 총인구수 기준으로 상위 5개 행정구역 추출
        df_top5 = data.nlargest(5, '총인구수').copy()
        
        # 시각화를 위해 데이터를 'long' 형태로 변환 (Melt)
        age_cols = [col for col in df_top5.columns if isinstance(col, int)]
        df_melted = df_top5.melt(
            id_vars=['행정구역', '총인구수'],
            value_vars=age_cols,
            var_name='연령',
            value_name='인구수'
        )

        st.header("📊 연령대별 인구 분포 (상위 5개 행정구역)")

        # Altair를 사용한 라인 차트 생성
        chart = alt.Chart(df_melted).mark_line(point=True).encode(
            x=alt.X('인구수:Q', title='인구수', axis=alt.Axis(format='~s')),
            y=alt.Y('연령:O', title='연령 (세)', sort='ascending'),
            color=alt.Color('행정구역:N', title='행정구역'),
            tooltip=[
                alt.Tooltip('행정구역', title='행정구역'),
                alt.Tooltip('연령', title='연령'),
                alt.Tooltip('인구수', title='인구수', format=',')
            ]
        ).interactive()

        st.altair_chart(chart, use_container_width=True)
        st.info("그래프의 범례를 클릭하여 특정 행정구역을 숨기거나 다시 표시할 수 있습니다.")


        st.header("📄 원본 데이터 (상위 5개 행정구역)")
        st.dataframe(df_top5.style.format('{:,}'))

    else:
        st.warning("데이터를 처리할 수 없습니다. 파일이 올바른지 확인해주세요.")

if __name__ == "__main__":
    main()
