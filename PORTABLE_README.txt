AI Video & Image Upscaler - Portable
=====================================

1. ZIP 파일을 영문 경로의 폴더에 완전히 압축 해제합니다.
2. VideoUpscaler.exe를 실행합니다.
3. AI 엔진 설치 버튼을 누를 필요 없이 바로 사용할 수 있습니다.

이미지 업스케일:
- 이미지 업스케일 탭에서 파일 하나 또는 폴더 전체를 선택할 수 있습니다.
- 2배/4배, 실사/애니메이션, PNG/JPG/WebP 출력을 지원합니다.
- PNG/WebP 출력은 투명도를 유지합니다. JPG는 투명 영역을 흰색으로 합성합니다.
- 기존 결과 덮어쓰기를 끄면 이미 처리한 파일을 건너뛰어 이어서 실행합니다.
- 이미지 파일이나 폴더를 VideoUpscaler.exe 위에 끌어놓아 열 수 있습니다.

영상 노이즈 제거:
- 영상 노이즈 제거 탭은 해상도와 FPS를 유지하고 얼룩·압축 노이즈만 정리합니다.
- 기본값은 균형 (클린 영상 권장), H.265 10비트, 고화질입니다.
- 색 띠/밴딩 완화는 그라데이션이 계단처럼 뭉친 영상에서만 켜는 것을 권장합니다.
- 이 기능은 FFmpeg 기반이라 AI 엔진이나 Vulkan GPU 없이도 사용할 수 있습니다.

포함 구성:
- 영상 탭의 원본 보존: AI와 원본 Lanczos 확대를 혼합 (30%/50%/70%). 가는 장신구는 30%부터 테스트하세요.
- Python/Tkinter가 포함된 VideoUpscaler.exe
- FFmpeg/ffprobe GPL shared Windows build
- Real-ESRGAN 실행 파일과 실사/애니메이션 필수 모델
- RIFE 실행 파일과 rife-v4.6/rife-anime 모델

캐시와 처리 프레임은 기본적으로 %LOCALAPPDATA%\VideoUpscalerAI에 저장됩니다.
Windows 사용자명에 비 ASCII 문자가 있으면 %PUBLIC%\VideoUpscalerAI를 사용합니다.

주의:
- 이 실행 파일은 코드 서명이 없어 Windows SmartScreen 경고가 표시될 수 있습니다.
- 긴 영상은 캐시 때문에 수십~수백 GB의 임시 저장 공간이 필요할 수 있습니다.
- third_party 폴더에서 제3자 구성요소의 원문 라이선스와 안내문을 확인할 수 있습니다.

