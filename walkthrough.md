# MTGA Swapper Web UI - 실행 및 검증 가이드

새로운 웹 UI가 성공적으로 구현되었습니다. 아래 절차에 따라 실행하고 기능을 검증해 보세요.

## 1. 실행 방법

프로젝트 루트 디렉토리(`c:\gitrepo\MTGA_Swapper`)에서 다음 명령어를 실행하여 백엔드와 프론트엔드 서버를 동시에 시작합니다.

```bash
.venv\Scripts\python.exe run_web.py
```

이 스크립트는 다음 작업을 수행합니다:
1.  **백엔드 서버 시작**: `http://localhost:8000` (FastAPI)
2.  **프론트엔드 서버 시작**: `http://localhost:5173` (Vite/React)
    *   *참고: 처음 실행 시 프론트엔드 의존성 설치(`npm install`)로 인해 시간이 조금 걸릴 수 있습니다.*

## 2. 검증 체크리스트

브라우저에서 `http://localhost:5173`으로 접속하여 다음 기능들을 확인해 주세요.

### [ ] 설정 (Settings)
1.  상단 메뉴에서 **Settings** 탭을 클릭합니다.
2.  **MTGA Database Path**가 자동으로 감지되었는지 확인합니다. (비어 있다면 기존 앱에서 사용하던 `.mtga` 파일 경로를 입력하세요)
3.  **Image Save Path**에 이미지를 저장할 폴더 경로를 입력합니다.
4.  **Save Changes** 버튼을 누르고 "Configuration saved successfully!" 메시지가 뜨는지 확인합니다.

### [ ] 카드 검색 (Card Browser)
1.  **Card Browser** 탭으로 이동합니다.
2.  카드 목록이 로드되는지 확인합니다.
3.  검색창에 카드 이름(예: "Lotus")을 입력하고 결과가 필터링되는지 확인합니다.
4.  카드 이미지가 정상적으로 표시되는지 확인합니다. (이미지가 없다면 "No Image"로 표시됨)

### [ ] 아트 교체 (Asset Editor)
1.  목록에서 임의의 카드를 클릭하여 **Asset Editor** 모달을 엽니다.
2.  현재 아트(Current Art)가 표시되는지 확인합니다.
3.  **Choose File** 버튼을 눌러 교체할 새 이미지(PNG/JPG)를 선택합니다.
4.  **Swap Art** 버튼을 클릭합니다.
5.  "Art swapped successfully!" 메시지가 뜨고, 현재 아트가 새 이미지로 업데이트되는지 확인합니다.

### [ ] 스타일 잠금 해제 (Style Unlock)
1.  **Asset Editor**에서 **Unlock Parallax Style** 버튼을 클릭합니다.
2.  확인 팝업에서 확인을 누릅니다.
3.  "Style unlocked successfully!" 메시지가 뜨는지 확인합니다.

### [ ] 일괄 스타일 잠금 해제 (Batch Unlock)
1.  검색창에 원하는 카드 이름(예: "Sheoldred")을 입력합니다.
2.  검색창 아래의 **"Unlock All Parallax Styles"** 버튼을 클릭합니다.
3.  확인 팝업에서 확인을 누릅니다.
4.  "Unlocked styles for X cards" 메시지가 뜨는지 확인합니다.

## 3. 문제 해결
- **서버가 켜지지 않나요?**
    - 터미널에서 에러 메시지를 확인해 주세요.
    - 포트 8000번이나 5173번이 이미 사용 중인지 확인해 주세요.
- **이미지가 안 보이나요?**
    - Settings에서 올바른 Database Path가 설정되었는지 다시 확인해 주세요.

## 4. 재설계된 UI (Redesigned UI)

사용자 스케치에 따라 재설계된 화면입니다.
- **네비게이션**: 상단 분리형 레이아웃
- **검색창**: 중앙 배치 및 크기 확대
- **카드 목록**: 세로형 카드 디자인 (Title - Image - Metadata) 및 반응형 그리드 적용

![Redesigned UI](/C:/Users/99san/.gemini/antigravity/brain/4aaec529-61fd-4ffd-b6ac-f29e3809303b/new_card_grid_restarted_1763870773574.png)

**확인 방법**: 검색창에 "vivi" 등을 입력하면 새로운 세로형 카드 레이아웃을 확인할 수 있습니다.
*(변경 사항 적용을 위해 서버를 재시작했습니다. 브라우저를 새로고침해 주세요.)*

**실행 녹화 영상:**
![Redesigned UI Recording](/C:/Users/99san/.gemini/antigravity/brain/4aaec529-61fd-4ffd-b6ac-f29e3809303b/new_card_grid_after_restart_1763870734407.webp)
