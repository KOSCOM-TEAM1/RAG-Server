from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env 파일과 환경 변수에서 설정을 읽어옵니다.
    # 기본 파일 경로는 'data/bigkinds_detailed_result.json' 입니다.
    json_file_path: str = "data/bigkinds_detailed_result.json"

    # .env 파일을 사용하도록 설정
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

# 설정 객체 인스턴스 생성
settings = Settings()
