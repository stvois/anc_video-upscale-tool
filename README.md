# AI Video & Image Upscaler (Windows)

Windows용 로컬 영상·이미지 업스케일링 GUI입니다. Python GUI에서 FFmpeg와 독립 실행형 Real-ESRGAN/RIFE 엔진을 호출하며, 별도의 Python 패키지는 필요하지 않습니다.

## 주요 기능

- Real-ESRGAN 기반 2배/4배 AI 업스케일
- 실사 및 애니메이션 전용 모델
- FFmpeg 기반 노이즈 제거
- RIFE 기반 FPS 2배 프레임 보간
- NVIDIA NVENC 자동 감지 및 CPU 인코딩 대체 경로
- MP4 H.264/H.265 및 MKV 출력
- 오디오, 자막, 메타데이터 보존
- 중단 후 이어하기 캐시
- PNG/JPG/WebP 이미지 2배/4배 업스케일
- 단일 이미지 및 폴더 일괄 처리
- PNG/WebP 투명도 보존, JPG 흰색 배경 합성
- 기존 결과 자동 건너뛰기와 폴더 일괄 이어하기
- 해상도와 FPS를 유지하는 영상 노이즈 제거 전용 탭
- 얼룩·압축 노이즈 3단계 제거 및 선택형 밴딩 완화
- H.265 10비트 클린 출력으로 그라데이션 재손상 억제
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
5. 영상 또는 이미지 탭에서 입력, 확대 배율, 종류, 출력 형식을 선택하고 실행합니다.

이미지는 파일 하나를 선택하거나 폴더 전체를 한 번에 처리할 수 있습니다. 이미지/폴더를 `VideoUpscaler.exe` 위에 끌어놓아 바로 열 수도 있습니다.

업스케일 없이 영상의 얼룩덜룩한 압축 노이즈만 정리하려면 **영상 노이즈 제거** 탭을 사용합니다. 기본 `균형 (클린 영상 권장)` 설정은 제공된 클린 참조 영상과 가장 가까운 결과를 내도록 맞췄습니다. 이 기능은 FFmpeg만 사용하므로 AI 엔진 없이도 실행됩니다.

AI 엔진 설치 전에도 `일반 고품질 (Lanczos)` 모드는 사용할 수 있습니다.

## EXE 빌드

Python 소스 대신 단일 실행 파일이 필요하면 PowerShell에서 다음을 실행합니다.

```powershell
.\build_exe.ps1
```

`dist\VideoUpscaler.exe`가 생성됩니다. EXE에는 Python/Tkinter와 AI 엔진 설치 스크립트가 포함되므로 실행 PC에 Python이 필요하지 않습니다. AI 모델은 처음 실행 후 **AI 엔진 설치** 버튼으로 내려받습니다. FFmpeg가 PATH에 없으면 `ffmpeg.exe`와 `ffprobe.exe`를 EXE 옆이나 `ffmpeg\bin` 폴더에 둘 수 있습니다.

Python, FFmpeg, Real-ESRGAN과 RIFE 필요 모델을 한 폴더에 포함한 포터블 ZIP은 다음 명령으로 생성합니다.

```powershell
.\build_portable.ps1
```

결과물은 `dist\VideoUpscaler-Portable`과 `dist\VideoUpscaler-Portable.zip`입니다. 압축을 풀고 `VideoUpscaler.exe`를 실행하면 별도 설치 없이 영상·이미지 AI 업스케일과 프레임 보간을 사용할 수 있습니다.

## 권장 설정

### SDR 고정밀 AI

NVIDIA PC에서는 `고정밀 엔진 설치`가 CUDA 12.8용 PyTorch 2.11.0/torchvision 0.26.0을 설치합니다. 기존 CPU 버전도 이 버튼으로 교체합니다. `고정밀 장치`의 자동은 NVIDIA 우선이며, NVIDIA GPU(CUDA)를 명시하면 CUDA가 없을 때 오류로 안내합니다. 로그의 `Device: cuda` 및 GPU 이름으로 AI 추론 장치를 확인하세요. NVIDIA 하드웨어 인코딩 체크는 최종 인코딩용이며 이 선택과 독립적입니다. CUDA 엔진은 별도 설치되어 포터블 ZIP 크기는 유지되지만 설치 시 수 GB가 추가됩니다.

`고정밀 엔진 설치`로 Python 3.10 기반 전용 환경(PyTorch, Spandrel, OpenCV)과 공식 Real-ESRGAN 모델을 설치합니다. Python 3.10 및 인터넷이 필요하며, 엔진은 사용자 데이터 폴더의 `precision`에 별도 저장됩니다. NVIDIA 감지 시 CUDA 버전을 설치하고 실제 GPU 연산으로 확인합니다. CPU는 긴 영상에 매우 느릴 수 있습니다.

영상 탭에서 `고정밀 AI (16비트 SDR)`, H.265 10비트, 노이즈 제거 사용 안 함, RIFE 끔을 선택하세요. 16비트 RGB PNG 추출 → float32 AI 및 원본 혼합 → 16비트 PNG → 10비트 출력 경로입니다. 실사와 애니메이션, 2배/4배를 지원합니다. 2배는 모델의 4배 추론 결과를 고정밀 축소합니다. 프레임 캐시 용량과 RAM 사용량이 증가합니다. HDR/BT.2020은 거부하며 BT.709 SDR용입니다. AI는 원본 색 정보의 무손실 보존을 보장하지 않습니다. 고정밀 엔진은 포터블 ZIP에 포함되지 않으므로 다른 PC에서 별도 설치해야 합니다.

설치 후 `py -3 test_precision_integration.py`로 실제 모델 추론 및 16비트 중간 프레임/10비트 출력 검증을 실행할 수 있습니다.

영상 업스케일 출력 형식에서 `MP4 H.265 10비트` 또는 `MKV H.265 10비트`를 선택할 수 있습니다. CPU와 NVIDIA 인코딩을 지원합니다. 현재 중간 PNG/AI 처리는 8비트이므로 이는 최종 인코딩의 10비트 출력이며 원본 10비트 정보의 무손실 보존을 의미하지 않습니다. HDR 색상 및 밝기 보존은 지원하지 않습니다.

이미지 탭에서도 `원본 보존`을 사용해 AI 결과와 원본 Lanczos 확대를 혼합할 수 있습니다. 기본값은 영상과 같은 70%이며, 사용 안 함·30%·50%·70% 중 선택합니다. 투명 이미지의 알파는 원본 확대 결과에서 유지합니다. AI 모드에서만 적용됩니다.

가는 목걸이 줄이나 귀걸이가 AI에서 뭉개지면 영상 탭의 `원본 보존`을 `원본 30%`부터 시험하세요. AI 프레임과 노이즈 제거 전 원본의 Lanczos 확대 프레임을 섞습니다. 50%·70%로 높이면 원본 형태가 더 남지만 선명도가 낮아지고 원본 노이즈도 돌아올 수 있습니다. AI 처리 방식에서만 적용되며, RIFE 보간 전에 혼합합니다. 옵션 변경 시 캐시는 별도로 생성됩니다.

- 일반 실사: `2배`, `실사 / 범용`, 노이즈 `약하게`, H.265 `균형`
- 이미 깨끗한 AI 생성 실사: 노이즈 `사용 안 함`
- 애니메이션: `2배`, `애니메이션 / 일러스트`, 노이즈 `사용 안 함`
- 사진: 이미지 탭의 `실사 / 범용`, PNG 또는 고품질 JPG
- 일러스트·투명 PNG: `애니메이션 / 일러스트`, PNG 출력
- 자막과 여러 오디오 트랙을 안전하게 보존하려면 MKV 사용
- 클린 처리: `균형`, H.265 10비트, 고화질을 먼저 권장
- 색이 계단처럼 뭉치는 밴딩이 보일 때만 `색 띠/밴딩도 완화` 사용

## 저장 위치와 이동

프로그램 폴더는 어느 드라이브나 경로에 놓아도 됩니다. AI 엔진과 캐시는 기본적으로 `%LOCALAPPDATA%\VideoUpscalerAI`에 저장됩니다. Windows 사용자명에 비 ASCII 문자가 있으면 `%PUBLIC%\VideoUpscalerAI`를 자동 사용합니다. `VIDEO_UPSCALER_DATA_DIR` 환경 변수로 영문 경로를 직접 지정할 수도 있습니다.

캐시는 입력 파일의 절대 경로와 수정 정보를 사용하므로 다른 컴퓨터로 복사하지 않는 것을 권장합니다. 긴 영상은 무손실 PNG 캐시 때문에 수십~수백 GB의 여유 공간이 필요할 수 있습니다.

## 구성

- `video_upscaler_gui.py`: Tkinter GUI
- `video_upscaler_core.py`: 영상·이미지 처리 파이프라인
- `setup_video_ai_engines.ps1`: 공식 릴리스에서 AI 엔진 설치
- `run_video_upscaler.bat`: Python 자동 감지 및 실행
- `build_exe.ps1`: PyInstaller 단일 EXE 빌드
- `build_portable.ps1`: FFmpeg와 선별 AI 모델을 포함한 포터블 패키지 빌드

## 제3자 구성 요소

설치 스크립트는 다음 프로젝트의 공식 릴리스를 다운로드합니다. 이 저장소는 해당 바이너리나 모델을 직접 포함하지 않습니다.

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
- [RIFE ncnn Vulkan](https://github.com/nihui/rife-ncnn-vulkan)
- [FFmpeg](https://ffmpeg.org/)

각 구성 요소에는 해당 프로젝트의 라이선스가 적용됩니다. 이 저장소 자체에는 아직 별도의 오픈소스 라이선스가 부여되지 않았습니다.

