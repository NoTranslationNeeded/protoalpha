# 구현 계획 - 독립 실행형 EXE 빌드 (Standalone Executable Build)

사용자가 Python이나 Node.js 설치 없이도 프로그램을 실행할 수 있도록, PyInstaller를 사용하여 단일 실행 파일(또는 폴더)로 패키징합니다.

## 사용자 검토 필요
> [!NOTE]
> **빌드 시간**: 빌드 과정은 몇 분 정도 소요될 수 있습니다.
> **결과물 위치**: 빌드가 완료되면 `dist/MTGA_Swapper` 폴더에 실행 파일이 생성됩니다.

## 제안된 변경 사항

### 백엔드 (`backend/`)

#### [MODIFY] [backend/main.py](file:///c:/gitrepo/MTGA_Swapper/backend/main.py)
- 정적 파일 서빙 로직을 활성화합니다.
- `frontend/dist` 폴더가 존재할 경우, 해당 폴더를 `/` 경로에 마운트하여 React 앱을 서빙하도록 수정합니다.
- API 라우터는 `/api` 접두사를 유지합니다.

### 빌드 스크립트 (Root)

#### [NEW] [build_exe.py](file:///c:/gitrepo/MTGA_Swapper/build_exe.py)
- **목적**: 빌드 과정을 자동화하는 스크립트입니다.
- **기능**:
    1. `frontend/` 디렉토리에서 `npm run build` 실행 -> `frontend/dist` 생성.
    2. `pyinstaller` 설치 (없을 경우).
    3. `PyInstaller` 실행:
        - 진입점: `run_web.py` (또는 `backend/main.py`를 직접 실행하는 래퍼 스크립트)
        - 데이터 포함: `frontend/dist` -> `frontend/dist`
        - 숨겨진 임포트: `uvicorn`, `fastapi`, `sqlite3` 등 필요한 라이브러리 명시.
        - 콘솔 표시 여부: 디버깅을 위해 초기에는 콘솔 표시 (`--console`).

## 검증 계획

### 자동화된 빌드
- `python build_exe.py` 실행.

### 수동 검증
1. `dist/MTGA_Swapper/MTGA_Swapper.exe` 실행.
2. 콘솔 창이 뜨고 서버가 시작되는지 확인.
3. 브라우저가 자동으로 열리고 앱이 정상 작동하는지 확인.
4. 다른 컴퓨터(또는 가상머신)에서 실행하여 의존성 문제 없는지 확인 (선택 사항).
