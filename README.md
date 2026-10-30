# AI Video Upscaler (Windows)

Windows용 로컬 영상 업스케일링 GUI입니다. Python GUI에서 FFmpeg와 독립 실행형 Real-ESRGAN/RIFE 엔진을 호출하며, 별도의 Python 패키지는 필요하지 않습니다.

## 주요 기능

- Real-ESRGAN 기반 2배/4배 AI 업스케일
- 실사 및 애니메이션 전용 모델
- FFmpeg 기반 노이즈 제거
- RIFE 기반 FPS 2배 프레임 보간
- NVIDIA NVENC 자동 감지 및 CPU 인코딩 대체 경로
- MP4 H.264/H.265 및 MKV 출력
- 오디오, 자막, 메타데이터 보존
- 중단 후 이어하기 캐시
- 한글 Windows 사용자명과 이동식 프로그램 폴더 지원

실사 모델의 2배 처리는 일부 ncnn 버전의 타일 좌표 오류를 피하기 위해 내부적으로 4배 AI 추론 후 Lanczos 2배 축소를 적용합니다.

## 요구 사항

- Windows 10/11
- Python 3.10 이상
- `ffmpeg`와 `ffprobe`가 PATH에 등록되어 있어야 함
- AI 모드는 Vulkan 지원 GPU 권장

## 빠른 시작

1. 저장소를 내려받거나 ZIP으로 다운로드합니다.
2. `run_video_upscaler.bat --check`로 Python 감지를 확인합니다.
3. `run_video_upscaler.bat`을 더블 클릭합니다.
4. 처음 한 번은 우측 상단의 **AI 엔진 설치**를 누릅니다.
5. 입력 영상, 확대 배율, 영상 종류, 출력 형식을 선택하고 실행합니다.

AI 엔진 설치 전에도 `일반 고품질 (Lanczos)` 모드는 사용할 수 있습니다.

## 권장 설정

- 일반 실사: `2배`, `실사 / 범용`, 노이즈 `약하게`, H.265 `균형`
- 이미 깨끗한 AI 생성 실사: 노이즈 `사용 안 함`
- 애니메이션: `2배`, `애니메이션 / 일러스트`, 노이즈 `사용 안 함`
- 자막과 여러 오디오 트랙을 안전하게 보존하려면 MKV 사용

## 저장 위치와 이동

프로그램 폴더는 어느 드라이브나 경로에 놓아도 됩니다. AI 엔진과 캐시는 기본적으로 `%LOCALAPPDATA%\VideoUpscalerAI`에 저장됩니다. Windows 사용자명에 비 ASCII 문자가 있으면 `%PUBLIC%\VideoUpscalerAI`를 자동 사용합니다. `VIDEO_UPSCALER_DATA_DIR` 환경 변수로 영문 경로를 직접 지정할 수도 있습니다.

캐시는 입력 파일의 절대 경로와 수정 정보를 사용하므로 다른 컴퓨터로 복사하지 않는 것을 권장합니다. 긴 영상은 무손실 PNG 캐시 때문에 수십~수백 GB의 여유 공간이 필요할 수 있습니다.

## 구성

- `video_upscaler_gui.py`: Tkinter GUI
- `video_upscaler_core.py`: 영상 처리 파이프라인
- `setup_video_ai_engines.ps1`: 공식 릴리스에서 AI 엔진 설치
- `run_video_upscaler.bat`: Python 자동 감지 및 실행

## 제3자 구성 요소

설치 스크립트는 다음 프로젝트의 공식 릴리스를 다운로드합니다. 이 저장소는 해당 바이너리나 모델을 직접 포함하지 않습니다.

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
- [RIFE ncnn Vulkan](https://github.com/nihui/rife-ncnn-vulkan)
- [FFmpeg](https://ffmpeg.org/)

각 구성 요소에는 해당 프로젝트의 라이선스가 적용됩니다. 이 저장소 자체에는 아직 별도의 오픈소스 라이선스가 부여되지 않았습니다.

