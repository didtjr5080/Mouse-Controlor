# emg_camera_mouse

Python 기반 보조공학/HCI MVP입니다. 웹캠으로 손 또는 얼굴/눈 위치를 추적해 마우스 커서를 이동하고, 실제 EMG 센서가 없는 현재 버전에서는 키보드 입력으로 EMG 수축 이벤트를 시뮬레이션합니다.

주의: 첫 실행 시 커서가 예상보다 빠르게 움직일 수 있습니다. 안전 테스트를 먼저 하려면 `config.py`에서 `ENABLE_MOUSE_MOVE = False`, `ENABLE_MOUSE_CLICK = False`로 바꾼 뒤 좌표 추적과 로그부터 확인하세요. 위험하게 움직이면 마우스를 화면 좌상단 모서리로 이동해 `pyautogui` FAILSAFE를 발동할 수 있습니다.

## 현재 기능

- OpenCV 웹캠 화면 표시
- `CONTROL_MODE = "hand"`: MediaPipe Hands 또는 MediaPipe Tasks로 검지 끝 landmark 8 추적
- `CONTROL_MODE = "gaze"`: OpenCV 얼굴/눈 검출 기반 시선 근사 추적
- normalized 좌표를 화면 좌표로 변환
- smoothing을 적용한 마우스 이동
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

Git Bash에서는 다음처럼 가상환경을 활성화합니다.

```bash
source .venv/Scripts/activate
pip install -r requirements.txt
```

최신 `mediapipe` 패키지는 손 추적 첫 실행 시 `models/hand_landmarker.task` 모델 파일이 필요합니다. 프로그램이 자동 다운로드를 시도하지만, 네트워크가 막혀 있으면 다음 주소에서 직접 받은 뒤 `models/hand_landmarker.task`로 저장하세요.

```text
https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

## 실행 방법

```powershell
python main.py
```

## 모드 선택

[config.py](config.py)에서 선택합니다.

```python
CONTROL_MODE = "hand"
```

손 대신 시선 근사 제어를 쓰려면 다음처럼 바꿉니다.

```python
CONTROL_MODE = "gaze"
```

시선 모드는 일반 웹캠만 사용하는 근사 방식입니다. 실제 아이트래커처럼 정확하지 않으며, 얼굴 위치와 눈 검출 결과를 이용해 화면 위치를 추정합니다. 사용자, 조명, 카메라 위치에 따라 아래 값을 조정하세요.

```python
GAZE_SENSITIVITY_X = 1.8
GAZE_SENSITIVITY_Y = 1.4
GAZE_DEADZONE = 0.04
```

## 조작법

- 손 모드: 손을 카메라에 보이면 검지 끝 위치에 따라 커서가 이동합니다.
- 시선 모드: 얼굴을 카메라 중앙에 두고 고개/눈 방향을 움직이면 커서가 이동합니다.
- `Space`: 좌클릭
- `R`: 우클릭
- `D`: 드래그 토글
- `Q` 또는 `ESC`: 종료

## 안전 테스트 방법

1. `config.py`에서 `ENABLE_MOUSE_MOVE = False`, `ENABLE_MOUSE_CLICK = False`로 설정합니다.
2. `CONTROL_MODE`를 `"hand"` 또는 `"gaze"`로 설정합니다.
3. `python main.py`를 실행합니다.
4. 웹캠 창이 열리는지 확인합니다.
5. 손 모드에서는 손을 보였을 때 `Hand detected`와 검지 끝 초록 점이 표시되는지 확인합니다.
6. 시선 모드에서는 얼굴과 눈 주변 박스, 노란 목표점이 표시되는지 확인합니다.
7. `Space`, `R`, `D`를 눌러 화면 상태와 `logs/session_log.csv`에 이벤트가 기록되는지 확인합니다.
8. 문제가 없으면 `ENABLE_MOUSE_MOVE = True`로 바꿔 커서 이동을 테스트합니다.
9. 마지막으로 필요할 때만 `ENABLE_MOUSE_CLICK = True`로 바꿔 클릭을 테스트합니다.

## 로그

실행 중 다음 파일이 자동 생성됩니다.

```text
logs/session_log.csv
```

저장 컬럼은 다음과 같습니다.

```text
timestamp, hand_detected, hand_x, hand_y, screen_x, screen_y, event
```

현재 컬럼명은 기존 손 추적 MVP와 호환되도록 유지했습니다. 시선 모드에서는 `hand_x`, `hand_y`에 시선 근사 목표점의 카메라 좌표가 저장됩니다.

## 추후 EMG 센서 확장

현재 `main.py`는 `emg_input_simulator.py`의 `EMGInputSimulator`를 사용합니다. Arduino와 EMG 센서를 연결한 뒤에는 `emg_serial.py`의 `EMGSerialInput`을 사용해 serial 값을 읽고, 임계값을 넘는 값을 `LEFT_CLICK`, `RIGHT_CLICK`, `DRAG_TOGGLE` 같은 이벤트로 변환하는 어댑터를 추가하면 됩니다.

예상 흐름:

1. Arduino가 EMG 값을 한 줄에 숫자 하나씩 serial 출력합니다.
2. `EMGSerialInput(port="COM3", baudrate=115200).connect()`로 연결합니다.
3. `read_value()`로 값을 읽습니다.
4. 값이 정한 임계값 이상이면 클릭 이벤트로 변환합니다.
5. `main.py`에서 `EMGInputSimulator` 대신 serial 기반 입력 클래스를 사용합니다.

## 문제 해결

- `mediapipe` 설치 오류가 나면 Python 3.10 또는 3.11 환경인지 확인하세요.
- `module 'mediapipe' has no attribute 'solutions'` 오류가 나면 최신 MediaPipe Tasks 패키지가 설치된 상태입니다. 현재 코드는 이 경우 `models/hand_landmarker.task` 모델을 사용합니다.
- 모델 자동 다운로드가 실패하면 위 모델 URL에서 직접 받아 `models/hand_landmarker.task`에 저장하세요.
- 카메라가 켜지지 않으면 `config.py`의 `CAMERA_INDEX`를 `1` 또는 다른 숫자로 바꿔보세요.
- 시선 모드가 흔들리면 조명을 밝게 하고, 얼굴이 카메라 정면에 오게 한 뒤 `GAZE_DEADZONE`을 조금 키워보세요.
- 마우스가 위험하게 움직이면 화면 좌상단으로 이동하여 `pyautogui` FAILSAFE를 발동하세요.
- 테스트 중 실제 커서 이동이나 클릭을 막으려면 `ENABLE_MOUSE_MOVE = False`, `ENABLE_MOUSE_CLICK = False`로 설정하세요.
