# gaze_emg_mouse

최종 주제명: **시선 방향과 근전도 입력을 활용한 보조 마우스 제어 시스템**

Python 기반 보조공학/HCI MVP입니다. 웹캠으로 얼굴 또는 눈 방향을 추정해 마우스 커서를 이동하고, 실제 EMG 센서가 없는 현재 버전에서는 키보드 입력으로 EMG 수축 이벤트를 시뮬레이션합니다.

현재 버전의 1차 목표는 정확한 시선 좌표 추적이 아니라 **얼굴 방향 기반 상대 커서 이동**입니다. 얼굴 기준점이 카메라 중앙에서 벗어난 방향으로 커서가 계속 움직이고, 중앙 dead zone 안에서는 멈춥니다.

주의: 첫 실행 시 마우스 이동이 위험할 수 있으므로 기본값은 `ENABLE_MOUSE_MOVE = False`, `ENABLE_MOUSE_CLICK = False`입니다. 추적이 안정적인 것을 확인한 뒤 `True`로 바꾸세요. 위험하게 움직이면 마우스를 화면 좌상단으로 이동해 `pyautogui` FAILSAFE를 발동할 수 있습니다.

## 현재 기능

- OpenCV 웹캠 화면 표시
- MediaPipe Face Mesh 또는 Face Landmarker로 얼굴 landmark 추적
- 코 끝 landmark 1번을 기준점으로 사용
- 얼굴 기준점과 화면 중앙 차이로 상대 이동량 계산
- dead zone, smoothing, speed scaling 적용
- 키보드 기반 EMG 이벤트 시뮬레이션
- 클릭 cooldown 적용
- `logs/session_log.csv`에 추적 상태와 이벤트 저장

## 설치 방법

Python 3.10 또는 3.11 사용을 권장합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Git Bash:

```bash
source .venv/Scripts/activate
pip install -r requirements.txt
```

최신 `mediapipe` 패키지는 첫 실행 시 `models/face_landmarker.task` 모델 파일이 필요할 수 있습니다. 프로그램이 자동 다운로드를 시도하지만, 네트워크가 막혀 있으면 다음 주소에서 직접 받아 저장하세요.

```text
https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
```

## 실행 방법

```powershell
python main.py
```

실행 시 콘솔에 현재 설정값이 출력됩니다.

## 조작법

- 얼굴을 카메라에 보이면 얼굴 방향에 따라 커서 이동량 `dx, dy`가 변합니다.
- `Space`: 좌클릭
- `R`: 우클릭
- `D`: 드래그 토글
- `Q` 또는 `ESC`: 종료

## config.py 설정

- `ENABLE_MOUSE_MOVE`: `False`이면 실제 마우스는 움직이지 않고 화면/로그에 이동량만 표시합니다.
- `ENABLE_MOUSE_CLICK`: `False`이면 실제 클릭하지 않고 이벤트만 표시/기록합니다.
- `DEAD_ZONE_X`, `DEAD_ZONE_Y`: 화면 중앙 근처 정지 영역 크기입니다.
- `MOUSE_SPEED`: 얼굴 offset을 실제 마우스 상대 이동량으로 바꾸는 배율입니다.
- `SMOOTHING`: 커서 이동을 부드럽게 만드는 값입니다. 낮을수록 느리고 부드럽습니다.
- `TRACKING_MODE`: 기본값은 `"face"`입니다. `"gaze"`는 실험용 skeleton입니다.

## 안전 테스트

1. `config.py`에서 `ENABLE_MOUSE_MOVE = False`, `ENABLE_MOUSE_CLICK = False`인지 확인합니다.
2. `python main.py`를 실행합니다.
3. 웹캠 창이 열리는지 확인합니다.
4. 얼굴을 보이면 `Face: Detected`가 표시되는지 확인합니다.
5. 코 위치 또는 기준점이 화면에 표시되는지 확인합니다.
6. 얼굴을 좌우/상하로 움직일 때 `dx, dy`가 변하는지 확인합니다.
7. `Space`, `R`, `D`를 눌러 이벤트가 화면과 로그에 기록되는지 확인합니다.
8. `Q` 또는 `ESC`로 종료되는지 확인합니다.
9. 안정적이면 `ENABLE_MOUSE_MOVE = True`로 바꿔 상대 이동을 테스트합니다.
10. 마지막으로 필요할 때만 `ENABLE_MOUSE_CLICK = True`로 바꿔 클릭을 테스트합니다.

## 로그

실행 중 다음 파일이 자동 생성됩니다.

```text
logs/session_log.csv
```

저장 컬럼:

```text
timestamp, face_detected, tracking_mode, face_x, face_y, dx, dy, event
```

## 추후 확장

`gaze_tracker.py`는 눈동자/홍채 방향 추정 기능을 넣기 위한 skeleton입니다. 이후 iris landmark, 사용자별 보정, blink filtering, dwell click 같은 기능을 추가할 수 있습니다.

실제 Arduino + EMG 센서를 연결할 때는 `emg_serial.py`의 `EMGSerialInput`을 사용해 serial 값을 읽고, 임계값 이상일 때 클릭 이벤트로 변환하는 어댑터를 추가하면 됩니다. 그 뒤 `main.py`에서 `EMGInputSimulator`를 serial 기반 입력 클래스로 교체합니다.

## 문제 해결

- `mediapipe` 설치 오류가 나면 Python 3.10 또는 3.11 환경인지 확인하세요.
- 카메라가 켜지지 않으면 `config.py`의 `CAMERA_INDEX`를 `1` 또는 다른 숫자로 바꿔보세요.
- 얼굴 추적이 흔들리면 `DEAD_ZONE_X`, `DEAD_ZONE_Y`를 키우거나 `MOUSE_SPEED`를 낮추세요.
- 마우스가 위험하게 움직이면 화면 좌상단으로 이동하여 `pyautogui` FAILSAFE를 발동하세요.
- `module 'mediapipe' has no attribute 'solutions'`가 보여도 현재 코드는 MediaPipe Tasks API로 fallback합니다.
