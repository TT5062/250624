import streamlit as st
import pandas as pd

# --- 페이지 설정 ---
st.set_page_config(
    page_title="2025년 5월 연령별 인구 현황",
    layout="wide"
)

# --- 데이터 로딩 및 전처리 함수 ---
@st.cache_data
def load_and_process_data(file_path):
    """
    CSV 파일을 로드하고 요청사항에 맞게 전처리합니다.
    - EUC-KR 인코딩으로 파일을 읽습니다.
    - 불필요한 전국 데이터를 제거합니다.
    - 컬럼 이름을 연령 숫자 등으로 간결하게 변경합니다.
    - 인구수 관련 컬럼을 숫자 형식으로 변환합니다.
    """
    # EUC-KR 인코딩으로 CSV 파일 읽기
    df = pd.read_csv(file_path, encoding='EUC-KR', thousands=',')

    # 첫 번째 행 '전국' 데이터 제외
    if '전국' in df.iloc[0]['행정구역']:
        df = df.iloc[1:].reset_index(drop=True)

    # 컬럼 이름 전처리
    new_columns = {}
    for col in df.columns:
        if '총인구수' in col:
            new_columns[col] = '총인구수'
        elif '_계_' in col:
            # '2025년05월_계_10세' -> '10'
            age = col.split('_계_')[-1].replace('세', '').replace(' 이상', '')
            new_columns[col] = age
        else:
            new_columns[col] = col # '행정구역' 컬럼 유지

    df = df.rename(columns=new_columns)

    # '행정구역' 컬럼에서 괄호 안의 지역 코드 제거 (예: "서울특별시 (1100000000)")
    df['행정구역'] = df['행정구역'].str.split(' ').str[0]

    # 숫자형으로 변환해야 할 컬럼 선택 (나이 컬럼과 총인구수)
    # 컬럼 이름이 숫자로만 구성된 경우와 '총인구수'를 선택
    numeric_cols = [col for col in df.columns if col.isdigit()] + ['총인구수']

    # 쉼표(,)를 제거하고 숫자형으로 변환
    for col in numeric_cols:
        # 이미 thousands=',' 옵션으로 처리되었으므로 직접 변환만 수행
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    return df

# --- UI 및 시각화 ---
st.title("📄 2025년 5월 기준 행정구역별 연령별 인구 현황")
st.write("제공된 CSV 파일을 바탕으로 총인구수 기준 상위 5개 행정구역의 연령별 인구 분포를 나타낸 대시보드입니다.")

try:
    # 데이터 로드
    file_path = '202505_202505_연령별인구현황_월간.csv'
    processed_df = load_and_process_data(file_path)

    # 총인구수 기준 상위 5개 행정구역 추출
    top5_df = processed_df.sort_values(by='총인구수', ascending=False).head(5)
    top5_df = top5_df.reset_index(drop=True)


    st.header("📊 총인구수 상위 5개 행정구역")
    st.dataframe(top5_df[['행정구역', '총인구수']].style.format({'총인구수': '{:,}'}))


    st.header("📈 연령별 인구 분포 선 그래프 (상위 5개 행정구역)")
    st.write("그래프의 각 선은 행정구역을 나타내며, X축은 나이, Y축은 해당 나이의 인구수를 의미합니다.")

    # 차트용 데이터 준비
    # '행정구역'을 인덱스로 설정하고, 나이(0세~100세 이상) 컬럼만 선택
    age_cols = [col for col in processed_df.columns if col.isdigit() or col == '100']
    chart_df = top5_df.set_index('행정구역')[age_cols]

    # st.line_chart는 index를 x축, column을 y축으로 사용하므로, 데이터를 전치(Transpose)
    st.line_chart(chart_df.T)


    # 원본 데이터 표시
    st.header("💿 원본 데이터 (전처리 후)")
    st.dataframe(processed_df)

except FileNotFoundError:
    st.error(f"'{file_path}' 파일을 찾을 수 없습니다. 앱과 동일한 디렉토리에 파일이 있는지 확인해주세요.")
except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
