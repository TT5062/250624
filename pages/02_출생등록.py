import streamlit as st
import pandas as pd
import numpy as np

# 페이지 설정 (한국어 제목을 위해)
st.set_page_config(page_title="월별 출생 등록 현황 분석")

@st.cache_data
def load_data(file_path):
    """
    EUC-KR로 인코딩된 CSV 파일을 로드하고 기본 전처리를 수행합니다.
    - 파일 경로: file_path
    - 반환: 전처리된 DataFrame
    """
    try:
        # EUC-KR 인코딩으로 CSV 파일 읽기
        df = pd.read_csv(file_path, encoding='EUC-KR', thousands=',')
        return df
    except FileNotFoundError:
        st.error("파일을 찾을 수 없습니다. '202505_202505_주민등록인구기타현황(출생등록)_월간.csv' 파일이 같은 디렉토리에 있는지 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"데이터 로딩 중 오류가 발생했습니다: {e}")
        return None

def process_data(df):
    """
    데이터를 분석하고 시각화에 적합한 형태로 가공합니다.
    - 입력: 원본 DataFrame
    - 반환: (상위 5개 지역 이름 리스트, 시각화용 DataFrame)
    """
    # '전국' 데이터 제외
    df_local = df[df['행정구역'] != '전국'].copy()

    # '총인구수', '세대수' 등 불필요한 초기 컬럼이 있다면 제거
    # '계' 컬럼을 기준으로 상위 5개 지역을 찾기 위해 숫자형으로 변환
    # 이미 thousands=',' 옵션으로 숫자형 변환이 시도되었으므로, 추가 확인
    if '계' not in df_local.columns:
        st.error("'계' 컬럼을 찾을 수 없습니다. 데이터 형식을 확인해주세요.")
        return None, None

    # 데이터 정제를 위해 숫자형으로 변환되지 않은 컬럼을 찾아 처리
    for col in df_local.columns:
        if df_local[col].dtype == 'object':
            try:
                # 콤마 제거 후 숫자 변환
                df_local[col] = df_local[col].str.replace(',', '').astype(int)
            except (ValueError, AttributeError):
                continue # 숫자 변환이 안되는 컬럼(예: 행정구역)은 그대로 둠

    # '계'를 기준으로 내림차순 정렬하여 상위 5개 행정구역 추출
    top5_districts = df_local.sort_values(by='계', ascending=False).head(5)
    top5_names = top5_districts['행정구역'].tolist()

    # 행정구역을 인덱스로 설정
    df_local.set_index('행정구역', inplace=True)

    # 연령 관련 컬럼만 선택 (0세 ~ 100세 이상)
    # '계' 와 같은 집계 컬럼을 제외하기 위해 숫자 형태의 연령 컬럼을 찾습니다.
    age_columns = [col for col in df_local.columns if '세' in col]
    if not age_columns: # '세'가 없는 경우 (e.g. '0', '1', ...)
        age_columns = [col for col in df_local.columns if col.isdigit()]
    
    if not age_columns:
        # '계'와 '총인구수', '세대수' 등 알려진 비-연령 컬럼을 제외하는 방식
        non_age_cols = ['총인구수', '세대수', '남', '여', '한국인 남', '한국인 여', '외국인 남', '외국인 여', '계']
        age_columns = [col for col in df_local.columns if col not in non_age_cols and '구성비' not in col]


    # 상위 5개 지역의 연령별 데이터만 추출
    chart_data = df_local.loc[top5_names, age_columns]

    # 시각화를 위해 행과 열을 바꿈 (Transpose)
    chart_data_transposed = chart_data.transpose()

    return top5_names, chart_data_transposed

# --- Streamlit UI 구성 ---

st.title("📊 2025년 5월 출생 등록 현황 분석")

# 데이터 로드
file_name = '202505_202505_주민등록인구기타현황(출생등록)_월간.csv'
raw_data = load_data(file_name)

if raw_data is not None:
    # 데이터 처리 및 분석
    top5_names, chart_data = process_data(raw_data.copy())

    if top5_names and chart_data is not None:
        st.header("👶 출생아 수 상위 5개 지역 (연령별)")
        st.write(f"2025년 5월 한 달간 출생 등록이 가장 많았던 **{', '.join(top5_names)}** 지역의 연령별 출생아 수입니다.")

        # 선 그래프 시각화
        st.line_chart(chart_data)
        st.info("그래프의 가로축은 '출생자의 모(母) 연령'을, 세로축은 '해당 연령의 출생아 수'를 나타냅니다.")

        st.divider()

    # 원본 데이터 표시
    st.header("📄 원본 데이터")
    st.write("분석에 사용된 2025년 5월 전체 출생 등록 현황 원본 데이터입니다.")
    st.dataframe(raw_data)
