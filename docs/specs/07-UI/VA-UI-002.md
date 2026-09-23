---
doc_id: VA-UI-002
type: UI
title: 와이어프레임 — 영상 분석 에이전트
status: draft
upstream: [VA-UI-001, VA-UC-001]
---

# 와이어프레임

## 0. 형식

이 문서는 화면마다 **요소가 어디에 있고, 무엇을 보여 주고, 누르면 무엇이 되는지** 정한다. 어떤 화면이 있는지, 어디서 어디로 가는지, 어느 화면에서든 같아야 하는 값과 틀이 무엇인지는 [[VA-UI-001]]이 이미 정했다. 여기서는 그것을 다시 쓰지 않고 가져다 쓴다.

| 이 문서가 정하는 것 | [[VA-UI-001]]이 정하는 것 |
|---|---|
| 화면마다 배치(캔버스를 옮긴 html)와 요소 번호 | 화면 7개와 각 화면의 종류·목적·주 유스케이스(2장) |
| 요소마다 보여 주는 것과 누르면 되는 것 | 화면 사이 이동, 진입·이탈, 주소(5장·6장) |
| 요소 단위 규칙: 상태별 모습, 나타나는 조건, 문구 | 디자인 토큰: 색·글꼴·간격·모서리·움직임·대비(3장) |
| 화면별 시나리오 | 공통 틀: 앱 셸·버튼과 칩·다이얼로그·시각 표기·안내와 오류·접근성(4장) |
| 공통 컴포넌트를 쓰는 곳과 동작(1장) | 보드와 화면 대응(0장) |

- **토큰 값의 원본은 [[VA-UI-001]] 3장·4장이다.** 배치 html의 색·글꼴·크기는 캔버스의 인라인 스타일을 그대로 옮긴 것이라 그 값과 같다. 요소 표와 규칙은 값을 옮겨 적지 않고 부품 이름으로만 부른다.
- 두 문서가 어긋나면 [[VA-UI-001]]을 따른다. 동작이나 값을 바꿀 때는 그 문서를 먼저 고치고 이 문서를 맞춘다. 이 문서가 새로 정하는 것은 [[VA-UI-001]]에 없는 요소 단위 규칙뿐이다.

**화면마다 절 하나.** [[VA-UI-001]] 2장 순서대로 UI-1부터 UI-7까지 둔다. 각 절은 메타 표로 시작하고 아래 네 부분이 이어진다.

| 부분 | 무엇 | 형태 |
|---|---|---|
| 배치 | 화면이 어떻게 생겼고 요소가 어디에 있나 | `html` 코드블록 **하나**. 승인된 디자인 캔버스의 보드를 옮긴 자기 완결 html이고 요소마다 `data-el` 번호. 주 보드 아래에 상태 보드를 잇는다 |
| 요소 | 요소마다 무엇을 보여 주고, 누르면 무엇이 되나 | 표. 열은 `#` · 이름 · 종류 · 보여주는 것 · 누르면. `#`은 배치의 `data-el`과 같은 번호 |
| 규칙 | 상태별 모습, 나타나고 사라지는 조건, 숫자·문구 규칙, 막혔을 때 | 목록. 요소는 번호로 부른다 |
| 시나리오 | 요소들이 이어져 사용자가 무엇을 이루나 | 번호를 매긴 흐름. [[VA-UC-001]]의 유스케이스 흐름을 이 화면에서 누르는 순서로 옮긴 것 |

**사람용 뷰.** 싱크독 웹은 이 문서를 화면별 탭으로 보여 준다. 탭 하나가 화면 하나다. 탭 안 위에 배치가, 아래에 요소 표·규칙·시나리오가 놓인다. 배치는 iframe에 격리해 그대로 그린다 — 「3. 공통 틀」의 글꼴과 기본 스타일이 모든 화면 앞에 함께 들어간다. 요소 번호를 누르면 배치의 그 요소와 표의 그 줄이 함께 강조된다. 뷰는 배치의 `<script>`와 `on…` 속성을 지운다. 그래서 동작은 배치에 쓰지 않고 요소 표의 「누르면」 열에 쓴다.

**번호 규칙**
- 요소마다 `data-el`에 번호를 붙인다. 화면 안의 큰 덩어리가 `N`, 그 안의 요소가 `N.M`이다. 읽는 순서대로 매긴다. 위에서 아래로, 한 줄 안에서는 왼쪽에서 오른쪽으로 간다.
- 번호는 한 화면 안에서만 겹치지 않으면 된다. UI-1의 2.1과 UI-4의 2.1은 다른 요소다. 요소 번호는 항목이 아니므로 다른 문서는 화면(`UI-4`)까지만 참조한다.
- 배치의 번호와 요소 표 `#` 열의 번호는 똑같다. 한쪽에만 있는 번호는 두지 않는다.
- 번호는 `div`·`span`·`a`·`button` 같은 보통 요소에 붙인다. 입력칸·select·textarea·표에는 뷰가 배지를 그리지 못하므로 감싸는 요소에 붙인다(3.2 · 10.3 · 2.3 · 3.1 · 3.3 · 5.1).
- 반복되는 행(목록 행, 파일 행, 인사이트, 챕터 카드, 스크립트 구간, 대화 턴 등)은 **첫 행에만** 번호를 붙인다. 행 안의 요소도 첫 행에서만 번호를 받는다. 둘째 행부터는 번호 없이 그린다. 진행 중 행의 작은 막대(UI-1 6.7)처럼 일부 행에만 있는 요소는 그것이 처음 나오는 행에서 번호를 받는다.
- 페이지 넷이 같이 쓰는 헤더에는 **번호가 없다.** 배치에는 캔버스의 헤더가 그대로 있고, 정의는 1.1에 한 번 있다. 키 없음 배너(1.4)는 UI-1 배치에만 그리고 거기서 번호(1 · 1.1 · 1.2)를 받는다. UI-3·UI-4 배치에는 배너를 그리지 않는다.
- **상태 보드.** 특정 상태에서만 나타나는 것(배너, 실패 알림, 빈 상태 상자, 대기 상태 등)은 주 보드 아래에 작은 보드로 잇고, 앞에 회색 주석 한 줄로 어떤 상태인지 적는다. 주석은 화면이 아니라 문서의 말이다. 상태 보드에서는 그 상태에서만 나타나는 요소만 번호를 받는다 — 번호는 상태를 가로질러 한 벌이다. 다이얼로그를 잘라 낸 보드는 덮개 색 바탕 위에 그린다.
- 1장 공통 컴포넌트가 들어가는 자리도(헤더와 UI-3·UI-4의 키 없음 배너는 빼고) 그 화면의 번호를 받는다. 요소 표에서는 「공통 1.3 시각 칩」처럼 번호와 이름으로 부른다. 1.8의 버튼 종류는 「공통 1.8의 주 버튼」처럼 부른다.

**구현과의 연결.** 프런트엔드는 이 문서를 그대로 옮긴 것이다(싱크독 개발 규약 DEV-17, `SYNC-STD-004`).
- **화면 항목 하나에 컴포넌트 하나.** 주소가 있는 페이지 넷(UI-1 · UI-3 · UI-4 · UI-5)은 `web/app/` 아래 그 주소에 해당하는 Next.js page 컴포넌트다. 주소가 없는 다이얼로그 셋(UI-2 · UI-6 · UI-7)은 그 다이얼로그를 여는 화면이 불러 쓰는 컴포넌트다. UI-6은 UI-1과 UI-4가 같은 컴포넌트를 쓴다.
- **요소 번호는 코드의 `data-el`이다.** 배치의 번호가 코드에서도 같은 DOM 노드에 그대로 붙는다. 반복 행은 코드에서도 첫 행에만 붙인다.
- 요소마다 컴포넌트를 따로 만들지 않는다. 컴포넌트로 따로 두는 것은 두 화면 이상이 쓰는 1장의 조각뿐이고, 이 조각은 불러 쓰는 화면에서 번호를 받는다(헤더와 UI-3·UI-4의 키 없음 배너는 빼고). 화면 컴포넌트 안에서 1장의 조각을 다시 만들지 않는다.
- 번호 검사(DEV-17)는 번호가 빠짐없이 있는지만 확인한다. 번호가 맞는 요소에 붙었는지, 배치가 캔버스와 같은지는 화면을 띄워 눈으로 확인한다.
- **배치의 글은 자리를 보여 주는 보기 글이다.** 버튼 이름·제목·안내 문장 같은 고정 문구는 요소 표와 규칙에 적힌 것이 기준이다. 영상 제목·채널·파일 이름·시각·금액·개수 같은 예시 값은 제품 문구가 아니다. 실제 값은 [[VA-UI-001]]에서 `{ }`로 표시한 자리에 들어간다.

**배치는 캔버스를 옮긴 것이다.** 모양의 원본은 사용자가 승인한 디자인 캔버스(https://claude.ai/artifact/5vRnv2qFrhTBDjYaNZC1XR)다([[VA-UI-001]] 0장). 캔버스 보드는 디자인 컴포넌트(`.dc.html`)라서 그대로 붙이지 못하고 정적 html로 펼쳐 옮겼다 — `{{자리}}`는 보드의 예시 값으로, 반복과 조건은 그 판의 값으로 채웠고, 보드 사이 링크(`*.dc.html`)는 `#`로 바꿨다. 인라인 스타일은 그대로 두었다 — 바꾼 것은 번호를 붙이려고 입력칸·select·textarea·표를 감싼 요소와, 내용이 보드보다 긴 설정 보드의 높이(`height` → `min-height`)뿐이다. 홈 목록에는 대기 중 행을 맨 위에 더하고 캔버스의 다섯째 행을 뺐다. 어느 보드가 어느 화면·상태인지는 [[VA-UI-001]] 0장 표와 각 화면 메타 표의 「디자인 보드」 행에 있다. 둘이 어긋나면 캔버스가 기준이고 배치를 고친다.

**캔버스에 없는 상태는 이 문서에서 그렸다.** 승인 뒤에 정해진 상태(대기열 · 연결 확인 못함)와 처음부터 보드가 없던 상태(입력 오류 · 빈 inbox · 시작 불가 · 답 대기와 실패 · 키 없는 질문 · 짧은 알림 · 키 카드 · 삭제와 내보내기 실패)다. 캔버스의 부품과 [[VA-UI-001]] 3장의 색만 써서 그렸고, 상태 보드 주석에 「캔버스에 없음」으로 표시했다. 모양은 디자인 보강 때 사용자 검토를 받아 캔버스에 보드로 더한다([[VA-UI-001]] 8장, 2장 미결).

---

## 1. 공통 컴포넌트

여러 화면이 같이 쓰는 조각을 여기서 한 번 정의한다. 화면 절에서는 번호와 이름으로만 부른다. 모양과 값의 원본은 [[VA-UI-001]] 4장이고, 이 장에는 쓰는 곳과 동작만 적는다. 화면 안의 자리와 요소 번호는 각 화면 절에서 정한다.

### 1.1 헤더

모든 페이지 맨 위에 있는 한 줄이다. 왼쪽에 로고, 오른쪽에 주 메뉴가 있다.

- 쓰는 곳: 페이지 넷(UI-1 · UI-3 · UI-4 · UI-5). 다이얼로그(UI-2 · UI-6 · UI-7)에는 자기 헤더가 없고, 뒤 페이지의 헤더가 덮개 아래에 그대로 남는다.
- 로고(타일 + 'Video Agent')는 UI-1로 가는 링크다.
- 주 메뉴(`nav`, aria-label '주 메뉴')에는 글자 메뉴 '분석한 영상'(→ UI-1)과 설정 아이콘(aria-label '설정', → UI-5)이 있다. 둘 다 화면을 옮기므로 링크다([[VA-UI-001]] 4.6). 로그인·계정 메뉴는 없다.
- 현재 위치 표시: UI-1은 '분석한 영상', UI-5는 설정 아이콘이다. UI-3·UI-4에는 표시하지 않는다. 표시하는 메뉴에는 바탕색과 `aria-current="page"`를 함께 준다. 보드는 UI-5에만 `aria-current`를 그렸지만 UI-1에도 붙인다.
- 창을 스크롤해도 헤더는 위에 남고, 그 아래 내용만 움직인다.
- 키 없음 배너(1.4)가 뜨면 헤더 바로 위에 붙는다.
- 헤더에는 번호가 없다. 배치에는 캔버스의 헤더가 그대로 있다.

### 1.2 다이얼로그 틀

뒤 페이지를 덮개로 덮고 그 위에 뜨는 흰 카드다. 가로로는 가운데, 세로로는 위쪽에 붙는다.

- 쓰는 곳: UI-2 사전 안내 · UI-6 삭제 확인 · UI-7 내보내기. 다이얼로그 위에 다른 다이얼로그가 뜨는 경우는 없다.
- 역할: UI-2·UI-7은 `role="dialog"`다. UI-6은 되돌릴 수 없는 동작을 묻기 때문에 `role="alertdialog"`다. 셋 다 `aria-modal="true"`이고, 제목을 `aria-labelledby`로 연결한다.
- 머리: UI-2·UI-7에는 제목과 부제가 있고, 오른쪽에 닫기(X, aria-label '닫기')가 있다. UI-6에는 닫기 대신 왼쪽 위에 빨간 톤 휴지통 타일이 있다. 제목 아래에는 지울 영상 제목이 오고, 이것을 `aria-describedby`로 연결한다.
- 닫는 방법: UI-2·UI-7에서는 닫기(X), Esc, 덮개 누름이 모두 [취소]와 같다. UI-6에는 닫기(X)가 없다. Esc만 [취소]와 같고, 덮개를 눌러도 닫히지 않는다.
- 처음 초점: UI-2는 [분석 시작](시작 불가 판에서는 [닫기]), UI-6은 [취소], UI-7은 고른 방법 칸이다. 열려 있는 동안 초점은 다이얼로그 밖으로 나가지 않는다. 닫히면 초점이 다이얼로그를 연 버튼으로 돌아간다.
- 버튼 줄: 맨 아래에 오른쪽으로 정렬한다. [취소](보조 버튼)가 왼쪽, 확인 동작이 오른쪽 끝에 온다. 확인 동작은 주 버튼이고, UI-6만 위험 버튼이다. UI-2 시작 불가 판에는 [닫기]만 있다.
- 다이얼로그는 주소를 바꾸지 않는다. 새로 고치면 다이얼로그가 닫히고 뒤 페이지만 열린다.

### 1.3 시각 칩

영상 속 한 시각을 담은 작은 칩이다. 누르면 오른쪽 패널의 스크립트가 그 시각으로 이동한다.

- 쓰는 곳: UI-4에만 있다. 인사이트 문장 끝과 답변의 '근거' 뒤에서는 칩 하나하나가 `button`이다(aria-label '{시각} 위치의 스크립트로 이동'). 챕터 카드의 시작 시각은 모양만 같고, 누르는 대상은 카드 전체다. 스크립트 구간에는 칩이 없고 줄 전체가 버튼이다.
- 표기 형식은 영상 길이에 따라 정한다. 1시간 미만 영상은 `mm:ss`(12:40), 1시간 이상 영상은 `h:mm:ss`(0:06:20)다. 한 영상 안의 시각은 모두 같은 형식을 쓰고, 영상 길이 표기도 같은 규칙을 따른다.
- 인사이트 칩, 챕터 카드, 근거 칩, 스크립트 구간 중 어느 것을 눌러도 똑같이 동작한다.
  1. 오른쪽 패널이 [스크립트] 탭으로 바뀐다.
  2. 그 시각이 들어 있는 스크립트 구간이 노란 바탕으로 강조되고, 패널이 그 구간까지 스크롤된다.
  3. 시작 시각이 같은 챕터 카드가 선택 모양(흰 바탕 + 청록 테두리)으로 바뀐다.
  4. 스크립트 머리줄 오른쪽의 시각이 그 시각으로 바뀐다.
- 선택은 한 번에 하나만 된다. 다른 시각을 누르면 앞의 선택이 풀린다. 모두 애니메이션 없이 바로 바뀐다([[VA-UI-001]] 3.4).
- 결과 화면의 시각을 눌러도 YouTube로 가지 않는다. `?t=` 링크는 내보낸 마크다운(UI-7)에만 생긴다.
- 누를 수 없는 시각·길이는 칩이 아니다. UI-1 목록·inbox 행의 길이와 UI-3 단계 메모는 고정폭 글자이고, UI-2·UI-4 메타 칩 안의 길이와 UI-3 부제·영상 머리의 길이·조각 수는 일반 UI 글자다([[VA-UI-001]] 4.4).

### 1.4 키 없음 배너

OpenAI API 키가 없거나 키 확인에 실패했을 때 헤더 위에 전체 폭으로 뜨는 빨간 톤 줄이다.

- 쓰는 곳: UI-1 · UI-3 · UI-4. UI-5는 키를 넣는 화면이므로 배너를 두지 않는다.
- `role="status"`다. 느낌표 원 아이콘, 문장 한 줄, 오른쪽의 배너 버튼 [키 넣으러 가기](→ UI-5)로 이루어진다.
- 문장: 키가 없으면 'OpenAI API 키가 없어서 아직 분석할 수 없어요. 분석해 둔 영상은 키 없이도 읽을 수 있습니다.'를 쓴다. 키 확인에 실패하면(형식 오류 · 인증 실패 · 잔액 없음) '키를 확인하지 못했어요 — {이유}'를 쓴다. 인터넷이 없어 확인하지 못했으면 '연결을 확인하지 못했어요 — 인터넷이 되면 분석 버튼을 누를 때 다시 확인합니다'를 쓰고 [키 넣으러 가기]를 보이지 않는다 — 키가 틀린 것이 아니라 설정에서 고칠 것이 없다(VA-UI-001 7장 17). 세 경우 모두 같은 배너다.
- 키는 앱이 시작할 때와 분석 버튼을 누를 때 확인한다. 배너가 떠 있는 동안 UI-1의 두 분석 버튼과 UI-3 다시 시도는 막힌 주 버튼(1.8)이 되고, UI-4 질문 입력과 추천 질문 전송도 막힌다(연결 문구일 때는 막지 않는다 — 아래). 이미 분석한 영상은 그대로 열어서 읽을 수 있다.
- UI-5에서 키 확인을 통과하면 배너가 사라진다.
- 배너 자체는 누를 수 없고, 누를 수 있는 것은 [키 넣으러 가기]뿐이다. 연결 문구일 때는 누를 수 있는 것이 없다.
- 연결 문구일 때는 아무것도 막지 않는다. 분석 버튼·다시 시도·질문 보내기를 누르면 서버가 그때 키를 다시 확인한다 — 통과하면 배너가 사라지고 하려던 일이 이어지고, 아직 안 되면 배너는 그대로이고 그 화면의 실패 자리에 '연결을 확인하지 못했어요'를 알린다. 막힌 버튼은 눌러도 요청을 보내지 않으므로 문구의 「누를 때 다시 확인」과 맞지 않기 때문이다 (VA-UI-001에 없음, 2장)
- 번호: UI-1은 배너(1)·문구(1.1)·[키 넣으러 가기](1.2)에 번호를 준다. UI-3·UI-4 배치에는 배너를 그리지 않았고, 코드에서도 data-el을 붙이지 않는다. 세 문구의 모습은 UI-1 배치의 「첫 실행」·「키 확인 실패」·「연결을 확인하지 못함」 보드에 있다.

### 1.5 짧은 알림

잠깐 보였다가 저절로 사라지는 한 줄 알림이다. 누를 것이 없다.

- 쓰는 곳은 UI-4의 두 경우다. UI-1에서 이미 분석한 영상을 다시 넣어 UI-4가 열리면 '이미 분석한 영상입니다'를 띄운다. UI-7 주 버튼으로 내보내기(파일로 저장 · 복사하기)가 끝나면 완료를 알린다.
- **끝난 일을 알릴 때만 쓴다.** 확인을 받거나 실패를 알릴 때는 쓰지 않는다. 확인은 다이얼로그(1.2)로 받고, 실패는 실패 알림(1.6)이나 문제가 생긴 자리의 한 줄로 알린다.
- 화면이 바뀌면서 알리는 경우에는 새로 열린 화면에서 보인다. UI-7의 완료 알림은 다이얼로그가 닫힌 뒤 UI-4 위에 뜬다.
- 스크린 리더가 읽을 수 있게 `role="status"`로 둔다. 초점은 옮기지 않는다.
- 위치와 보이는 시간은 캔버스에 없다. 모양은 UI-4 배치의 「짧은 알림」 보드(11)에 캔버스 부품으로 그렸고 디자인 보강 때 확정한다([[VA-UI-001]] 8장). 위치, 보이는 시간, 여러 알림이 겹칠 때의 처리는 2장 미결사항이다.
- 위 두 경우 말고 다른 곳에서 쓰려면 [[VA-UI-001]] 4.5 표에 먼저 추가한다.

### 1.6 실패 알림

분석 단계가 실패했을 때 진행 카드 안, 단계 목록 아래에 뜨는 빨간 톤 상자다.

- 쓰는 곳: UI-3 실패 상태. 어느 단계(자막 가져오기·음성 내려받기·음성 추출·받아쓰기·핵심 요약·챕터·추천 질문)가 실패하든 같은 상자를 쓴다.
- `role="alert"`다. 왼쪽에 느낌표 원 아이콘, 오른쪽에 제목과 본문이 있다. 아래 오른쪽에는 [목록으로](보조 버튼, → UI-1)와 다시 시도(주 버튼, 새로고침 아이콘) 두 버튼이 있다.
- 제목에는 **무엇이** 안 됐는지 쓴다(예: 'OpenAI API에 연결하지 못했어요'). 본문에는 **어느 단계·조각에서, 왜** 실패했는지(몇 번 다시 보냈는지 포함)와 **무엇이 남았는지**를 쓴다. 할 수 있는 동작은 버튼으로 붙인다([[VA-UI-001]] 4.5 문구 규칙).
- 다시 시도 버튼 글자는 받아쓰기 실패면 '{r}번째 조각부터 다시 시도', 다른 단계 실패면 '{단계}부터 다시 시도'다. {r}은 아직 완료하지 않은 첫 조각 번호다. 조각은 동시에 보내므로 실패한 조각 번호 {k}와 다를 수 있다.
- 다시 시도는 같은 작업을 이어서 진행한다. 누르면 같은 화면이 진행 상태로 돌아가고 상자가 사라진다. 키가 없거나 키 확인에 실패한 동안에는 막힌 주 버튼(1.8)이고 누르면 UI-5로 간다.
- 다른 실패에도 같은 문구 규칙을 쓴다: UI-1 주소 형식 오류, UI-2 시작 불가, UI-4 답변 실패, UI-5 키 확인 실패, UI-6 삭제 실패, UI-7 저장·복사 실패. 다만 이런 실패는 이 상자가 아니라 문제가 생긴 자리에 한 줄로 보이고, 각 화면 절에서 그린다.

### 1.7 빈 상태 상자

목록이 비었을 때 목록 자리에 두는 점선 상자다. 제목 한 줄과 본문 한 문단으로 되어 있고, 누를 것이 없다.

- 쓰는 곳은 두 곳이다. UI-1 「분석한 영상」이 0개일 때와 UI-4 [질문하기] 대화 목록에 질문 턴이 하나도 없을 때다(답 대기·답변 실패 턴도 턴으로 센다).
- UI-1: 가운데 정렬이다. 제목은 '아직 분석한 영상이 없어요'다. 본문은 키가 있는지에 따라 다르다. 키가 없으면 '설정에서 OpenAI API 키를 넣은 뒤, 위에 링크를 붙여 넣거나 inbox 폴더에 파일을 넣어 보세요.'를 쓴다. 키가 있으면 키 문장을 빼고, 링크를 붙여 넣거나 inbox에 파일을 넣으라는 안내만 남긴다. 목록 머리의 '0개'는 그대로 보인다.
- UI-1 상자를 보일지는 키와 상관없이 목록만 보고 정한다. 키가 없어도 분석한 영상이 있으면 상자 대신 목록 행이 보인다.
- UI-4: 왼쪽 정렬이다. 제목은 '아직 질문이 없어요', 본문은 '아래 추천 질문을 누르거나 직접 물어보세요. 답에는 근거가 된 시각이 함께 붙습니다.'다. 아래 입력 영역(추천 칩 줄 · 입력칸 · [보내기])은 그대로 있다.
- 상자 안에는 버튼을 두지 않는다. 다음에 할 동작은 이미 상자 주변에 있다. UI-1은 위쪽의 입력 카드 둘, UI-4는 아래쪽의 입력 영역이다.
- UI-4에서 첫 질문을 보내면 상자가 사라지고 그 자리에 대화 목록이 나온다.

### 1.8 버튼과 추천 질문

버튼의 종류와 추천 질문의 두 가지 모양을 정한다. 모양은 [[VA-UI-001]] 4.2 표를 따른다.

- **화면을 옮기면 링크, 동작을 하면 버튼이다.** 보드가 `a`로 그린 버튼([분석 시작] [저장] 등)도 코드에서는 `button`으로 만든다. 뒤로 링크 '← 분석한 영상', '원본 영상 열기', 헤더 설정 아이콘은 링크다.
- 종류:
  - **주 버튼**: 그 영역의 확인 동작. [분석] [선택한 파일 분석] [분석 시작] [저장] [파일로 저장]·[복사하기], 다시 시도
  - **보조 버튼**: [취소] [목록으로] [내보내기] [확인하고 저장]
  - **위험 버튼**: UI-6 [삭제] 하나
  - **배너 버튼**: [키 넣으러 가기]
  - **아이콘 버튼**: 다이얼로그 닫기, 목록 행 휴지통, 헤더 설정(모양만 아이콘 버튼)
  - **테두리 아이콘 버튼**: UI-4 머리 휴지통
  - **보내기 버튼**: UI-4 질문 입력
- 아이콘만 있는 버튼에는 aria-label을 붙인다: '설정' · '닫기' · '보내기' · '분석 결과 삭제' · '{제목} 분석 결과 삭제'.
- **막힌 주 버튼**은 키가 없거나 키 확인에 실패했을 때 UI-1의 [분석]·[선택한 파일 분석]과 UI-3 다시 시도에 쓴다. 회색이고 `aria-disabled="true"`지만 초점은 받는다. 누르면 UI-5로 간다. 막다른 길이 되지 않도록 `disabled`는 쓰지 않는다.
- 키가 있고 inbox 폴더가 비었을 때 UI-1 [선택한 파일 분석]도 막힌 주 버튼 모양에 aria-disabled="true"로 두지만, 누르면 아무것도 보내지 않고 화면도 바뀌지 않는다. 이때는 UI-5로 가지 않는다(UI-1 규칙).
- 기다리는 동안: 서버가 영상 정보를 확인하는 동안 [분석]·[선택한 파일 분석]에 대기 표시를 한다. 답을 기다리는 동안에는 입력칸과 [보내기]를 잠근다.
- **추천 질문은 같은 3개가 두 가지 모양으로 나온다.** 큰 알약은 UI-4 본문 「이런 걸 물어볼 수 있어요」에 말풍선 아이콘과 함께 놓이고, 줄바꿈된다. 작은 칩은 [질문하기] 입력칸 위에 한 줄로 놓이고, 줄바꿈 없이 넘치는 부분은 잘린다.
- 어느 모양이든 누르면 오른쪽 패널이 [질문하기] 탭으로 바뀌고 그 문장이 바로 질문으로 전송된다. 입력칸에 그 문장을 쳐서 [보내기]를 누른 것과 같다. 답을 기다리는 동안이나 키가 없을 때는 두 모양 모두 문장을 보내지 않는다. 큰 알약은 탭만 바꾼다.

---

## 2. 미결사항

와이어프레임 단계에서 정해야 하지만 배치만으로는 정할 수 없는 것들이다. 제품 수준의 미결(상위 문서 갱신 요청·사용자 결정·디자인 보강)은 [[VA-UI-001]] 8장에 있다.

- [ ] 시각을 눌렀을 때의 스크롤 위치: 고른 스크립트 구간을 패널 맨 위에 둘지 가운데에 둘지, 이미 보이는 구간이면 스크롤하지 않을지(1.3)
- [ ] 챕터 강조 기준: 인사이트·근거 시각이 어느 챕터의 시작 시각과도 같지 않으면, 지금 규칙으로는 어떤 챕터도 강조되지 않는다. 그 시각이 들어 있는 챕터를 강조할지, 그 챕터가 접힌 파트 안에 있으면 파트를 펼칠지(1.3). 정할 때까지는 UI-4 규칙대로 강조하지 않고 파트도 펴지 않는다
- [ ] 시각 선택을 주소에 남길지: 새로 고치거나 다른 화면에 다녀오면 선택이 풀리는지, 남긴다면 주소 형식은 무엇인지
- [ ] 탭을 오갈 때의 스크롤 위치: 근거 칩을 눌러 [스크립트]로 갔다가 [질문하기]로 돌아왔을 때 읽던 대화 위치를 유지할지
- [ ] 초점을 돌려줄 버튼이 없어지는 경우: UI-2 [분석 시작]으로 UI-3이 열릴 때와 UI-4에서 연 UI-6 [삭제]로 UI-1이 열릴 때 초점을 어디에 둘지(1.2). UI-1에서 연 UI-6 [삭제]는 UI-1 규칙으로 정했다
- [ ] 짧은 알림의 보이는 시간과 겹침: 몇 초 동안 보일지, 두 알림이 잇달아 뜨면 앞의 것을 바꿀지 쌓을지, 마우스를 올리면 멈출지(1.5)
- [x] 내보내기가 실패할 때: 파일 쓰기가 실패하거나 브라우저가 클립보드 접근을 막는 경우다. 짧은 알림은 실패에 쓰지 않으므로, UI-7을 닫지 않고 그 안에 이유를 보일지(1.5 · 1.6) — 결정: UI-7을 닫지 않고 그 안의 실패 한 줄(5.1)에 이유를 보이고 잠금을 푼다(UI-7 규칙)
- [x] 키가 없을 때의 추천 질문과 다시 시도: 추천 질문(1.8)을 누르면 탭만 바꾸고 입력칸의 키 없음 안내를 보일지, 막힌 분석 버튼처럼 UI-5로 보낼지. UI-3 실패 알림의 다시 시도(1.6)도 OpenAI로 요청을 보내므로 함께 막을지 — 결정: 추천 질문은 보내지 않고 큰 알약은 탭만 바꾼다(UI-4 규칙). UI-3 다시 시도(5.4)는 막힌 주 버튼이고 누르면 UI-5로 간다(UI-3 규칙)
- [x] 다른 영상이 분석 중일 때의 [분석 시작] — 결정: 대기열(VA-UI-001 7장 16). UI-1 대기 중 행 · UI-2 대기 안내(6.1) · UI-3 대기 상태로 그렸다
- [x] 인터넷이 없어 키를 확인하지 못했을 때 — 결정: 배너 문구를 가르고 [키 넣으러 가기]를 뺀다(VA-UI-001 7장 17). 공통 1.4 · UI-1 · UI-3 · UI-4 10.2에 넣었다
- [x] UI-5 2.2 저장 위치 캡션 — 결정: '.env에 저장됨' 고정([[VA-INFRA-001#C6]])
- [x] (반영: 화면 설계 v6 UI-1 규칙 · 설정 서비스 MINISPEC v2 `require_key`) **되먹임** 연결 문구일 때는 버튼을 막지 않는다(1.4) — [[VA-UI-001]] UI-1 규칙은 확인 실패를 한데 묶어 「분석 버튼과 질문 입력을 막는다」고 쓴다. 연결 실패만 막지 않는다는 한 문장이 필요하다. MINISPEC(설정 서비스)의 「마지막 결과로 막기」도 마지막 결과가 연결 실패면 그때 한 번 다시 확인해야 다시 시도와 질문에서도 풀린다 — 지금은 분석 버튼(영상 등록)만 다시 확인한다
- [ ] 대기 상태의 모양 — 캔버스에 없다. UI-1 대기 중 행의 글자색, UI-3 대기 상태 카드는 정상 상태의 색을 그대로 써서 배치에 그렸다. 디자인 보강 때 같이 본다
- [ ] 캔버스에 없는 상태 보드의 검토 — 0장 「캔버스에 없는 상태는 이 문서에서 그렸다」의 보드들(UI-1 넷 · UI-2 둘 · UI-3 하나 · UI-4 다섯 · UI-5 둘 · UI-6 하나 · UI-7 하나, 대기 중 행 포함). 사용자가 보고 확정하면 캔버스에 보드로 더한다([[VA-UI-001]] 8장 디자인 보강)
- [x] 배치를 싱크독 새 뷰에 맞춘다(2026-09-23) — 싱크독이 배치 html을 iframe에 격리해 그대로 그리게 되면서(카드 Z · AC · AE) 뷰가 주던 클래스 사전이 없어졌다. 클래스로 그린 뼈대가 스타일 없이 보여, 배치를 승인된 캔버스 html로 옮기고 「3. 공통 틀」을 더했다. 요소 번호와 요소 표·규칙·시나리오는 그대로다
- [ ] 이미 보낸 추천 질문: 두 모양에서 뺄지, 그대로 두고 다시 누르면 같은 질문을 또 보내게 할지(1.8)
- [x] UI-5 「키 없음」 상태 보드의 2.1 배지 색 — 보드는 칩 면(회색)으로 그렸는데 UI-5 규칙과 [[VA-UI-001]] 3.1 색 언어(빨강은 키 없음에)는 위험 톤이다. 결정: 규칙대로 위험 톤으로 보드를 고쳤다(카드 A 구현에서 찾음, 2026-09-23)

---

## 3. 공통 틀

이 절의 첫 html 블록은 뷰가 **이 문서 모든 화면의 배치 앞에** 넣는다([[VA-UI-001]] 4장의 앱 셸과 다르다 — 이것은 문서를 그리는 틀이다). 마크업은 없고 글꼴 `<link>`와 `<style>`뿐이다. 글꼴과 `body` 규칙은 캔버스 보드의 `<helmet>`을 그대로 옮겼고, 값의 원본은 [[VA-UI-001]] 3장이다. 뒤의 네 규칙은 문서의 것이다 — 상태 보드 앞 주석 줄(`.var`), 잘라 낸 작은 보드(`.crop`, 다이얼로그면 덮개 색 `.dim`), 작은 보드를 나란히 두는 줄(`.row`). `body` 바탕만 캔버스와 달리 한 단계 어둡게 했다 — 보드 사이 경계가 보이게.

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hahmlet:wght@500;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap">
<style>
/* 공통 틀 — 캔버스 보드의 <helmet> 그대로(값의 원본은 VA-UI-001 3장). body 바탕만 보드 경계가 보이게 한 단계 어둡게 */
body { margin: 0; background: #E4E0D7; color: #1B1A17; font-family: 'IBM Plex Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; word-break: keep-all; -webkit-font-smoothing: antialiased; }
a { color: #0F6E68; }
a:hover { color: #0B5752; }
button, input, select, textarea { font-family: inherit; }
@keyframes va-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.va-pulse { animation: va-pulse 1.4s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) { .va-pulse { animation: none; } }
/* 문서의 말 — 상태 보드 앞 주석 줄. 화면이 아니다 */
.var { box-sizing: border-box; width: 1440px; padding: 32px 4px 10px; font: 500 13px/1.5 'IBM Plex Mono', monospace; color: #5E5A52; }
.var b { color: #1B1A17; font-weight: 600; }
/* 잘라 낸 작은 보드 — 페이지 바탕 위에. 다이얼로그는 덮개 색(#F6F4EF 위 rgba(27,26,23,.52)) 위에 */
.crop { box-sizing: border-box; width: fit-content; padding: 24px; background: #F6F4EF; }
.crop.dim { padding: 40px; background: #84817D; }
/* 작은 보드를 나란히 */
.row { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 0 40px; width: 1440px; }
</style>
```

---

## UI-1 홈

| 항목 | 내용 |
|---|---|
| 화면 설계 | [[VA-UI-001#UI-1]] |
| 경로 | `/` |
| 디자인 보드 | Main · FirstRun |
| 진입 | 앱 시작 · 헤더 로고와 '분석한 영상' · UI-3/UI-4 '← 분석한 영상' · UI-3 [목록으로] · UI-2 [취소]/닫기 · UI-5 [취소]/[저장] · UI-6 [삭제]/[취소] |
| 유스케이스 | [[VA-UC-001#UC-H1]] 기본 흐름 1~2, 확장 1a·2a·2b · [[VA-UC-001#UC-H2]] 기본 흐름 1~2, 확장 1a·2a · [[VA-UC-001#UC-H0]] 확장 2a·2b·3a · [[VA-UC-001#UC-H5]] 기본 흐름 1~2, 확장 1a·1b · [[VA-UC-001#UC-H6]] 기본 흐름 1·4, 확장 3a · [[VA-UC-001#UC-H8]] 트리거·최소 보장, 확장 3a · [[VA-UC-001#UC-S5]] 기본 흐름 1, 확장 1a·1b · [[VA-UC-001#UC-S6]] 기본 흐름 1~2 |

### 배치

```html
<!-- 주 보드: 캔버스 Main. 목록 맨 위에 대기 중 행 하나를 더했다(캔버스에 없음). 아래는 상태 보드 -->
<div style="width: 1440px; height: 960px; box-sizing: border-box; background: #F6F4EF; display: flex; flex-direction: column; overflow: hidden;">
<header style="height: 64px; flex-shrink: 0; box-sizing: border-box; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2DDD3; background: #F6F4EF;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 10px; color: #1B1A17; text-decoration: none;">
<span style="width: 30px; height: 30px; border-radius: 8px; background: #1B1A17; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="#F6F4EF" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;">Video Agent</span>
</a>
<nav aria-label="주 메뉴" style="display: flex; align-items: center; gap: 4px;">
<a href="#" aria-current="page" style="height: 44px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; border-radius: 10px; background: #EAE6DD; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">분석한 영상</a>
<a href="#" aria-label="설정" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 7h-9"></path><path d="M14 17H5"></path><circle cx="17" cy="17" r="3"></circle><circle cx="7" cy="7" r="3"></circle></svg>
</a>
</nav>
</header>
<main style="flex-grow: 1; min-height: 0; box-sizing: border-box; padding: 44px 160px 0; display: flex; flex-direction: column; gap: 44px;">
<section aria-labelledby="home-title" style="display: flex; flex-direction: column; gap: 24px;">
<div data-el="2" style="display: flex; flex-direction: column; gap: 8px;">
<h1 id="home-title" data-el="2.1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 40px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em;">어떤 영상을 읽어 볼까요?</h1>
<p data-el="2.2" style="margin: 0; font-size: 16px; line-height: 1.6; color: #5E5A52;">YouTube 링크를 붙여 넣거나 inbox 폴더의 파일을 고르세요. 분석 결과는 이 PC에만 저장됩니다.</p>
</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px;">
<div data-el="3" style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<div data-el="3.1" style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #E1EFEC; color: #0F6E68; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">YouTube 링크</span>
<span style="font-size: 13px; color: #6B665C;">watch · youtu.be · shorts 주소를 받아요</span>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="yt-url" style="font-size: 14px; font-weight: 600; color: #4A463F;">영상 주소</label>
<div style="display: flex; gap: 10px;">
<span data-el="3.2" style="flex-grow: 1; min-width: 0; display: flex;"><input id="yt-url" type="url" placeholder="https://www.youtube.com/watch?v=…" value="" style="width: 100%; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FBFAF7; color: #1B1A17; font-size: 15px;"></span>
<a data-el="3.3" href="#" aria-disabled="false" style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">분석</a>
</div>
</div>
<p data-el="3.5" style="margin: 0; font-size: 13px; line-height: 1.55; color: #6B665C;">자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.</p>
</div>
<div data-el="4" style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 14px;">
<div data-el="4.1" style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">내 파일</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #6B665C;">~/video-agent/inbox</span>
</div>
</div>
<div role="group" aria-label="inbox 파일" data-el="4.2" style="display: flex; flex-direction: column; gap: 6px;">
<button type="button" data-el="4.3" aria-pressed="true" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #0F6E68; background: #E1EFEC; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: #0F6E68;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">workshop_0912.mp4</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">2:30:00</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">1.8 GB</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #E2DDD3; background: #FBFAF7; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: transparent;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">meetup_0901.mp4</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">1:58:20</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">1.4 GB</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #E2DDD3; background: #FBFAF7; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: transparent;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">interview_0903.m4a</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">1:04:12</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">58 MB</span>
</button>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
<span data-el="4.5" style="font-size: 13px; color: #6B665C;">mp4 · mkv · mov · webm · mp3 · m4a · wav</span>
<a data-el="4.6" href="#" aria-disabled="false" style="height: 44px; flex-shrink: 0; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">선택한 파일 분석</a>
</div>
</div>
</div>
</section>
<section aria-labelledby="list-title" style="display: flex; flex-direction: column; gap: 12px;">
<div data-el="5" style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="list-title" data-el="5.1" tabindex="-1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">분석한 영상</h2>
<span data-el="5.2" style="font-size: 14px; color: #6B665C;">5개</span>
</div>
<span data-el="5.3" style="font-size: 13px; color: #6B665C;">최근 순</span>
</div>
<div data-el="6" style="border-top: 1px solid #E2DDD3; display: flex; flex-direction: column;">
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a data-el="6.1" href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span data-el="6.2" style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span data-el="6.3" style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">벡터 검색 튜닝 실전</span>
<span data-el="6.4" style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span data-el="6.5" style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">38:05</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span data-el="6.6" style="font-size: 14px; font-weight: 600; color: #6B665C;">대기 중 · 1번째</span>
</span>
</a>
<a data-el="6.8" href="#" aria-label="벡터 검색 튜닝 실전 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</span>
<span style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">50:12</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 400; color: #6B665C;">오늘 14:08 분석</span>
</span>
</a>
<a href="#" aria-label="RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">workshop_0912.mp4</span>
<span style="font-size: 13px; color: #6B665C;">로컬 파일</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">2:30:00</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 600; color: #0F6E68;">받아쓰기 중 · 12 / 30</span>
<span data-el="6.7" style="width: 160px; height: 4px; border-radius: 2px; background: #E2DDD3; display: block; overflow: hidden;">
<span style="width: 40%; height: 4px; display: block; background: #0F6E68;"></span>
</span>
</span>
</a>
<a href="#" aria-label="workshop_0912.mp4 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">meetup_0901.mp4</span>
<span style="font-size: 13px; color: #6B665C;">로컬 파일</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">1:58:20</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 600; color: #A33A2B;">받아쓰기 16 / 24에서 멈춤</span>
</span>
</a>
<a href="#" aria-label="meetup_0901.mp4 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">LLM 에이전트 설계 패턴 정리</span>
<span style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">1:12:40</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 400; color: #6B665C;">9월 12일 분석</span>
</span>
</a>
<a href="#" aria-label="LLM 에이전트 설계 패턴 정리 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
</div>
</section>
</main>
</div>
<div class="var"><b>첫 실행</b> — 키가 없고 분석한 영상이 없을 때. 키 없음 배너(1)와 빈 상태 상자(7), 막힌 분석 버튼 · 캔버스 FirstRun 보드</div>
<div style="width: 1440px; height: 960px; box-sizing: border-box; background: #F6F4EF; display: flex; flex-direction: column; overflow: hidden;">
<div role="status" data-el="1" style="min-height: 56px; flex-shrink: 0; box-sizing: border-box; padding: 8px 40px; display: flex; align-items: center; gap: 12px; background: #F7E6E2; color: #7A2A1E; font-size: 15px;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4"></path><path d="M12 16h.01"></path></svg>
<span data-el="1.1" style="flex-grow: 1;">OpenAI API 키가 없어서 아직 분석할 수 없어요. 분석해 둔 영상은 키 없이도 읽을 수 있습니다.</span>
<a data-el="1.2" href="#" style="height: 40px; box-sizing: border-box; padding: 0 16px; display: flex; align-items: center; border-radius: 8px; background: #7A2A1E; color: #FFFFFF; font-size: 14px; font-weight: 600; text-decoration: none;">키 넣으러 가기</a>
</div>
<header style="height: 64px; flex-shrink: 0; box-sizing: border-box; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2DDD3; background: #F6F4EF;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 10px; color: #1B1A17; text-decoration: none;">
<span style="width: 30px; height: 30px; border-radius: 8px; background: #1B1A17; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="#F6F4EF" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;">Video Agent</span>
</a>
<nav aria-label="주 메뉴" style="display: flex; align-items: center; gap: 4px;">
<a href="#" aria-current="page" style="height: 44px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; border-radius: 10px; background: #EAE6DD; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">분석한 영상</a>
<a href="#" aria-label="설정" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 7h-9"></path><path d="M14 17H5"></path><circle cx="17" cy="17" r="3"></circle><circle cx="7" cy="7" r="3"></circle></svg>
</a>
</nav>
</header>
<main style="flex-grow: 1; min-height: 0; box-sizing: border-box; padding: 44px 160px 0; display: flex; flex-direction: column; gap: 44px;">
<section aria-labelledby="home-title" style="display: flex; flex-direction: column; gap: 24px;">
<div style="display: flex; flex-direction: column; gap: 8px;">
<h1 id="home-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 40px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em;">어떤 영상을 읽어 볼까요?</h1>
<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #5E5A52;">YouTube 링크를 붙여 넣거나 inbox 폴더의 파일을 고르세요. 분석 결과는 이 PC에만 저장됩니다.</p>
</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px;">
<div style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #E1EFEC; color: #0F6E68; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">YouTube 링크</span>
<span style="font-size: 13px; color: #6B665C;">watch · youtu.be · shorts 주소를 받아요</span>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="yt-url" style="font-size: 14px; font-weight: 600; color: #4A463F;">영상 주소</label>
<div style="display: flex; gap: 10px;">
<span style="flex-grow: 1; min-width: 0; display: flex;"><input id="yt-url" type="url" placeholder="https://www.youtube.com/watch?v=…" value="" style="width: 100%; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FBFAF7; color: #1B1A17; font-size: 15px;"></span>
<a href="#" aria-disabled="true" style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #E2DDD3; color: #5E5A52; font-size: 15px; font-weight: 600; text-decoration: none;">분석</a>
</div>
</div>
<p style="margin: 0; font-size: 13px; line-height: 1.55; color: #6B665C;">자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.</p>
</div>
<div style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">내 파일</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #6B665C;">~/video-agent/inbox</span>
</div>
</div>
<div role="group" aria-label="inbox 파일" style="display: flex; flex-direction: column; gap: 6px;">
<button type="button" aria-pressed="true" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #0F6E68; background: #E1EFEC; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: #0F6E68;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">workshop_0912.mp4</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">2:30:00</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">1.8 GB</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #E2DDD3; background: #FBFAF7; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: transparent;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">meetup_0901.mp4</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">1:58:20</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">1.4 GB</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #E2DDD3; background: #FBFAF7; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: transparent;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">interview_0903.m4a</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">1:04:12</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">58 MB</span>
</button>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
<span style="font-size: 13px; color: #6B665C;">mp4 · mkv · mov · webm · mp3 · m4a · wav</span>
<a href="#" aria-disabled="true" style="height: 44px; flex-shrink: 0; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; background: #E2DDD3; color: #5E5A52; font-size: 15px; font-weight: 600; text-decoration: none;">선택한 파일 분석</a>
</div>
</div>
</div>
</section>
<section aria-labelledby="list-title" style="display: flex; flex-direction: column; gap: 12px;">
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="list-title" tabindex="-1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">분석한 영상</h2>
<span style="font-size: 14px; color: #6B665C;">0개</span>
</div>
<span style="font-size: 13px; color: #6B665C;">최근 순</span>
</div>
<div data-el="7" style="box-sizing: border-box; padding: 40px; border-radius: 16px; border: 1px dashed #CFC8BB; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center;">
<span data-el="7.1" style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600;">아직 분석한 영상이 없어요</span>
<span data-el="7.2" style="font-size: 15px; line-height: 1.6; color: #5E5A52;">설정에서 OpenAI API 키를 넣은 뒤, 위에 링크를 붙여 넣거나 inbox 폴더에 파일을 넣어 보세요.</span>
</div>
</section>
</main>
</div>
<div class="var"><b>키 확인 실패</b> — 키는 있는데 확인에 실패했을 때 배너 문구. 분석 버튼은 막힌다 · 캔버스에 없음</div>
<div class="crop" style="width: 1440px; padding: 0;">
<div role="status" style="min-height: 56px; flex-shrink: 0; box-sizing: border-box; padding: 8px 40px; display: flex; align-items: center; gap: 12px; background: #F7E6E2; color: #7A2A1E; font-size: 15px;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4"></path><path d="M12 16h.01"></path></svg>
<span style="flex-grow: 1;">키를 확인하지 못했어요 — 인증 실패</span>
<a href="#" style="height: 40px; box-sizing: border-box; padding: 0 16px; display: flex; align-items: center; border-radius: 8px; background: #7A2A1E; color: #FFFFFF; font-size: 14px; font-weight: 600; text-decoration: none;">키 넣으러 가기</a>
</div>
</div>
<div class="var"><b>연결을 확인하지 못함</b> — 인터넷이 없어 키를 확인하지 못했을 때. [키 넣으러 가기]가 없고 분석 버튼은 막지 않는다 · 캔버스에 없음</div>
<div class="crop" style="width: 1440px; padding: 0;">
<div role="status" style="min-height: 56px; flex-shrink: 0; box-sizing: border-box; padding: 8px 40px; display: flex; align-items: center; gap: 12px; background: #F7E6E2; color: #7A2A1E; font-size: 15px;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4"></path><path d="M12 16h.01"></path></svg>
<span style="flex-grow: 1;">연결을 확인하지 못했어요 — 인터넷이 되면 분석 버튼을 누를 때 다시 확인합니다</span>
</div>
</div>
<div class="row">
<div>
<div class="var" style="width: 598px;"><b>주소 형식 오류</b> — [분석]을 눌렀는데 주소가 세 형태가 아닐 때(3.4) · 캔버스에 없음</div>
<div class="crop" style="width: 598px;">
<div style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #E1EFEC; color: #0F6E68; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">YouTube 링크</span>
<span style="font-size: 13px; color: #6B665C;">watch · youtu.be · shorts 주소를 받아요</span>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="yt-url" style="font-size: 14px; font-weight: 600; color: #4A463F;">영상 주소</label>
<div style="display: flex; gap: 10px;">
<span style="flex-grow: 1; min-width: 0; display: flex;"><input id="yt-url" type="url" placeholder="https://www.youtube.com/watch?v=…" value="https://vimeo.com/76979871" style="width: 100%; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 10px; border: 1px solid #A33A2B; background: #FBFAF7; color: #1B1A17; font-size: 15px;"></span>
<a href="#" aria-disabled="false" style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">분석</a>
</div>
<p data-el="3.4" role="alert" style="margin: 0; font-size: 13px; line-height: 1.55; color: #A33A2B;">YouTube 영상 주소가 아니에요 — watch · youtu.be · shorts 형태로 넣어 주세요</p>
</div>
<p style="margin: 0; font-size: 13px; line-height: 1.55; color: #6B665C;">자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.</p>
</div>
</div>
</div>
<div>
<div class="var" style="width: 598px;"><b>inbox가 빔</b> — inbox 폴더에 파일이 없을 때(4.4). 키가 있어도 [선택한 파일 분석]은 막힌 모양 · 캔버스에 없음</div>
<div class="crop" style="width: 598px;">
<div style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">내 파일</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #6B665C;">~/video-agent/inbox</span>
</div>
</div>
<div role="group" aria-label="inbox 파일" style="display: flex; flex-direction: column; gap: 6px;">
<p data-el="4.4" id="inbox-empty" style="margin: 0; min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; border-radius: 10px; border: 1px dashed #CFC8BB; font-size: 14px; color: #5E5A52;">inbox 폴더에 파일이 없어요</p>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
<span style="font-size: 13px; color: #6B665C;">mp4 · mkv · mov · webm · mp3 · m4a · wav</span>
<a href="#" aria-disabled="true" style="height: 44px; flex-shrink: 0; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; background: #E2DDD3; color: #5E5A52; font-size: 15px; font-weight: 600; text-decoration: none;">선택한 파일 분석</a>
</div>
</div>
</div>
</div>
</div>
```

### 요소

| # | 이름 | 종류 | 보여주는 것 | 누르면 |
|---|---|---|---|---|
| 1 | 키 없음 배너 | 영역 | 공통 1.4 키 없음 배너. 헤더 위 전체 폭. API 키가 없거나 키 확인에 실패했을 때만 | — |
| 1.1 | 배너 문구 | 텍스트 | 키 없음: 'OpenAI API 키가 없어서 아직 분석할 수 없어요. 분석해 둔 영상은 키 없이도 읽을 수 있습니다.' / 확인 실패: '키를 확인하지 못했어요 — {이유}' | — |
| 1.2 | 키 넣으러 가기 | 링크 | 배너 오른쪽 끝, 배너 버튼 모양. 연결 문구일 때는 없다 | [[#UI-5]] |
| 2 | 제목 영역 | 영역 | 페이지 제목과 안내 | — |
| 2.1 | 제목 | 텍스트 | '어떤 영상을 읽어 볼까요?'. 페이지 제목이라 h1이다(보드와 같다) | — |
| 2.2 | 안내 | 텍스트 | 'YouTube 링크를 붙여 넣거나 inbox 폴더의 파일을 고르세요. 분석 결과는 이 PC에만 저장됩니다.' | — |
| 3 | YouTube 링크 카드 | 상자 | 입력 카드 둘 중 왼쪽 | — |
| 3.1 | 카드 머리 | 텍스트 | 링크 아이콘 타일 + 'YouTube 링크' + 'watch · youtu.be · shorts 주소를 받아요' | — |
| 3.2 | 영상 주소 | 입력 | 라벨 '영상 주소', placeholder `https://www.youtube.com/watch?v=…` | 주소 입력 |
| 3.3 | 분석 | 버튼 | 입력칸 오른쪽 주 버튼. 키가 없거나 확인 실패면 공통 1.8의 막힌 주 버튼 | 형식이 맞으면 대기 표시 뒤 [[#UI-2]] (자막 있음 판, 자막이 없으면 받아쓰기 필요 판) / 형식이 틀리면 3.4 / 이미 분석한 영상이면 [[#UI-4]] 또는 [[#UI-3]] / 막힌 상태면 [[#UI-5]] / 누를 때 키 확인에 실패하면 이동 없이 배너(1)가 뜨고 막힌 상태가 된다 / 시작할 수 없는 영상이면 [[#UI-2]] 자리에 이유와 길이, [닫기] |
| 3.4 | 입력 오류 | 텍스트 | 입력칸 바로 아래 한 줄. 받는 주소 형태를 알린다. 형식이 틀렸거나 비었을 때만 | — |
| 3.5 | 자막 안내 | 텍스트 | '자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.' | — |
| 4 | 내 파일 카드 | 상자 | 입력 카드 둘 중 오른쪽 | — |
| 4.1 | 카드 머리 | 텍스트 | 폴더 아이콘 타일 + '내 파일' + inbox 폴더 경로 `{inbox 경로}`(고정폭) | — |
| 4.2 | inbox 파일 목록 | 목록 | inbox 폴더의 파일 행 묶음. aria-label 'inbox 파일' | — |
| 4.3 | 파일 행 | 행 | 라디오 링과 점 · 파일 이름(한 줄, 넘치면 말줄임) · 길이(고정폭) · 크기. 고른 행은 선택 모양 | 이 파일을 고른다. 고르던 행은 풀린다. 화면 이동 없음 |
| 4.4 | inbox 빈 안내 | 텍스트 | inbox 폴더가 비었을 때만 파일 행 자리에 한 줄 | — |
| 4.5 | 받는 형식 | 텍스트 | 'mp4 · mkv · mov · webm · mp3 · m4a · wav' | — |
| 4.6 | 선택한 파일 분석 | 버튼 | 카드 맨 아래 줄 오른쪽 주 버튼. 키가 없거나 확인 실패면 공통 1.8의 막힌 주 버튼 | 대기 표시 뒤 [[#UI-2]] 받아쓰기 필요 판 / 이미 분석한 파일이면 [[#UI-4]] 또는 [[#UI-3]] / 막힌 상태면 [[#UI-5]] / 누를 때 키 확인에 실패하면 이동 없이 배너(1)가 뜨고 막힌 상태가 된다 / 시작할 수 없는 파일이면 [[#UI-2]] 자리에 이유와 길이, [닫기] / 키가 있고 inbox가 비었으면 동작 없음(화면 그대로) |
| 5 | 목록 머리 | 영역 | 「분석한 영상」 섹션 머리 한 줄 | — |
| 5.1 | 섹션 제목 | 텍스트 | '분석한 영상' | — |
| 5.2 | 개수 | 텍스트 | '{n}개'. 목록 행 수. 0개면 '0개' | — |
| 5.3 | 정렬 표시 | 텍스트 | 고정 글자 '최근 순'. 누를 수 없다 | — |
| 6 | 분석한 영상 목록 | 목록 | 분석한 영상 행들. 1개 이상일 때만 | — |
| 6.1 | 행 | 행 | 6.2부터 6.7까지 담은 링크. 휴지통(6.8)은 행 밖의 따로 된 버튼 | 완료 → [[#UI-4]] / 진행 중 → [[#UI-3]] / 대기 중 → [[#UI-3]] 대기 상태 / 실패 → [[#UI-3]] 실패 상태 |
| 6.2 | 출처 아이콘 | 아이콘 | 링크 모양 = YouTube, 필름 모양 = 로컬 파일 | — |
| 6.3 | 제목 | 텍스트 | 영상 제목 또는 파일 이름. 한 줄, 넘치면 말줄임 | — |
| 6.4 | 부제 | 텍스트 | 'YouTube · {채널}' 또는 '로컬 파일' | — |
| 6.5 | 길이 | 텍스트 | 영상 길이. 고정폭 글자, 누를 수 없음 | — |
| 6.6 | 상태 글자 | 텍스트 | 완료 '{오늘 HH:MM 또는 날짜} 분석' / 진행 중 '받아쓰기 중 · {n} / {m}' / 대기 중 '대기 중 · {n}번째' / 실패 '받아쓰기 {k} / {m}에서 멈춤' | — |
| 6.7 | 작은 진행 막대 | 막대 | 진행 중 행만. UI-3 퍼센트와 같은 값만큼 찬다 | — |
| 6.8 | 휴지통 | 버튼 | 아이콘 버튼. aria-label '{제목} 분석 결과 삭제'. 완료·진행 중·대기 중·실패 행 모두 | [[#UI-6]] (이 행의 영상) |
| 7 | 빈 상태 상자 | 상자 | 공통 1.7 빈 상태 상자. 분석한 영상이 0개일 때만 목록 자리에 | — |
| 7.1 | 빈 상태 제목 | 텍스트 | '아직 분석한 영상이 없어요' | — |
| 7.2 | 빈 상태 본문 | 텍스트 | 키 없음: '설정에서 OpenAI API 키를 넣은 뒤, 위에 링크를 붙여 넣거나 inbox 폴더에 파일을 넣어 보세요.' / 키 있음: 앞의 키 문장을 뺀 안내 | — |

### 규칙

- 위에서 아래로 키 없음 배너(1) · 공통 1.1 헤더 · 제목 영역(2) · 입력 카드 둘(왼쪽 3, 오른쪽 4) · 목록 머리(5) · 목록(6) 또는 빈 상태 상자(7) 순서다. 입력 카드 둘은 같은 폭으로 나란히 두고, 폭과 간격은 VA-UI-001 3.3을 따른다.
- 헤더의 '분석한 영상' 메뉴를 현재 위치로 표시하고 aria-current="page"를 붙인다(VA-UI-001 4.1).
- 키 상태와 목록 상태는 따로 정한다. 키가 없으면 배너(1)를 띄우고 분석(3.3)과 선택한 파일 분석(4.6)을 막는다. 목록은 분석한 영상이 있으면 목록(6), 없으면 빈 상태 상자(7)다. 키 없음이면서 0개인 것이 첫 실행 상태(FirstRun 보드)다.
- 배너(1)는 공통 1.4 키 없음 배너이고 role="status"다. 키가 없으면 배너 문구(1.1)는 보드 문구 그대로다. 키 넣으러 가기(1.2)와 헤더 설정 아이콘은 UI-5로 간다.
- 키가 있어도 확인에 실패하면(형식 오류·인증 실패·잔액 없음) 키 없음과 같이 다룬다. 배너(1)를 띄우고 배너 문구(1.1)를 '키를 확인하지 못했어요 — {이유}'로 바꾸고 3.3과 4.6을 막는다. 이 문구는 보드에 없다(VA-UI-001 8장).
- 인터넷이 없어 확인하지 못했으면 배너 문구(1.1)는 '연결을 확인하지 못했어요 — 인터넷이 되면 분석 버튼을 누를 때 다시 확인합니다'이고 1.2는 없다(공통 1.4). 이때 3.3과 4.6은 막지 않는다. 누르면 키를 다시 확인해, 통과하면 배너가 사라지고 그대로 UI-2를 연다. 아직 안 되면 배너가 그대로이고 UI-2는 열리지 않는다 (VA-UI-001에 없음)
- 키는 앱이 시작할 때와 3.3·4.6을 누를 때 확인한다([[VA-PRD-001#N3]], [[VA-INFRA-001#C6]]). 누를 때 확인에 실패하면 UI-2를 열지 않고 이 화면에 배너(1)를 띄운다.
- 막힌 3.3과 4.6은 공통 1.8의 막힌 주 버튼이다. aria-disabled="true"이지만 초점을 받고, 누르면 주소 형식 검사나 영상 정보 확인 없이 UI-5로 간다.
- 키가 없어도 inbox 파일 행(4.3)은 보이고 고를 수 있다. 분석한 영상이 있으면 목록(6)도 그대로 보이고, 행을 눌러 결과를 읽을 수 있다.
- 영상 주소(3.2)는 watch · youtu.be · shorts 세 형태의 YouTube 주소를 받는다([[VA-PRD-001#R2]]). 분석(3.3)을 눌렀는데 주소가 세 형태가 아니면 입력 오류(3.4)를 입력칸 바로 아래 한 줄로 보이고 화면을 바꾸지 않는다([[VA-UC-001#UC-H1]] 1a, VA-UI-001 4.5). 3.4는 받는 형태를 알려야 하고, 배치의 문구는 자리 표시다. 문구와 모양은 디자인 보강 대상이다(VA-UI-001 8장).
- 입력칸이 비어 있을 때 3.3을 누르면 형식 오류와 같은 3.4를 보인다 (VA-UI-001에 없음)
- 영상 주소(3.2)의 내용을 고치면 3.4를 지운다 (VA-UI-001에 없음)
- 3.3이나 4.6을 누르면 서버가 영상 정보를 확인하는 동안 누른 버튼에 대기 표시를 하고, 끝나면 UI-2를 연다. 대기 표시 모양은 디자인 보강 대상이다(VA-UI-001 8장).
- 대기 표시 중에는 3.3과 4.6 어느 쪽을 눌러도 새 요청을 보내지 않는다 (VA-UI-001에 없음)
- 3.3은 자막이 있으면 UI-2 자막 있음 판을, 자막이 없으면 출처 줄이 'YouTube · {채널}'인 받아쓰기 필요 판을 연다. 4.6은 UI-2 받아쓰기 필요 판을 연다.
- 형식이 맞는 주소로 3.3을 누르면 영상 주소가 서버를 거쳐 YouTube로 가서 제목·채널·길이·자막 유무를 받는다([[VA-UC-001#UC-H1]] 2번, VA-UI-001 UI-5 「밖으로 나가는 데이터」). 4.6은 서버가 inbox 파일을 PC 안에서 열어 길이·음성 트랙을 확인하고 지문을 만들 뿐, 파일은 밖으로 나가지 않는다([[VA-UC-001#UC-H2]] 2번). 키를 확인할 때는 키로 OpenAI에 가벼운 요청이 간다([[VA-UC-001#UC-H8]] 3번). 음성 조각과 스크립트 텍스트는 UI-2 [분석 시작] 전에는 OpenAI로 가지 않는다([[VA-UC-001#UC-H0]] 3a).
- 시작할 수 없는 영상(정보 조회 실패·3시간 초과·음성 트랙 없음·영상·음성 파일이 아님)이면 UI-2 자리에 이유와 길이, [닫기]만 보인다(VA-UI-001 4.5).
- 이미 분석한 영상을 다시 넣으면 UI-2를 열지 않는다. 완료된 영상이면 UI-4를 열고 공통 1.5 짧은 알림으로 '이미 분석한 영상입니다'를 알린다. 진행 중이거나 실패한 영상이면 UI-3을 연다([[VA-PRD-001#R7]], [[VA-UC-001#UC-S5]]).
- 같은 영상인지는 출처 식별자로 본다. YouTube는 영상 ID라서 watch와 youtu.be처럼 주소 형태가 달라도 같고, 파일은 내용 해시라서 이름이 달라도 같다([[VA-UC-001#UC-S5]] 1a·1b).
- UI-2에서 취소해 작업이 없는 영상은 목록(6)에 보이지 않고, 다시 넣으면 처음 넣은 영상처럼 UI-2를 연다.
- UI-2를 [취소]·닫기(X)·Esc·덮개로 닫거나 시작 불가 판을 [닫기]로 닫을 때, 또는 UI-6을 [취소]·Esc로 닫을 때는 이 화면이 그대로다. 영상 주소(3.2)에 넣은 주소와 고른 파일이 남고, 초점은 연 버튼(3.3·4.6·6.8)으로 돌아간다(공통 1.2 다이얼로그 틀). UI-2 [분석 시작]은 UI-3으로 간다.
- UI-6 [삭제]로 행이 빠지면 연 버튼(6.8)도 함께 사라지므로 초점은 바로 아래 행의 행 링크(6.1)로 간다. 아래 행이 없으면 바로 위 행의 6.1로, 목록이 비면 섹션 제목(5.1)으로 가고, 이를 위해 5.1은 tabindex="-1"이다 (VA-UI-001에 없음)
- 로컬 파일은 inbox 파일 목록(4.2)에서만 고른다. 경로 입력·업로드·브라우저 파일 선택은 없다([[VA-INFRA-001#C4]]). 카드 머리(4.1)는 inbox 폴더 경로를 고정폭 글자로, 받는 형식(4.5)은 카드 맨 아래 줄 4.6 왼쪽에 보인다([[VA-PRD-001#R1]]).
- inbox 파일 목록(4.2)은 aria-label 'inbox 파일' 묶음이다. 파일 행(4.3)은 파일 이름(한 줄, 넘치면 말줄임)·길이·크기를 보인다. 목록을 주는 서버가 파일마다 길이도 알려 준다.
- 파일은 한 번에 하나만 고른다. 고른 파일 행(4.3)은 VA-UI-001 4.2 고르는 행의 선택 모양에 aria-pressed="true"이고, 나머지 행은 aria-pressed="false"다.
- 화면을 처음 열면 inbox 목록의 맨 위 파일이 골라져 있다. 보드가 이 모습이다 (VA-UI-001에 없음)
- inbox 폴더가 비어 있으면 파일 행 자리에 inbox 빈 안내(4.4) 한 줄을 보인다. 이 상태는 VA-UI-001 8장의 디자인 보강 대상이고, 한 줄 안내라는 모양과 배치의 문구는 자리 표시다 (VA-UI-001에 없음)
- 키가 있고 inbox 폴더가 비었으면 4.6은 aria-disabled="true"이고 aria-describedby로 4.4를 잇는다. 누르면 요청을 보내지 않고 화면도 바뀌지 않는다. 키가 없거나 확인에 실패했으면 막힌 4.6 규칙대로 UI-5로 간다 (VA-UI-001에 없음)
- 목록(6)은 최근 순이다. 개수(5.2)는 행 수로 '{n}개'이고, 정렬 표시(5.3)는 고정 글자 '최근 순'이다. 정렬 바꾸기와 검색은 없다.
- 최근 순의 기준은 분석을 시작한 때(영상이 목록(6)에 올라간 때)이고, 늦게 시작한 영상이 위에 온다. 완료 행 상태 글자(6.6)의 시각은 분석이 끝난 때다 (VA-UI-001에 없음)
- 분석을 시작하면 그 영상이 바로 목록(6)에 진행 중 행으로 올라간다. 다른 영상이 분석 중이면 대기 중 행으로 올라간다. 진행 중·대기 중·실패 행도 개수(5.2)에 든다.
- 행(6.1)은 행 전체가 링크이고 휴지통(6.8)은 따로 된 버튼이다(VA-UI-001 4.6). 완료 행은 UI-4, 진행 중 행은 UI-3, 대기 중 행은 UI-3 대기 상태, 실패 행은 UI-3 실패 상태로 간다([[VA-DOM-001#Video]]).
- 길이(6.5)와 파일 행(4.3)의 길이는 누를 수 없는 고정폭 글자이고, 형식은 VA-UI-001 4.4를 따른다. 공통 1.3 시각 칩은 이 화면에 없다.
- 상태 글자(6.6)는 완료면 보통 굵기 캡션색 '{오늘 HH:MM 또는 날짜} 분석'(예: '오늘 14:08 분석', '9월 12일 분석'), 진행 중이면 청록 굵게 '받아쓰기 중 · {n} / {m}', 대기 중이면 캡션색 굵게 '대기 중 · {n}번째', 실패면 위험색 굵게 '받아쓰기 {k} / {m}에서 멈춤'이다. 색과 굵기 값은 VA-UI-001 3.1·3.2를 따른다.
- 상태 글자(6.6)의 숫자는 UI-3 숫자 규칙을 따른다. 진행 중의 n은 완료한 조각 수, 실패의 k는 실패한 조각 번호다. 대기 중의 n은 대기열에서의 차례다 — 바로 다음에 돌 영상이 1번째이고, 지금 도는 영상은 세지 않는다.
- 받아쓰기가 아닌 단계에서는 상태 글자(6.6)에 조각 숫자 대신 그 단계 이름을 쓴다. 문구 모양은 디자인 보강 대상이다(VA-UI-001 8장). 작업이 아직 첫 단계에 들어가지 않았으면(단계 값 `pending`) 진행 중은 '시작하는 중', 실패는 '시작하기 전에 멈춤'이다 — 워커가 꺼낸 직후 서버가 죽었거나 임시 폴더를 만들지 못한 경우다 (VA-UI-001에 없음)
- 작은 진행 막대(6.7)는 진행 중 행에만 있고 UI-3의 퍼센트와 같은 값을 쓴다. 보드의 40%와 UI-3의 38% 차이는 예시 값이다.
- 이 화면을 열어 둔 동안 진행 중 행은 서버에서 새로 받아 6.6과 6.7을 갱신하고, 끝나면 완료 행으로, 실패하면 실패 행으로 바꾼다. 대기 중 행도 같이 새로 받아 차례({n})를 고치고, 차례가 오면 진행 중 행으로 바꾼다. 진행 중 · 대기 중 행이 있는 동안 3초마다 목록을 다시 받고, 그런 행이 없으면 다시 받지 않는다 (VA-UI-001에 없음)
- 휴지통(6.8)은 완료·진행 중·대기 중·실패 행 모두에 있고 aria-label은 '{제목} 분석 결과 삭제'다. 누르면 그 영상으로 UI-6을 연다. 진행 중인 영상은 UI-6에서 작업을 멈춘 뒤, 대기 중인 영상은 대기열에서 뺀 뒤 지운다. [삭제]하면 이 화면으로 돌아와 그 행이 빠지고 개수(5.2)가 줄어들며, 마지막 행이었으면 빈 상태 상자(7)가 보인다.
- 빈 상태 상자(7)는 공통 1.7 빈 상태 상자다. 분석한 영상이 0개일 때만 목록(6) 자리에 보이고 개수(5.2)는 '0개'다([[VA-UC-001#UC-H5]] 1b).
- 빈 상태 본문(7.2)은 키가 없으면 보드 문구 그대로다. 키가 있으면 앞의 키 문장 '설정에서 OpenAI API 키를 넣은 뒤,'를 빼고 링크를 붙여 넣거나 inbox 폴더에 파일을 넣으라는 안내만 둔다.
- 안내(2.2)의 '분석 결과는 이 PC에만 저장됩니다.'([[VA-INFRA-001#C9]])와 자막 안내(3.5)의 '자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.'([[VA-PRD-001#N1]])는 상태와 관계없이 늘 보인다.
- 다른 영상이 분석 중이어도 3.3과 4.6은 켜져 있다(보드). 그때 시작한 분석은 대기열에 들어가 차례를 기다린다(VA-UI-001 7장 16, [[VA-UC-001#UC-H0]] 3b).

### 시나리오

**S-1 YouTube 링크로 분석을 시작한다** — [[VA-UC-001#UC-H1]] 기본 흐름 1~3
1. 영상 주소(3.2)에 youtu.be 주소를 붙여 넣는다
2. 분석(3.3)을 누른다. 형식이 맞아 3.3에 대기 표시가 붙고, 서버가 제목·채널·길이·자막 유무를 확인한다
3. 자막이 있는 영상이라 UI-2 자막 있음 판이 이 화면 위에 뜬다
4. UI-2에서 [분석 시작]을 누르면 UI-3으로 간다. 나중에 이 화면으로 돌아오면 이 영상이 목록(6) 맨 위에 있다. 아직 돌고 있으면 진행 중 행, 끝났으면 완료 행이다

**S-2 inbox 파일로 분석을 시작한다** — [[VA-UC-001#UC-H2]] 기본 흐름 1~3
1. 내 파일 카드(4)에서 아직 분석하지 않은 파일 행(배치 예시의 세 번째 interview_0903.m4a)을 누른다. 그 행만 파일 행(4.3)의 선택 모양이 되고 맨 위 행은 풀린다
2. 선택한 파일 분석(4.6)을 누른다. 4.6에 대기 표시가 붙고, 서버가 길이와 음성 트랙을 확인하고 파일 지문을 만든다
3. UI-2 받아쓰기 필요 판이 이 화면 위에 뜬다
4. [분석 시작]을 누르면 UI-3 받아쓰기 중으로 간다

**S-3 사전 안내에서 취소한다** — [[VA-UC-001#UC-H0]] 확장 3a
1. 분석(3.3)으로 연 UI-2에서 [취소]를 누른다
2. UI-2가 닫히고 영상 주소(3.2)에 넣은 주소가 그대로 남는다. 초점은 3.3에 있다
3. 목록(6)에는 이 영상이 올라가지 않는다
4. 같은 주소로 3.3을 다시 누르면 이미 분석한 영상으로 보지 않고 UI-2를 다시 연다

**S-4 주소 형식이 틀렸다** — [[VA-UC-001#UC-H1]] 확장 1a
1. 영상 주소(3.2)에 YouTube가 아닌 주소를 넣고 분석(3.3)을 누른다
2. 입력 오류(3.4)가 입력칸 바로 아래에 받는 주소 형태와 함께 뜬다. 화면은 바뀌지 않는다
3. 주소를 고치면 3.4가 사라진다. 3.3을 다시 누르면 S-1의 2번부터 이어진다

**S-5 이미 분석한 영상을 다시 넣었다** — [[VA-UC-001#UC-H5]] 확장 1a · [[VA-UC-001#UC-S5]] 확장 1a·1b
1. 전에 youtu.be 주소로 분석을 끝낸 영상을 watch 주소로 영상 주소(3.2)에 넣고 분석(3.3)을 누른다
2. 영상 ID가 같아 같은 영상으로 판정된다. UI-2는 열리지 않는다
3. UI-4가 열리고 공통 1.5 짧은 알림 '이미 분석한 영상입니다'가 잠깐 보인다
4. 받아쓰기 중인 파일을 다른 이름으로 복사해 둔 것을 파일 행(4.3)에서 고르고 4.6을 누르면, 내용 해시가 같아 UI-2 없이 UI-3이 열린다

**S-6 목록에서 다시 연다** — [[VA-UC-001#UC-H5]] 기본 흐름 1~3 · [[VA-UC-001#UC-S6]] 기본 흐름 1~2
1. 목록(6)에 행이 최근 순으로 있고 개수(5.2)는 '5개'다
2. 완료 행(6.1)을 누르면 UI-4가 열리고 저장된 결과가 보인다
3. 진행 중 행은 상태 글자(6.6) '받아쓰기 중 · 12 / 30'과 작은 진행 막대(6.7)를 보이고, 화면을 열어 둔 동안 숫자와 막대가 늘어난다. 누르면 UI-3이 열린다
4. 실패 행은 상태 글자(6.6)가 '받아쓰기 16 / 24에서 멈춤'이다. 누르면 UI-3 실패 상태가 열리고 거기서 이어서 다시 시도할 수 있다

**S-7 목록에서 지운다** — [[VA-UC-001#UC-H6]] 기본 흐름 1~4, 확장 3a
1. 지울 행의 휴지통(6.8)을 누른다
2. 그 영상의 UI-6이 이 화면 위에 뜬다
3. [삭제]를 누르면 UI-6이 닫히고 그 행이 목록(6)에서 빠지며 개수(5.2)가 하나 줄어든다. 초점은 바로 아래 행의 행 링크(6.1)로 간다
4. [삭제] 대신 [취소]를 누르면 목록은 그대로이고 초점이 6.8로 돌아온다

**S-8 첫 실행** — [[VA-UC-001#UC-H8]] 트리거 · [[VA-UC-001#UC-H5]] 확장 1b
1. 키 없이 앱을 처음 열면 헤더 위에 키 없음 배너(1)가 뜬다
2. 분석(3.3)과 선택한 파일 분석(4.6)이 막힌 모양이다. 파일 행(4.3)은 보이고 고를 수 있다
3. 목록 자리에 빈 상태 상자(7)가 보이고 개수(5.2)는 '0개'다
4. 4.6을 누르면 UI-5로 간다. 키 넣으러 가기(1.2)를 눌러도 같다
5. UI-5에서 [확인하고 저장]으로 키를 저장하고 [저장]을 누르면 이 화면으로 돌아온다
6. 배너(1)가 사라지고 3.3과 4.6이 켜진다. 빈 상태 본문(7.2)에서 키 문장이 빠진다

**S-9 키 확인에 실패했다** — [[VA-UC-001#UC-H8]] 최소 보장 · 확장 3a
1. 키가 있는 상태에서 분석(3.3)을 누른다. 키 확인이 인증 실패로 끝난다
2. UI-2는 열리지 않고 배너(1)가 뜬다. 배너 문구(1.1)는 '키를 확인하지 못했어요 — 인증 실패'다
3. 3.3과 4.6이 막힌다. 목록(6)의 행은 그대로 눌러 결과를 읽을 수 있다
4. 키 넣으러 가기(1.2)를 눌러 UI-5에서 키를 바꾼다

**S-10 키 없이 분석한 영상을 읽는다** — [[VA-UC-001#UC-H5]] 기본 흐름 1~3
1. 전에 분석한 영상이 있는데 API 키가 없는 채로 앱을 연다
2. 배너(1)가 뜨고 3.3과 4.6이 막힌다
3. 목록(6)은 행과 개수(5.2)를 그대로 보인다. 빈 상태 상자(7)는 없다
4. 완료 행(6.1)을 누르면 UI-4가 열려 결과를 읽을 수 있다

**S-11 시작할 수 없는 영상이다** — [[VA-UC-001#UC-H0]] 확장 2b · [[VA-UC-001#UC-H1]] 확장 2a · [[VA-UC-001#UC-H2]] 확장 2a
1. 3시간이 넘는 영상 주소를 영상 주소(3.2)에 넣고 분석(3.3)을 누른다
2. 3.3에 대기 표시가 붙은 뒤 UI-2 자리에 이유와 영상 길이, [닫기]만 뜬다. [분석 시작]은 없다
3. [닫기]를 누르면 이 화면이 그대로이고 3.2에 주소가 남으며 초점은 3.3으로 돌아온다
4. 목록(6)에는 이 영상이 올라가지 않는다
5. 비공개·삭제된 영상 주소를 3.3으로 넣거나 음성 트랙이 없는 파일을 4.6으로 넣어도 같은 자리에 이유와 [닫기]만 뜬다

**S-12 인터넷 없이 앱을 열었다** — [[VA-UC-001#UC-H8]] 확장 3b
1. 키는 맞는데 인터넷이 끊긴 채로 앱을 연다. 시작할 때의 키 확인이 연결 실패로 끝난다
2. 배너(1)가 뜨고 배너 문구(1.1)는 '연결을 확인하지 못했어요 — 인터넷이 되면 분석 버튼을 누를 때 다시 확인합니다'다. 키 넣으러 가기(1.2)는 없다
3. 3.3과 4.6은 켜져 있다. 목록(6)의 행은 그대로 눌러 결과를 읽는다
4. 인터넷이 돌아온 뒤 주소를 넣고 분석(3.3)을 누른다. 키 확인을 통과해 배너가 사라지고 UI-2가 열린다

---

## UI-2 사전 안내

| 항목 | 내용 |
|---|---|
| 화면 설계 | [[VA-UI-001#UI-2]] |
| 경로 | (다이얼로그) |
| 디자인 보드 | Estimate · EstimateLocal |
| 진입 | UI-1 [분석] → 자막 있음 판(자막이 없으면 받아쓰기 필요 판) · UI-1 [선택한 파일 분석] → 받아쓰기 필요 판 · 두 버튼 모두 시작할 수 없는 영상이면 시작 불가 판(7) |
| 유스케이스 | [[VA-UC-001#UC-S1]] 기본 흐름 1~6, 확장 1a·2a · [[VA-UC-001#UC-H0]] 기본 흐름 2~3, 확장 2b·3a · [[VA-UC-001#UC-H1]] 기본 흐름 1~3, 확장 2a·2b · [[VA-UC-001#UC-H2]] 기본 흐름 1~3, 확장 1a·2a·2b |

### 배치

```html
<!-- 주 보드: 캔버스 Estimate(자막 있음 판). 뒤는 UI-1 홈이 덮개 아래 그대로다. 아래는 상태 보드 -->
<div style="width: 1440px; height: 960px; position: relative; overflow: hidden; background: #F6F4EF;">
<div style="position: absolute; left: 0; top: 0; width: 1440px; height: 960px;">
<div style="width: 1440px; height: 960px; box-sizing: border-box; background: #F6F4EF; display: flex; flex-direction: column; overflow: hidden;">
<header style="height: 64px; flex-shrink: 0; box-sizing: border-box; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2DDD3; background: #F6F4EF;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 10px; color: #1B1A17; text-decoration: none;">
<span style="width: 30px; height: 30px; border-radius: 8px; background: #1B1A17; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="#F6F4EF" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;">Video Agent</span>
</a>
<nav aria-label="주 메뉴" style="display: flex; align-items: center; gap: 4px;">
<a href="#" aria-current="page" style="height: 44px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; border-radius: 10px; background: #EAE6DD; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">분석한 영상</a>
<a href="#" aria-label="설정" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 7h-9"></path><path d="M14 17H5"></path><circle cx="17" cy="17" r="3"></circle><circle cx="7" cy="7" r="3"></circle></svg>
</a>
</nav>
</header>
<main style="flex-grow: 1; min-height: 0; box-sizing: border-box; padding: 44px 160px 0; display: flex; flex-direction: column; gap: 44px;">
<section aria-labelledby="home-title" style="display: flex; flex-direction: column; gap: 24px;">
<div style="display: flex; flex-direction: column; gap: 8px;">
<h1 id="home-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 40px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em;">어떤 영상을 읽어 볼까요?</h1>
<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #5E5A52;">YouTube 링크를 붙여 넣거나 inbox 폴더의 파일을 고르세요. 분석 결과는 이 PC에만 저장됩니다.</p>
</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px;">
<div style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #E1EFEC; color: #0F6E68; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">YouTube 링크</span>
<span style="font-size: 13px; color: #6B665C;">watch · youtu.be · shorts 주소를 받아요</span>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="yt-url" style="font-size: 14px; font-weight: 600; color: #4A463F;">영상 주소</label>
<div style="display: flex; gap: 10px;">
<span style="flex-grow: 1; min-width: 0; display: flex;"><input id="yt-url" type="url" placeholder="https://www.youtube.com/watch?v=…" value="" style="width: 100%; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FBFAF7; color: #1B1A17; font-size: 15px;"></span>
<a href="#" aria-disabled="false" style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">분석</a>
</div>
</div>
<p style="margin: 0; font-size: 13px; line-height: 1.55; color: #6B665C;">자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.</p>
</div>
<div style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">내 파일</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #6B665C;">~/video-agent/inbox</span>
</div>
</div>
<div role="group" aria-label="inbox 파일" style="display: flex; flex-direction: column; gap: 6px;">
<button type="button" aria-pressed="true" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #0F6E68; background: #E1EFEC; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: #0F6E68;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">workshop_0912.mp4</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">2:30:00</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">1.8 GB</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #E2DDD3; background: #FBFAF7; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: transparent;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">meetup_0901.mp4</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">1:58:20</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">1.4 GB</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #E2DDD3; background: #FBFAF7; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: transparent;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">interview_0903.m4a</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">1:04:12</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">58 MB</span>
</button>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
<span style="font-size: 13px; color: #6B665C;">mp4 · mkv · mov · webm · mp3 · m4a · wav</span>
<a href="#" aria-disabled="false" style="height: 44px; flex-shrink: 0; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">선택한 파일 분석</a>
</div>
</div>
</div>
</section>
<section aria-labelledby="list-title" style="display: flex; flex-direction: column; gap: 12px;">
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="list-title" tabindex="-1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">분석한 영상</h2>
<span style="font-size: 14px; color: #6B665C;">5개</span>
</div>
<span style="font-size: 13px; color: #6B665C;">최근 순</span>
</div>
<div style="border-top: 1px solid #E2DDD3; display: flex; flex-direction: column;">
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">벡터 검색 튜닝 실전</span>
<span style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">38:05</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 600; color: #6B665C;">대기 중 · 1번째</span>
</span>
</a>
<a href="#" aria-label="벡터 검색 튜닝 실전 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</span>
<span style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">50:12</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 400; color: #6B665C;">오늘 14:08 분석</span>
</span>
</a>
<a href="#" aria-label="RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">workshop_0912.mp4</span>
<span style="font-size: 13px; color: #6B665C;">로컬 파일</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">2:30:00</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 600; color: #0F6E68;">받아쓰기 중 · 12 / 30</span>
<span style="width: 160px; height: 4px; border-radius: 2px; background: #E2DDD3; display: block; overflow: hidden;">
<span style="width: 40%; height: 4px; display: block; background: #0F6E68;"></span>
</span>
</span>
</a>
<a href="#" aria-label="workshop_0912.mp4 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">meetup_0901.mp4</span>
<span style="font-size: 13px; color: #6B665C;">로컬 파일</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">1:58:20</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 600; color: #A33A2B;">받아쓰기 16 / 24에서 멈춤</span>
</span>
</a>
<a href="#" aria-label="meetup_0901.mp4 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">LLM 에이전트 설계 패턴 정리</span>
<span style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">1:12:40</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 400; color: #6B665C;">9월 12일 분석</span>
</span>
</a>
<a href="#" aria-label="LLM 에이전트 설계 패턴 정리 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
</div>
</section>
</main>
</div>
</div>
<div style="position: absolute; left: 0; top: 0; width: 1440px; height: 960px; box-sizing: border-box; padding-top: 104px; display: flex; justify-content: center; align-items: flex-start; background: rgba(27, 26, 23, 0.52);">
<div role="dialog" aria-modal="true" aria-labelledby="est-title" style="width: 620px; box-sizing: border-box; padding: 32px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 28px 80px rgba(27, 26, 23, 0.32); display: flex; flex-direction: column; gap: 22px;">
<div data-el="1" style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;">
<div style="display: flex; flex-direction: column; gap: 6px;">
<h2 id="est-title" data-el="1.1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 28px; line-height: 1.3; font-weight: 600; letter-spacing: -0.01em;">분석을 시작할까요?</h2>
<span data-el="1.2" style="font-size: 15px; color: #5E5A52;">걸릴 시간과 비용을 먼저 확인하세요.</span>
</div>
<a data-el="1.3" href="#" aria-label="닫기" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
</a>
</div>
<div data-el="2" style="box-sizing: border-box; padding: 16px; border-radius: 12px; background: #F6F4EF; display: flex; gap: 16px;">
<span data-el="2.1" style="width: 144px; height: 81px; flex-shrink: 0; border-radius: 8px; background: #E2DDD3; color: #6B665C; display: flex; align-items: center; justify-content: center;">
<svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<div style="min-width: 0; display: flex; flex-direction: column; gap: 6px;">
<span data-el="2.2" style="font-size: 17px; line-height: 1.45; font-weight: 600;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</span>
<span data-el="2.3" style="font-size: 14px; color: #5E5A52;">YouTube · [채널명]</span>
<div style="display: flex; flex-wrap: wrap; gap: 6px;">
<span data-el="2.4" style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">길이 50:12</span>
<span data-el="2.5" style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #134E49; font-size: 13px; font-weight: 500;">자막 있음 · 한국어</span>
</div>
</div>
</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;">
<div data-el="3" style="box-sizing: border-box; padding: 18px; border-radius: 12px; border: 1px solid #E2DDD3; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #5E5A52;">예상 시간</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 32px; line-height: 1.2; font-weight: 600; letter-spacing: -0.01em;" data-el="3.1">약 1분</span>
<span data-el="3.2" style="font-size: 13px; line-height: 1.55; color: #5E5A52;">받아쓰기 없이 자막을 가져와 바로 요약합니다.</span>
</div>
<div data-el="4" style="box-sizing: border-box; padding: 18px; border-radius: 12px; border: 1px solid #E2DDD3; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #5E5A52;">예상 비용</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 32px; line-height: 1.2; font-weight: 600; letter-spacing: -0.01em;" data-el="4.1">약 $0.02</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span data-el="4.2" style="display: flex; justify-content: space-between; gap: 8px; font-size: 13px; line-height: 1.55; color: #5E5A52;">
<span>받아쓰기 (자막 사용)</span>
<span style="font-family: 'IBM Plex Mono', monospace;">$0.00</span>
</span>
<span data-el="4.3" style="display: flex; justify-content: space-between; gap: 8px; font-size: 13px; line-height: 1.55; color: #5E5A52;">
<span>요약 · 챕터 · 추천 질문</span>
<span style="font-family: 'IBM Plex Mono', monospace;">$0.02</span>
</span>
</div>
</div>
</div>
<div data-el="5" style="box-sizing: border-box; padding: 14px 16px; border-radius: 12px; background: #E1EFEC; color: #134E49; display: flex; gap: 10px; font-size: 14px; line-height: 1.55;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="flex-shrink: 0; margin-top: 2px; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
<span>요약을 만들려고 스크립트 텍스트가 OpenAI(gpt-5-mini)로 전송됩니다. 영상은 전송되지 않아요.</span>
</div>
<div data-el="6" style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
<a data-el="6.2" href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">취소</a>
<a data-el="6.3" href="#" style="height: 44px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">분석 시작</a>
</div>
</div>
</div>
</div>
<div class="row">
<div>
<div class="var" style="width: 700px;"><b>받아쓰기 필요 판</b> — 자막이 없는 영상 · 캔버스 EstimateLocal 보드</div>
<div class="crop dim">
<div role="dialog" aria-modal="true" aria-labelledby="est-title" style="width: 620px; box-sizing: border-box; padding: 32px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 28px 80px rgba(27, 26, 23, 0.32); display: flex; flex-direction: column; gap: 22px;">
<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;">
<div style="display: flex; flex-direction: column; gap: 6px;">
<h2 id="est-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 28px; line-height: 1.3; font-weight: 600; letter-spacing: -0.01em;">분석을 시작할까요?</h2>
<span style="font-size: 15px; color: #5E5A52;">걸릴 시간과 비용을 먼저 확인하세요.</span>
</div>
<a href="#" aria-label="닫기" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; padding: 16px; border-radius: 12px; background: #F6F4EF; display: flex; gap: 16px;">
<span style="width: 144px; height: 81px; flex-shrink: 0; border-radius: 8px; background: #E2DDD3; color: #6B665C; display: flex; align-items: center; justify-content: center;">
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<div style="min-width: 0; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 17px; line-height: 1.45; font-weight: 600;">workshop_0912.mp4</span>
<span style="font-size: 14px; color: #5E5A52;">로컬 파일 · inbox</span>
<div style="display: flex; flex-wrap: wrap; gap: 6px;">
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">길이 2:30:00</span>
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">자막 없음 · 받아쓰기 필요</span>
</div>
</div>
</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;">
<div style="box-sizing: border-box; padding: 18px; border-radius: 12px; border: 1px solid #E2DDD3; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #5E5A52;">예상 시간</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 32px; line-height: 1.2; font-weight: 600; letter-spacing: -0.01em;">약 8분</span>
<span style="font-size: 13px; line-height: 1.55; color: #5E5A52;">음성을 뽑아 30개 조각으로 나누고, 3개씩 동시에 받아씁니다.</span>
</div>
<div style="box-sizing: border-box; padding: 18px; border-radius: 12px; border: 1px solid #E2DDD3; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #5E5A52;">예상 비용</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 32px; line-height: 1.2; font-weight: 600; letter-spacing: -0.01em;">약 $0.92</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="display: flex; justify-content: space-between; gap: 8px; font-size: 13px; line-height: 1.55; color: #5E5A52;">
<span>받아쓰기 150분 × $0.006</span>
<span style="font-family: 'IBM Plex Mono', monospace;">$0.90</span>
</span>
<span style="display: flex; justify-content: space-between; gap: 8px; font-size: 13px; line-height: 1.55; color: #5E5A52;">
<span>요약 · 챕터 · 추천 질문</span>
<span style="font-family: 'IBM Plex Mono', monospace;">$0.02</span>
</span>
</div>
</div>
</div>
<div style="box-sizing: border-box; padding: 14px 16px; border-radius: 12px; background: #E1EFEC; color: #134E49; display: flex; gap: 10px; font-size: 14px; line-height: 1.55;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="flex-shrink: 0; margin-top: 2px; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
<span>받아쓰기에는 음성 조각이, 요약에는 스크립트 텍스트가 OpenAI로 전송됩니다. 영상 파일 자체는 이 PC 밖으로 나가지 않아요.</span>
</div>
<div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">취소</a>
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">분석 시작</a>
</div>
</div>
</div>
</div>
<div>
<div class="var" style="width: 700px;"><b>다른 영상이 분석 중</b> — 버튼 줄 왼쪽에 대기 안내(6.1) · 캔버스에 없음</div>
<div class="crop dim">
<div role="dialog" aria-modal="true" aria-labelledby="est-title" style="width: 620px; box-sizing: border-box; padding: 32px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 28px 80px rgba(27, 26, 23, 0.32); display: flex; flex-direction: column; gap: 22px;">
<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;">
<div style="display: flex; flex-direction: column; gap: 6px;">
<h2 id="est-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 28px; line-height: 1.3; font-weight: 600; letter-spacing: -0.01em;">분석을 시작할까요?</h2>
<span style="font-size: 15px; color: #5E5A52;">걸릴 시간과 비용을 먼저 확인하세요.</span>
</div>
<a href="#" aria-label="닫기" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; padding: 16px; border-radius: 12px; background: #F6F4EF; display: flex; gap: 16px;">
<span style="width: 144px; height: 81px; flex-shrink: 0; border-radius: 8px; background: #E2DDD3; color: #6B665C; display: flex; align-items: center; justify-content: center;">
<svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<div style="min-width: 0; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 17px; line-height: 1.45; font-weight: 600;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</span>
<span style="font-size: 14px; color: #5E5A52;">YouTube · [채널명]</span>
<div style="display: flex; flex-wrap: wrap; gap: 6px;">
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">길이 50:12</span>
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #134E49; font-size: 13px; font-weight: 500;">자막 있음 · 한국어</span>
</div>
</div>
</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;">
<div style="box-sizing: border-box; padding: 18px; border-radius: 12px; border: 1px solid #E2DDD3; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #5E5A52;">예상 시간</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 32px; line-height: 1.2; font-weight: 600; letter-spacing: -0.01em;">약 1분</span>
<span style="font-size: 13px; line-height: 1.55; color: #5E5A52;">받아쓰기 없이 자막을 가져와 바로 요약합니다.</span>
</div>
<div style="box-sizing: border-box; padding: 18px; border-radius: 12px; border: 1px solid #E2DDD3; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #5E5A52;">예상 비용</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 32px; line-height: 1.2; font-weight: 600; letter-spacing: -0.01em;">약 $0.02</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="display: flex; justify-content: space-between; gap: 8px; font-size: 13px; line-height: 1.55; color: #5E5A52;">
<span>받아쓰기 (자막 사용)</span>
<span style="font-family: 'IBM Plex Mono', monospace;">$0.00</span>
</span>
<span style="display: flex; justify-content: space-between; gap: 8px; font-size: 13px; line-height: 1.55; color: #5E5A52;">
<span>요약 · 챕터 · 추천 질문</span>
<span style="font-family: 'IBM Plex Mono', monospace;">$0.02</span>
</span>
</div>
</div>
</div>
<div style="box-sizing: border-box; padding: 14px 16px; border-radius: 12px; background: #E1EFEC; color: #134E49; display: flex; gap: 10px; font-size: 14px; line-height: 1.55;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="flex-shrink: 0; margin-top: 2px; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
<span>요약을 만들려고 스크립트 텍스트가 OpenAI(gpt-5-mini)로 전송됩니다. 영상은 전송되지 않아요.</span>
</div>
<div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
<span data-el="6.1" style="margin-right: auto; max-width: 300px; font-size: 13px; line-height: 1.55; color: #5E5A52;">지금 다른 영상을 분석 중이에요. 시작하면 차례를 기다렸다가 저절로 시작돼요.</span>
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">취소</a>
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">분석 시작</a>
</div>
</div>
</div>
</div>
</div>
<div class="var"><b>시작 불가 판</b> — 시작할 수 없는 영상일 때 1~6 대신 뜬다(7). 이유 · 길이 · [닫기]만 · 캔버스에 없음</div>
<div class="crop dim">
<div role="dialog" aria-modal="true" aria-labelledby="blk-title" data-el="7" style="width: 540px; box-sizing: border-box; padding: 32px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 28px 80px rgba(27, 26, 23, 0.32); display: flex; flex-direction: column; gap: 22px;">
<div style="display: flex; flex-direction: column; gap: 12px;">
<h2 id="blk-title" data-el="7.1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 28px; line-height: 1.3; font-weight: 600; letter-spacing: -0.01em;">3시간이 넘는 영상은 분석할 수 없어요</h2>
<div style="display: flex; flex-wrap: wrap; gap: 6px;">
<span data-el="7.2" style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">길이 3:12:40</span>
</div>
</div>
<div style="display: flex; justify-content: flex-end; gap: 10px;">
<a data-el="7.3" href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">닫기</a>
</div>
</div>
</div>
```

### 요소

| # | 이름 | 종류 | 보여주는 것 | 누르면 |
|---|---|---|---|---|
| 1 | 머리 | 영역 | 제목 묶음과 오른쪽 닫기. 공통 1.2 다이얼로그 틀의 머리 | — |
| 1.1 | 제목 | 텍스트 | '분석을 시작할까요?'. 다이얼로그 이름(aria-labelledby) | — |
| 1.2 | 부제 | 텍스트 | '걸릴 시간과 비용을 먼저 확인하세요.' | — |
| 1.3 | 닫기 | 버튼 | X 아이콘 버튼. aria-label '닫기' | 6.2와 같다. 아무것도 전송하지 않고 닫힘 → [[#UI-1]] |
| 2 | 영상 카드 | 상자 | 고른 영상. 왼쪽 썸네일 자리, 오른쪽 제목·출처 줄·칩 | — |
| 2.1 | 썸네일 자리 | 상자 | 아이콘만. YouTube는 재생 삼각형, 로컬 파일은 필름. 실제 썸네일 이미지는 없다 | — |
| 2.2 | 영상 제목 | 텍스트 | YouTube 영상 제목 또는 파일 이름 | — |
| 2.3 | 출처 줄 | 텍스트 | 'YouTube · {채널}' 또는 '로컬 파일 · inbox' | — |
| 2.4 | 길이 칩 | 칩 | '길이 {길이}'. 회색 메타 칩 | — |
| 2.5 | 자막 칩 | 칩 | 자막이 있으면 청록 메타 칩 '자막 있음 · {언어}', 없으면 회색 메타 칩 '자막 없음 · 받아쓰기 필요' | — |
| 3 | 예상 시간 카드 | 상자 | 라벨 '예상 시간', 값, 설명 | — |
| 3.1 | 예상 시간 | 텍스트 | '약 {n}분'. 큰 숫자 | — |
| 3.2 | 시간 설명 | 텍스트 | 어떻게 처리하는지 한 줄. 자막 사용 또는 조각 수·동시 수 | — |
| 4 | 예상 비용 카드 | 상자 | 라벨 '예상 비용', 합계, 줄별 금액 둘 | — |
| 4.1 | 비용 합계 | 텍스트 | '약 ${합계}'. 큰 숫자 | — |
| 4.2 | 받아쓰기 비용 줄 | 행 | 왼쪽 '받아쓰기 (자막 사용)' 또는 '받아쓰기 {분}분 × ${단가}', 오른쪽 고정폭 금액 | — |
| 4.3 | 요약 비용 줄 | 행 | 왼쪽 '요약 · 챕터 · 추천 질문', 오른쪽 고정폭 금액(추정값) | — |
| 5 | 전송 안내 상자 | 상자 | 정보 아이콘과 OpenAI로 가는 것·가지 않는 것. VA-UI-001 4.5 정보 상자 | — |
| 6 | 버튼 줄 | 영역 | 왼쪽 안내 자리, 오른쪽 [취소] [분석 시작] | — |
| 6.1 | 대기 안내 | 텍스트 | 다른 영상이 분석 중이거나 대기 중일 때만 '지금 다른 영상을 분석 중이에요. 시작하면 차례를 기다렸다가 저절로 시작돼요.' 캡션 글자. 아니면 비어 있다 | — |
| 6.2 | 취소 | 버튼 | 보조 버튼 '취소' | 아무것도 전송하지 않고 닫힘 → [[#UI-1]] |
| 6.3 | 분석 시작 | 버튼 | 주 버튼 '분석 시작'. 열릴 때 처음 초점 | 분석 시작(다른 영상이 분석 중이면 대기열에 넣음), 영상이 목록에 올라감 → [[#UI-3]] |
| 7 | 시작 불가 판 | 다이얼로그 | 시작할 수 없는 영상일 때 1~6 대신 뜨는 판. 이유·길이·닫기만 | — |
| 7.1 | 이유 | 텍스트 | 무엇이 왜 안 되는지 한 줄. 이 판의 다이얼로그 이름(aria-labelledby) | — |
| 7.2 | 길이 칩 | 칩 | '길이 {길이}'. 길이를 알 때만 | — |
| 7.3 | 닫기 | 버튼 | '닫기'. 분석 시작 버튼은 없다 | 닫힘 → [[#UI-1]] |

### 규칙

- UI-1 위에 뜨는 다이얼로그다. 덮개·틀·버튼 모양은 공통 1.2 다이얼로그 틀과 공통 1.8 버튼과 추천 질문을 쓰고, 값은 VA-UI-001 3장·4장을 따른다.
- 영상 정보와 예상치가 다 준비된 뒤에 열린다. 확인하는 동안의 대기 표시는 UI-1 분석 버튼이 맡으므로 이 다이얼로그에는 불러오는 중 모습이 없다.
- UI-2가 열리지 않는 때는 이렇다(UI-1 규칙). YouTube 주소 형식이 틀리면 UI-1 입력칸 아래에 알리고 화면을 바꾸지 않는다([[VA-UC-001#UC-H1]] 확장 1a). API 키가 없거나 이미 확인에 실패한 상태면 UI-1의 두 분석 버튼이 막혀 있고 누르면 UI-5로 간다. 누르는 순간 키 확인에 실패하면 UI-2를 열지 않고 UI-1에 공통 1.4 키 없음 배너를 띄운다. 이미 분석한 영상이면 완료는 UI-4, 진행 중·실패는 UI-3이 열린다.
- 판은 자막 유무로 정한다. 자막이 있으면 자막 있음 판, 없으면 받아쓰기 필요 판이다. 자막 없는 YouTube도 받아쓰기 필요 판이고 2.3이 'YouTube · {채널}'이다.
- 자막 없는 YouTube의 2.1은 출처대로 재생 삼각형이고 2.2는 영상 제목이다 (VA-UI-001에 없음).
- 2.1은 아이콘만 둔다. YouTube는 재생 삼각형, 로컬 파일은 필름이다. 실제 썸네일 이미지는 그리지 않는다.
- 2.2는 말줄임 없이 줄을 바꿔 전부 보인다 (VA-UI-001에 없음).
- 2.4·2.5는 VA-UI-001 4.2 메타 칩이고, '자막 있음 · {언어}'일 때의 2.5만 청록 메타 칩이다. 길이 형식은 VA-UI-001 4.4를 따른다.
- 자막 있음 판은 3.1 '약 1분', 3.2 '받아쓰기 없이 자막을 가져와 바로 요약합니다.', 4.2 '받아쓰기 (자막 사용)' $0.00이다.
- 받아쓰기 필요 판은 3.1 '약 {n}분', 3.2 '음성을 뽑아 {k}개 조각으로 나누고, {c}개씩 동시에 받아씁니다.', 4.2 '받아쓰기 {분}분 × ${단가}' ${금액}이다. k와 c는 서버가 준 값이고 고정 문구가 아니다.
- 로컬 음성 파일(mp3·m4a·wav)은 음성 추출이 없으므로 3.2에서 '음성을 뽑아'를 빼고 '{k}개 조각으로 나누고, {c}개씩 동시에 받아씁니다.'로 쓴다([[VA-UC-001#UC-H2]] 확장 2b) (VA-UI-001에 없음).
- 로컬 음성 파일의 5는 받아쓰기 필요 판 문구에서 '영상 파일 자체는'을 '음성 파일 자체는'으로 바꿔 쓴다. 보드가 없어 디자인 보강을 기다린다 (VA-UI-001에 없음).
- 4.1은 4.2와 4.3의 합이고 앞에 '약'을 붙인다. 4.2·4.3은 왼쪽에 항목 이름, 오른쪽에 고정폭 금액이다.
- 4.2의 단가는 UI-5에서 고른 받아쓰기 모델의 단가다. 4.3은 추정값이고 추정 방법은 MINISPEC에서 정한다.
- 자막이 있어도 4.3 요약 비용이 들어 4.1은 $0이 아니다. [[VA-PRD-001#R8]]의 「비용 없음」, [[VA-UC-001#UC-S1]] 기본 흐름 5번의 「자막 있음: 약 1분, 비용 없음」과 다르고, 두 상위 갱신 요청이 VA-UI-001 8장에 있다.
- 3·4의 숫자(시간·조각 수·분·단가·금액)는 서버가 계산한 값을 그대로 보이고 화면에서 다시 계산하지 않는다 (VA-UI-001에 없음).
- 5는 무엇이 OpenAI로 가고 무엇이 안 가는지 알린다. 자막 있음 판은 '요약을 만들려고 스크립트 텍스트가 OpenAI({요약 모델})로 전송됩니다. 영상은 전송되지 않아요.'이다. {요약 모델}은 UI-5에서 고른 요약 모델 이름이다.
- 받아쓰기 필요 판의 5는 '받아쓰기에는 음성 조각이, 요약에는 스크립트 텍스트가 OpenAI로 전송됩니다. 영상 파일 자체는 이 PC 밖으로 나가지 않아요.'이다.
- 자막 없는 YouTube의 5 문구는 보드가 없어 디자인 보강을 기다린다(VA-UI-001 8장).
- 닫는 길은 넷이고 모두 취소다(6.3을 누르기 전까지): 1.3, 6.2, Esc, 덮개 누름. 아무것도 전송하지 않고 UI-1로 돌아가며, 뒤 페이지는 넣은 주소와 고른 파일까지 그대로 남는다.
- 취소한 영상은 작업이 없어 UI-1 목록에 올라가지 않는다. 같은 영상을 다시 넣으면 처음 넣은 영상처럼 이 다이얼로그가 다시 열린다.
- 열리면 처음 초점은 6.3이다. 초점은 다이얼로그 밖으로 나가지 않고, 닫히면 이 다이얼로그를 연 UI-1 분석 버튼으로 돌아간다.
- 다이얼로그는 주소를 바꾸지 않는다. 새로 고치면 닫히고 UI-1이 열린다.
- 6.3을 누르면 분석이 시작되고 영상이 곧바로 UI-1 목록에 올라가며 UI-3이 열린다. UI-3 단계 목록은 그 출처에 필요한 단계만 보인다.
- 6.3을 누른 뒤 UI-3이 열릴 때까지 6.3을 다시 누를 수 없고, 1.3·6.2·Esc·덮개 누름으로도 닫히지 않는다. 시작 요청이 실패하면 잠금을 풀고 다이얼로그를 그대로 둔다. 실패를 알리는 자리와 모양은 보드에 없어 디자인 보강을 기다린다 (VA-UI-001에 없음).
- 다른 영상이 분석 중이거나 대기 중이면 6.1에 대기 안내를 보인다. 6.3은 그대로 켜져 있고 문구도 '분석 시작'이다. 누르면 영상이 대기열에 들어가 UI-1 목록에 대기 중 행으로 올라가고 UI-3이 대기 상태로 열린다(VA-UI-001 7장 16, [[VA-UC-001#UC-H0]] 3b). 예상 시간(3.1)은 이 영상만의 값이고 기다리는 시간은 더하지 않는다.
- 6.1을 보일지는 다이얼로그를 열 때의 상태로 정한다. 열어 둔 사이에 앞 영상이 끝나면 6.1이 남아 있어도 6.3을 눌렀을 때 바로 시작된다 (VA-UI-001에 없음)
- 6.1의 근거는 UI-1 목록(6)이다 — 다이얼로그를 열 때 목록에 진행 중이거나 대기 중인 행이 하나라도 있으면 보인다. 사전 안내에 쓰는 영상 정보와 예상치에는 다른 영상의 상태가 없어서다 (VA-UI-001에 없음)
- 시작할 수 없는 영상(정보 조회 실패·3시간 초과·음성 트랙 없음·영상·음성 파일이 아님)이면 1~6 대신 7을 보인다. 이유(7.1)·길이(7.2)·닫기(7.3)만 있고 분석 시작 버튼은 없다.
- 7.1은 VA-UI-001 4.5 문구 규칙대로 무엇이 왜 안 되는지 한 줄로 쓴다.
- 7.1이 7의 제목 자리에 서고 aria-labelledby로 이어진다. 1.1·1.2 같은 따로 된 제목·부제와 X 닫기는 7에 없다 (VA-UI-001에 없음).
- 7.1 문구 예는 정보 조회 실패 '영상 정보를 가져오지 못했어요 — {이유}' · 3시간 초과 '3시간이 넘는 영상은 분석할 수 없어요' · 음성 없음 '받아쓸 음성이 없는 파일이에요' · 파일 아님 '영상·음성 파일이 아닙니다'다 (VA-UI-001에 없음).
- 7.2는 2.4와 같은 '길이 {길이}' 메타 칩이고 길이를 알 때만 보인다. 정보 조회 실패나 파일이 아닐 때처럼 길이를 모르면 뺀다 (VA-UI-001에 없음).
- 7은 7.3·Esc·덮개 누름으로 닫히고 UI-1로 돌아간다. 아무것도 전송되지 않는다.
- 7이 열리면 처음 초점은 7.3이다 (VA-UI-001에 없음).
- 7의 모양은 캔버스에 없어 배치의 「시작 불가 판」 보드에 캔버스 부품으로 그렸다. [닫기]는 보조 버튼이다. 디자인 보강 때 확정한다(VA-UI-001 8장).

### 시나리오

**S-1 자막 있는 YouTube를 확인하고 시작한다** — [[VA-UC-001#UC-H1]] 기본 흐름 1~3 · [[VA-UC-001#UC-S1]] 기본 흐름 1~6
1. UI-1 「YouTube 링크」에 주소를 넣고 [분석]을 누른다. 버튼의 대기 표시가 끝나면 이 다이얼로그가 열리고 초점은 분석 시작(6.3)에 있다.
2. 영상 카드(2)에서 제목(2.2), 'YouTube · {채널}'(2.3), '길이 50:12'(2.4), 청록 '자막 있음 · 한국어'(2.5)를 보고 고른 영상이 맞는지 확인한다.
3. 예상 시간(3.1)은 '약 1분'이고 설명(3.2)이 받아쓰기 없이 자막을 쓴다고 알린다.
4. 예상 비용(4.1)은 '약 $0.02'다. 받아쓰기 줄(4.2)이 $0.00이라 비용이 요약 줄(4.3)에서만 나온다는 것을 안다.
5. 전송 안내(5)에서 스크립트 텍스트만 요약 모델로 가고 영상은 가지 않는다는 것을 읽는다.
6. 분석 시작(6.3)을 누른다. 영상이 목록에 올라가고 UI-3이 자막 가져오기 → 핵심 요약 → 챕터 → 추천 질문 단계로 열린다.

**S-2 로컬 파일의 받아쓰기 비용을 보고 시작한다** — [[VA-UC-001#UC-H2]] 기본 흐름 1~3 · [[VA-UC-001#UC-S1]] 기본 흐름 5~6
1. UI-1 「내 파일」에서 inbox 파일 하나를 고르고 [선택한 파일 분석]을 누른다. 받아쓰기 필요 판이 열린다.
2. 썸네일 자리(2.1)는 필름 아이콘, 제목(2.2)은 파일 이름, 출처 줄(2.3)은 '로컬 파일 · inbox', 자막 칩(2.5)은 회색 '자막 없음 · 받아쓰기 필요'다.
3. 예상 시간(3.1)은 '약 8분', 설명(3.2)은 '음성을 뽑아 30개 조각으로 나누고, 3개씩 동시에 받아씁니다.'다.
4. 받아쓰기 줄(4.2) '받아쓰기 150분 × $0.006' $0.90과 요약 줄(4.3) $0.02를 더한 합계(4.1)가 '약 $0.92'다. 비용 대부분이 받아쓰기라는 것을 본다.
5. 전송 안내(5)에서 음성 조각과 스크립트 텍스트는 OpenAI로 가고 영상 파일은 PC 밖으로 나가지 않는다는 것을 확인한다.
6. 분석 시작(6.3)을 누른다. UI-3이 음성 추출 → 받아쓰기 → 핵심 요약 → 챕터 → 추천 질문 단계로 열린다.

**S-3 비용을 보고 취소한다** — [[VA-UC-001#UC-H0]] 확장 3a
1. S-1이나 S-2처럼 다이얼로그가 열렸는데 예상 비용(4.1)이 생각보다 크다.
2. 취소(6.2)를 누른다. 닫기(1.3)·Esc·덮개 누름도 같다.
3. 아무것도 전송되지 않고 UI-1로 돌아간다. 넣은 주소나 고른 파일은 그대로이고 초점은 눌렀던 분석 버튼에 있다.
4. 이 영상은 목록에 올라가지 않는다. 나중에 다시 넣으면 이 다이얼로그가 처음처럼 열린다.

**S-4 자막 없는 YouTube** — [[VA-UC-001#UC-H1]] 확장 2b
1. UI-1에서 [분석]을 누른 YouTube 영상에 자막이 없다.
2. 받아쓰기 필요 판이 열린다. 출처 줄(2.3)은 'YouTube · {채널}', 자막 칩(2.5)은 회색 '자막 없음 · 받아쓰기 필요'다.
3. 설명(3.2)이 조각 수와 동시 수를, 받아쓰기 줄(4.2)이 '받아쓰기 {분}분 × ${단가}'와 금액을 보인다.
4. 분석 시작(6.3)을 누르면 UI-3이 음성 내려받기 → 받아쓰기 → 핵심 요약 → 챕터 → 추천 질문 단계로 열린다.

**S-5 3시간이 넘는 영상** — [[VA-UC-001#UC-H0]] 확장 2b · [[VA-UC-001#UC-S1]] 확장 2a
1. UI-1에서 길이가 3시간을 넘는 파일을 고르고 [선택한 파일 분석]을 누른다.
2. 사전 안내 대신 시작 불가 판(7)이 열린다. 이유(7.1)가 3시간이 넘어 분석할 수 없다고 알리고 길이 칩(7.2)이 영상 길이를 보인다.
3. 분석 시작 버튼은 없다. 닫기(7.3)를 누르면 UI-1로 돌아가고 아무것도 전송되지 않는다.

**S-6 정보를 가져올 수 없는 영상** — [[VA-UC-001#UC-H1]] 확장 2a · [[VA-UC-001#UC-S1]] 확장 1a
1. 비공개·삭제·지역 제한 영상의 주소로 [분석]을 누른다.
2. 시작 불가 판(7)이 열리고 이유(7.1)가 정보를 가져오지 못한 까닭을 알린다. 길이를 모르므로 길이 칩(7.2)은 없다.
3. 닫기(7.3)나 Esc로 UI-1로 돌아간다. 아무것도 전송되지 않는다.

**S-7 받아쓸 음성이 없거나 영상·음성 파일이 아니다** — [[VA-UC-001#UC-H2]] 확장 1a·2a
1. inbox에서 파일을 고르고 [선택한 파일 분석]을 누른다.
2. 음성 트랙이 없는 영상이면 시작 불가 판(7)의 이유(7.1)가 받아쓸 음성이 없다고 알리고 길이 칩(7.2)이 길이를 보인다.
3. 영상·음성 파일이 아니면 이유(7.1)가 '영상·음성 파일이 아닙니다'이고 길이 칩(7.2)은 없다.
4. 닫기(7.3)를 누르면 UI-1로 돌아간다.

**S-8 로컬 음성 파일** — [[VA-UC-001#UC-H2]] 확장 2b
1. UI-1 「내 파일」에서 mp3 파일을 고르고 [선택한 파일 분석]을 누른다. 받아쓰기 필요 판이 열린다.
2. 썸네일 자리(2.1)는 필름 아이콘, 출처 줄(2.3)은 '로컬 파일 · inbox', 자막 칩(2.5)은 회색 '자막 없음 · 받아쓰기 필요'다.
3. 설명(3.2)은 '{k}개 조각으로 나누고, {c}개씩 동시에 받아씁니다.'이고 '음성을 뽑아'가 없다. 전송 안내(5)는 '음성 파일 자체는 이 PC 밖으로 나가지 않아요.'로 끝난다.
4. 분석 시작(6.3)을 누르면 UI-3이 받아쓰기 → 핵심 요약 → 챕터 → 추천 질문 단계로 열린다.

**S-9 다른 영상이 분석 중일 때 시작한다** — [[VA-UC-001#UC-H0]] 확장 3b
1. 로컬 파일 하나가 받아쓰기 중이다. UI-1에 YouTube 주소를 넣고 [분석]을 누르면 이 다이얼로그가 열린다.
2. 버튼 줄 왼쪽 대기 안내(6.1)에 '지금 다른 영상을 분석 중이에요. 시작하면 차례를 기다렸다가 저절로 시작돼요.'가 보인다. 예상 시간(3.1)과 예상 비용(4.1)은 이 영상만의 값이다.
3. 분석 시작(6.3)을 누른다. 영상이 UI-1 목록에 '대기 중 · 1번째'로 올라가고 UI-3이 대기 상태로 열린다.

---

## UI-3 분석 진행

| 항목 | 내용 |
|---|---|
| 화면 설계 | [[VA-UI-001#UI-3]] |
| 경로 | `/videos/{id}/progress` |
| 디자인 보드 | Progress · ProgressLocal · ProgressFailed |
| 진입 | UI-2 [분석 시작] · UI-1 진행 중·실패 행 · UI-1에 진행 중·실패 영상을 다시 넣음 · UI-4 주소인데 결과가 아직 없음(진행 중·실패) · 주소로 바로(새로 고침) · 다시 시도 5.4(자기 자신) |
| 유스케이스 | [[VA-UC-001#UC-S6]] 기본 흐름 1~3, 확장 1a · [[VA-UC-001#UC-S2]] 기본 흐름 1~2, 확장 1a~1d · [[VA-UC-001#UC-S3]] 기본 흐름 3, 확장 3a·3b · [[VA-UC-001#UC-S4]] 기본 흐름 1~6, 확장 1b~4b · [[VA-UC-001#UC-H0]] 기본 흐름 4~8, 확장 4a~6a · [[VA-UC-001#UC-H1]] 기본 흐름 3 · [[VA-UC-001#UC-H2]] 기본 흐름 3 · [[VA-UC-001#UC-H5]] 기본 흐름 1~2 · [[VA-UC-001#UC-S5]] 기본 흐름 1 |

### 배치

```html
<!-- 주 보드: 캔버스 ProgressLocal(로컬 영상 · 받아쓰기 12/30). 아래는 상태 보드 -->
<div style="width: 1440px; height: 1040px; box-sizing: border-box; background: #F6F4EF; display: flex; flex-direction: column; overflow: hidden;">
<header style="height: 64px; flex-shrink: 0; box-sizing: border-box; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2DDD3; background: #F6F4EF;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 10px; color: #1B1A17; text-decoration: none;">
<span style="width: 30px; height: 30px; border-radius: 8px; background: #1B1A17; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="#F6F4EF" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;">Video Agent</span>
</a>
<nav aria-label="주 메뉴" style="display: flex; align-items: center; gap: 4px;">
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; border-radius: 10px; color: #4A463F; font-size: 15px; font-weight: 600; text-decoration: none;">분석한 영상</a>
<a href="#" aria-label="설정" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 7h-9"></path><path d="M14 17H5"></path><circle cx="17" cy="17" r="3"></circle><circle cx="7" cy="7" r="3"></circle></svg>
</a>
</nav>
</header>
<main style="flex-grow: 1; min-height: 0; box-sizing: border-box; padding: 28px 260px 0; display: flex; flex-direction: column; gap: 24px;">
<a data-el="1" href="#" style="align-self: flex-start; height: 44px; display: flex; align-items: center; gap: 6px; color: #4A463F; font-size: 15px; text-decoration: none;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>
분석한 영상
</a>
<div data-el="2" style="display: flex; align-items: center; gap: 14px;">
<span data-el="2.1" style="width: 44px; height: 44px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<div style="min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span data-el="2.2" style="font-size: 18px; font-weight: 600;">workshop_0912.mp4</span>
<span data-el="2.3" style="font-size: 14px; color: #5E5A52;">로컬 파일 · 2:30:00 · 자막 없음</span>
</div>
</div>
<section aria-live="polite" data-el="3" style="box-sizing: border-box; padding: 32px; border-radius: 18px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 26px;">
<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 24px;">
<div style="display: flex; flex-direction: column; gap: 8px;">
<h1 data-el="3.1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 34px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em; color: #1B1A17;">받아쓰기 중</h1>
<span data-el="3.2" style="font-size: 16px; color: #4A463F;">조각 12 / 30 · 남은 시간 약 5분</span>
</div>
<span data-el="3.3" style="font-family: 'IBM Plex Mono', monospace; font-size: 40px; line-height: 1; font-weight: 600; color: #0F6E68;">38%</span>
</div>
<div data-el="3.4" style="height: 8px; border-radius: 4px; background: #EFECE5; overflow: hidden;">
<div style="width: 38%; height: 8px; border-radius: 4px; background: #0F6E68;"></div>
</div>
<ol data-el="4" style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column;">
<li data-el="4.1" style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span data-el="4.2" style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; background: #0F6E68; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" aria-hidden="true" style="stroke-width: 3; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 6 9 17l-5-5"></path></svg>
</span>
<span data-el="4.5" style="width: 2px; flex-grow: 1; min-height: 18px; background: #0F6E68; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span data-el="4.3" style="font-size: 17px; font-weight: 500; color: #1B1A17;">음성 추출</span>
<span data-el="4.4" style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">18초</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span class="va-pulse" style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
<span style="width: 10px; height: 10px; border-radius: 50%; background: #0F6E68; display: block;"></span>
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 600; color: #1B1A17;">받아쓰기</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #0F6E68;">12 / 30</span>
</span>
<span style="display: flex; flex-direction: column; gap: 10px;">
<span role="img" aria-label="조각 30개 중 12개 완료, 3개 받아쓰는 중" data-el="4.6" style="display: grid; grid-template-columns: repeat(15, minmax(0, 1fr)); gap: 4px;">
<span data-el="4.7" style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span class="va-pulse" style="height: 18px; border-radius: 4px; background: #8FC7BE; display: block;"></span>
<span class="va-pulse" style="height: 18px; border-radius: 4px; background: #8FC7BE; display: block;"></span>
<span class="va-pulse" style="height: 18px; border-radius: 4px; background: #8FC7BE; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
</span>
<span data-el="4.8" style="display: flex; flex-wrap: wrap; gap: 18px; font-size: 13px; color: #5E5A52;">
<span style="display: flex; align-items: center; gap: 6px;">
<span style="width: 10px; height: 10px; border-radius: 3px; background: #0F6E68; display: block;"></span>
완료 12
</span>
<span style="display: flex; align-items: center; gap: 6px;">
<span style="width: 10px; height: 10px; border-radius: 3px; background: #8FC7BE; display: block;"></span>
받아쓰는 중 3
</span>
<span style="display: flex; align-items: center; gap: 6px;">
<span style="width: 10px; height: 10px; border-radius: 3px; background: #E2DDD3; display: block;"></span>
대기 15
</span>
</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">핵심 요약</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">챕터</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">추천 질문</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
</ol>
</section>
<div data-el="6" style="display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 14px; color: #5E5A52;">
<span data-el="6.1" style="display: flex; align-items: center; gap: 8px;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7 7h10v10"></path><path d="M7 17 17 7"></path></svg>
음성 조각 → OpenAI whisper-1 · 동시 3개
</span>
<span data-el="6.2">이 화면을 닫아도 분석은 계속돼요.</span>
</div>
</main>
</div>
<div class="var"><b>요약 중</b> — 자막 있는 YouTube, 단계 넷. 조각 격자가 없다 · 캔버스 Progress 보드</div>
<div class="crop" style="width: 1440px; padding: 0 0 28px;">
<main style="flex-grow: 1; min-height: 0; box-sizing: border-box; padding: 28px 260px 0; display: flex; flex-direction: column; gap: 24px;">
<a href="#" style="align-self: flex-start; height: 44px; display: flex; align-items: center; gap: 6px; color: #4A463F; font-size: 15px; text-decoration: none;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>
분석한 영상
</a>
<div style="display: flex; align-items: center; gap: 14px;">
<span style="width: 44px; height: 44px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<div style="min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 18px; font-weight: 600;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</span>
<span style="font-size: 14px; color: #5E5A52;">YouTube · 50:12 · 자막 있음</span>
</div>
</div>
<section aria-live="polite" style="box-sizing: border-box; padding: 32px; border-radius: 18px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 26px;">
<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 24px;">
<div style="display: flex; flex-direction: column; gap: 8px;">
<h1 style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 34px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em; color: #1B1A17;">핵심 요약을 만드는 중</h1>
<span style="font-size: 16px; color: #4A463F;">4단계 중 2단계 · 남은 시간 약 30초</span>
</div>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 40px; line-height: 1; font-weight: 600; color: #0F6E68;">55%</span>
</div>
<div style="height: 8px; border-radius: 4px; background: #EFECE5; overflow: hidden;">
<div style="width: 55%; height: 8px; border-radius: 4px; background: #0F6E68;"></div>
</div>
<ol style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column;">
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; background: #0F6E68; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" aria-hidden="true" style="stroke-width: 3; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 6 9 17l-5-5"></path></svg>
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #0F6E68; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #1B1A17;">자막 가져오기</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">3초</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span class="va-pulse" style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
<span style="width: 10px; height: 10px; border-radius: 50%; background: #0F6E68; display: block;"></span>
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 600; color: #1B1A17;">핵심 요약</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #0F6E68;">진행 중</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">챕터</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">추천 질문</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
</ol>
</section>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 14px; color: #5E5A52;">
<span style="display: flex; align-items: center; gap: 8px;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7 7h10v10"></path><path d="M7 17 17 7"></path></svg>
스크립트 텍스트 → OpenAI gpt-5-mini
</span>
<span>끝나면 결과 화면이 바로 열려요. 닫아도 분석은 계속됩니다.</span>
</div>
</main>
</div>
<div class="var"><b>실패</b> — 받아쓰기가 16번째 조각에서 멈췄을 때. 실패 알림(5) · 캔버스 ProgressFailed 보드</div>
<div class="crop" style="width: 1440px; padding: 0 0 28px;">
<main style="flex-grow: 1; min-height: 0; box-sizing: border-box; padding: 28px 260px 0; display: flex; flex-direction: column; gap: 24px;">
<a href="#" style="align-self: flex-start; height: 44px; display: flex; align-items: center; gap: 6px; color: #4A463F; font-size: 15px; text-decoration: none;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>
분석한 영상
</a>
<div style="display: flex; align-items: center; gap: 14px;">
<span style="width: 44px; height: 44px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<div style="min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 18px; font-weight: 600;">meetup_0901.mp4</span>
<span style="font-size: 14px; color: #5E5A52;">로컬 파일 · 1:58:20 · 자막 없음</span>
</div>
</div>
<section aria-live="polite" style="box-sizing: border-box; padding: 32px; border-radius: 18px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 26px;">
<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 24px;">
<div style="display: flex; flex-direction: column; gap: 8px;">
<h1 style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 34px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em; color: #7A2A1E;">받아쓰기가 멈췄어요</h1>
<span style="font-size: 16px; color: #4A463F;">조각 16 / 24에서 실패 · 완료한 15개는 저장됨</span>
</div>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 40px; line-height: 1; font-weight: 600; color: #A33A2B;">41%</span>
</div>
<div style="height: 8px; border-radius: 4px; background: #EFECE5; overflow: hidden;">
<div style="width: 41%; height: 8px; border-radius: 4px; background: #A33A2B;"></div>
</div>
<ol style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column;">
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; background: #0F6E68; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" aria-hidden="true" style="stroke-width: 3; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 6 9 17l-5-5"></path></svg>
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #0F6E68; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #1B1A17;">음성 추출</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">14초</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #A33A2B; background: #A33A2B; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" aria-hidden="true" style="stroke-width: 3; stroke-linecap: round; stroke-linejoin: round;"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 600; color: #1B1A17;">받아쓰기</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #A33A2B;">16 / 24에서 멈춤</span>
</span>
<span style="display: flex; flex-direction: column; gap: 10px;">
<span role="img" aria-label="조각 24개 중 15개 완료, 1개 실패" style="display: grid; grid-template-columns: repeat(15, minmax(0, 1fr)); gap: 4px;">
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #0F6E68; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #A33A2B; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
<span style="height: 18px; border-radius: 4px; background: #E2DDD3; display: block;"></span>
</span>
<span style="display: flex; flex-wrap: wrap; gap: 18px; font-size: 13px; color: #5E5A52;">
<span style="display: flex; align-items: center; gap: 6px;">
<span style="width: 10px; height: 10px; border-radius: 3px; background: #0F6E68; display: block;"></span>
완료 15
</span>
<span style="display: flex; align-items: center; gap: 6px;">
<span style="width: 10px; height: 10px; border-radius: 3px; background: #A33A2B; display: block;"></span>
실패 1
</span>
<span style="display: flex; align-items: center; gap: 6px;">
<span style="width: 10px; height: 10px; border-radius: 3px; background: #E2DDD3; display: block;"></span>
대기 8
</span>
</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">핵심 요약</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">챕터</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">추천 질문</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
</ol>
<div role="alert" data-el="5" style="box-sizing: border-box; padding: 20px; border-radius: 14px; background: #F7E6E2; display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: flex-start; gap: 12px;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#A33A2B" aria-hidden="true" style="flex-shrink: 0; margin-top: 2px; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4"></path><path d="M12 16h.01"></path></svg>
<div style="display: flex; flex-direction: column; gap: 4px;">
<span data-el="5.1" style="font-size: 16px; font-weight: 600; color: #7A2A1E;">OpenAI API에 연결하지 못했어요</span>
<span data-el="5.2" style="font-size: 14px; line-height: 1.6; color: #5C2418;">16번째 조각을 3번 다시 보냈지만 네트워크 시간 초과로 실패했습니다. 완료한 15개 조각은 저장돼 있어 처음부터 다시 받아쓰지 않아요.</span>
</div>
</div>
<div style="display: flex; justify-content: flex-end; gap: 10px;">
<a data-el="5.3" href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">목록으로</a>
<a data-el="5.4" href="#" style="height: 44px; box-sizing: border-box; padding: 0 20px; display: flex; align-items: center; gap: 8px; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg>
16번째 조각부터 다시 시도
</a>
</div>
</div>
</section>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 14px; color: #5E5A52;">
<span style="display: flex; align-items: center; gap: 8px;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7 7h10v10"></path><path d="M7 17 17 7"></path></svg>
음성 조각 → OpenAI whisper-1
</span>
<span>다시 시도하면 16번째 조각부터 이어서 받아씁니다.</span>
</div>
</main>
</div>
<div class="var"><b>대기 중</b> — 다른 영상이 분석 중이라 차례를 기다릴 때. 단계는 모두 대기, 남은 시간 없음 · 캔버스에 없음</div>
<div class="crop" style="width: 1440px; padding: 0 0 28px;">
<main style="flex-grow: 1; min-height: 0; box-sizing: border-box; padding: 28px 260px 0; display: flex; flex-direction: column; gap: 24px;">
<a href="#" style="align-self: flex-start; height: 44px; display: flex; align-items: center; gap: 6px; color: #4A463F; font-size: 15px; text-decoration: none;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>
분석한 영상
</a>
<div style="display: flex; align-items: center; gap: 14px;">
<span style="width: 44px; height: 44px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<div style="min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 18px; font-weight: 600;">벡터 검색 튜닝 실전</span>
<span style="font-size: 14px; color: #5E5A52;">YouTube · 38:05 · 자막 있음</span>
</div>
</div>
<section aria-live="polite" style="box-sizing: border-box; padding: 32px; border-radius: 18px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 26px;">
<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 24px;">
<div style="display: flex; flex-direction: column; gap: 8px;">
<h1 style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 34px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em; color: #1B1A17;">차례를 기다리는 중</h1>
<span style="font-size: 16px; color: #4A463F;">앞 영상 1개가 끝나면 시작해요</span>
</div>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 40px; line-height: 1; font-weight: 600; color: #0F6E68;">0%</span>
</div>
<div style="height: 8px; border-radius: 4px; background: #EFECE5; overflow: hidden;">
<div style="width: 0%; height: 8px; border-radius: 4px; background: #0F6E68;"></div>
</div>
<ol style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column;">
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">자막 가져오기</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">핵심 요약</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
<span style="width: 2px; flex-grow: 1; min-height: 18px; background: #E2DDD3; display: block;"></span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">챕터</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
<li style="display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 16px;">
<span style="display: flex; flex-direction: column; align-items: center;">
<span style="width: 28px; height: 28px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; background: #FFFFFF; display: flex; align-items: center; justify-content: center;">
</span>
</span>
<span style="box-sizing: border-box; padding: 2px 0 20px; display: flex; flex-direction: column; gap: 12px;">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<span style="font-size: 17px; font-weight: 500; color: #6B665C;">추천 질문</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #6B665C;">—</span>
</span>
</span>
</li>
</ol>
</section>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 14px; color: #5E5A52;">
<span style="display: flex; align-items: center; gap: 8px;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7 7h10v10"></path><path d="M7 17 17 7"></path></svg>
아직 OpenAI로 보내는 것이 없어요
</span>
<span>이 화면을 닫아도 차례가 되면 시작돼요.</span>
</div>
</main>
</div>
```

### 요소

| # | 이름 | 종류 | 보여주는 것 | 누르면 |
|---|---|---|---|---|
| 1 | 뒤로 링크 | 링크 | '← 분석한 영상'. 본문 맨 위 | [[#UI-1]] |
| 2 | 영상 머리 | 영역 | 지금 분석 중인 영상. 출처 아이콘·제목·부제 | — |
| 2.1 | 출처 아이콘 | 아이콘 | 아이콘 타일 안에 YouTube면 링크, 로컬 파일이면 필름 | — |
| 2.2 | 영상 제목 | 텍스트 | YouTube 영상 제목 또는 파일 이름 | — |
| 2.3 | 영상 부제 | 텍스트 | '{출처} · {길이} · {자막 있음 또는 자막 없음}'. 출처는 'YouTube' 또는 '로컬 파일' | — |
| 3 | 진행 카드 | 영역 | 헤드라인·부제·퍼센트·막대, 단계 목록(4), 실패 때 실패 알림(5)을 담는 카드. 바뀐 내용을 aria-live polite로 알린다 | — |
| 3.1 | 헤드라인 | 텍스트 | 지금 하는 일 한 줄. '핵심 요약을 만드는 중' / '받아쓰기 중' / 대기 때 '차례를 기다리는 중' / 실패 때 '받아쓰기가 멈췄어요' / 보드에 없는 단계는 같은 말투(예 '음성을 추출하는 중') / 받아쓰기가 아닌 단계 실패 때 '{단계} 단계가 멈췄어요' | — |
| 3.2 | 진행 부제 | 텍스트 | 정상: '{단계 수}단계 중 {i}단계 · 남은 시간 {남은}' 또는 '조각 {n} / {m} · 남은 시간 {남은}'. 대기: '앞 영상 {n}개가 끝나면 시작해요'. 실패: '조각 {k} / {m}에서 실패 · 완료한 {j}개는 저장됨' / 받아쓰기가 아닌 단계 실패: '{단계 수}단계 중 {i}단계에서 실패'(보존된 것이 있으면 ' · 스크립트는 저장됨') | — |
| 3.3 | 퍼센트 | 텍스트 | 전체 진행률 '{p}%'. 오른쪽 위 큰 숫자 | — |
| 3.4 | 진행 막대 | 막대 | 3.3과 같은 값만큼 채운 큰 진행 막대 | — |
| 4 | 단계 목록 | 목록 | 이 출처에 필요한 단계만 순서대로. 넷 또는 다섯 | — |
| 4.1 | 단계 행 | 행 | 단계 하나. 왼쪽에 단계 표시와 연결선, 오른쪽에 이름과 메모 | — |
| 4.2 | 단계 표시 | 표시 | 완료(체크) / 진행 중(가운데 점, 깜빡임) / 실패(X) / 대기(빈 원) | — |
| 4.3 | 단계 이름 | 텍스트 | '자막 가져오기' · '음성 내려받기' · '음성 추출' · '받아쓰기' · '핵심 요약' · '챕터' · '추천 질문'. 진행 중·실패면 굵게 | — |
| 4.4 | 단계 메모 | 텍스트 | 완료: 걸린 시간 '18초' / 진행 중: '진행 중' 또는 '{n} / {m}' / 실패: '{k} / {m}에서 멈춤'(조각 없는 단계는 '멈춤') / 대기: '—' | — |
| 4.5 | 연결선 | 선 | 다음 단계로 잇는 세로선. 마지막 행에는 없다 | — |
| 4.6 | 조각 격자 | 격자 | 받아쓰기 행 아래. 조각 하나가 칸 하나, 한 줄 15칸. role img와 글 설명 '조각 {m}개 중 {n}개 완료, {c}개 받아쓰는 중' | — |
| 4.7 | 조각 칸 | 칸 | 완료 / 받아쓰는 중(깜빡임) / 실패 / 대기 | — |
| 4.8 | 범례 | 목록 | 견본 + '완료 {n}' · '받아쓰는 중 {c}' · '실패 {f}' · '대기 {w}' | — |
| 5 | 실패 알림 | 상자 | 공통 1.6 실패 알림. 실패 상태에서만 단계 목록 아래에 뜬다 | — |
| 5.1 | 알림 제목 | 텍스트 | 무엇이 안 됐는지. 예 'OpenAI API에 연결하지 못했어요' | — |
| 5.2 | 알림 본문 | 텍스트 | 어느 조각을 몇 번 다시 보냈고 왜 실패했는지, 무엇이 저장됐는지. 예 '{k}번째 조각을 3번 다시 보냈지만 네트워크 시간 초과로 실패했습니다. 완료한 {j}개 조각은 저장돼 있어 처음부터 다시 받아쓰지 않아요.' | — |
| 5.3 | 목록으로 | 버튼 | 공통 1.8의 보조 버튼 '목록으로' | [[#UI-1]]. 작업은 실패 상태로 남는다 |
| 5.4 | 다시 시도 | 버튼 | 공통 1.8의 주 버튼. 새로고침 아이콘 + '{r}번째 조각부터 다시 시도' 또는 '{단계}부터 다시 시도' | 같은 작업을 이어서 시작. 5가 사라지고 이 화면이 진행 중 상태로 바뀐다. 키가 없으면 [[#UI-5]] |
| 6 | 카드 아래 줄 | 영역 | 왼쪽 전송 표시, 오른쪽 떠나기 안내 | — |
| 6.1 | 전송 표시 | 텍스트 | 오른쪽 위 화살표 아이콘 + 지금 무엇을 어느 모델로 보내는지. '음성 조각 → OpenAI {받아쓰기 모델} · 동시 {c}개' / '스크립트 텍스트 → OpenAI {요약 모델}' / 보내는 것이 없는 단계: '아직 OpenAI로 보내는 것이 없어요' | — |
| 6.2 | 떠나기 안내 | 텍스트 | '끝나면 결과 화면이 바로 열려요. 닫아도 분석은 계속됩니다.' / '이 화면을 닫아도 분석은 계속돼요.' / 실패 때 '다시 시도하면 {r}번째 조각부터 이어서 받아씁니다.' / 받아쓰기가 아닌 단계 실패 때 '다시 시도하면 {단계}부터 이어서 합니다.' | — |

### 규칙

- 진행 내용은 1초마다 서버에서 새로 받아 3·4·6을 바꾼다. 화면을 닫거나 떠나도 분석은 서버에서 계속된다([[VA-INFRA-001]] 3절).
- 분석이 끝나면 UI-4를 저절로 연다. 결과로 가는 버튼은 없다. 이때 방문 기록을 바꿔치기해서 뒤로 가기가 이 화면으로 돌아오지 않게 한다.
- 이 주소로 들어왔는데 작업이 이미 끝났으면 UI-4로 넘긴다. 이때도 방문 기록을 바꿔치기한다.
- 영상이 없거나(그 사이 지워짐) 분석 작업이 없는 영상이면 UI-1로 넘긴다 (VA-UI-001에 없음)
- 분석 취소·중지 버튼은 없다. 멈추려면 UI-6에서 그 영상을 지운다. 대기 중인 영상도 같다.
- 대기 상태: 다른 영상이 분석 중이라 차례를 기다리는 동안이다(VA-UI-001 7장 16, [[VA-UC-001#UC-H0]] 3b). 3.1은 '차례를 기다리는 중', 3.2는 '앞 영상 {n}개가 끝나면 시작해요'이고 남은 시간은 보이지 않는다. 3.3은 '0%', 3.4는 빈 막대다. 색은 정상 상태와 같다.
- 대기 상태의 {n}은 이 영상보다 먼저 돌 영상 수다 — 지금 도는 영상 하나와 앞에서 기다리는 영상들. 그래서 UI-1 상태 글자 '대기 중 · {k}번째'의 k와 같다.
- 대기 상태의 단계 목록 4는 출처에 필요한 단계를 모두 대기(빈 원, 4.4 '—')로 보인다. 4.6·4.8과 5는 없다. 6.1은 '아직 OpenAI로 보내는 것이 없어요', 6.2는 '이 화면을 닫아도 차례가 되면 시작돼요.'다.
- 대기 상태에서도 1초마다 새로 받는다. 앞 영상이 끝나 차례가 오면 주소는 그대로이고 같은 화면이 첫 단계 진행 중으로 바뀐다. 앞 영상이 실패해도 차례는 온다 — 실패한 작업은 대기열을 막지 않는다.
- 뒤로 링크(1)와 목록으로(5.3)는 UI-1로 간다. 헤더의 두 메뉴는 이 화면에서 현재 위치로 표시하지 않는다.
- API 키가 없거나 확인에 실패한 동안 헤더 위에 공통 1.4 키 없음 배너를 두고, 배너의 [키 넣으러 가기]는 UI-5로 간다. 모양과 문구는 VA-UI-001 4.5절을 따른다.
- API 키가 없거나 확인에 실패한 동안 5.4는 공통 1.8의 막힌 주 버튼(aria-disabled)이다. 초점은 받고, 누르면 UI-5로 간다. 문구는 그대로다. 배너가 연결 문구일 때는 5.4를 막지 않는다 — 누르면 키를 다시 확인하고 이어 간다(공통 1.4) (VA-UI-001에 없음)
- 2.1은 YouTube면 링크 아이콘, 로컬 파일이면 필름 아이콘이다. 2.3의 길이는 VA-UI-001 4.4절 형식(1시간 미만 mm:ss, 1시간 이상 h:mm:ss)을 따른다.
- 단계 목록 4는 출처에 필요한 단계만 보인다. 자막 있는 YouTube: 자막 가져오기 → 핵심 요약 → 챕터 → 추천 질문 · 자막 없는 YouTube: 음성 내려받기 → 받아쓰기 → 핵심 요약 → 챕터 → 추천 질문 · 로컬 영상 파일: 음성 추출 → 받아쓰기 → 핵심 요약 → 챕터 → 추천 질문 · 로컬 음성 파일: 받아쓰기 → 핵심 요약 → 챕터 → 추천 질문.
- 4.3은 작업 단계 값에서 온다. `download` = 자막이면 '자막 가져오기', 아니면 '음성 내려받기' · `extract` = '음성 추출' · `transcribe` = '받아쓰기' · `summarize` = '핵심 요약' · `chapter` = '챕터' · `suggest` = '추천 질문' · `pending` = 첫 단계가 진행 중인 모습(작업 상태가 대기면 대기 상태) · `done` = UI-4로 넘김 · `failed` = 실패 상태. 코드 값은 클래스 명세를 다시 쓸 때 맞춘다.
- 4.2는 넷이다. 완료 = 채운 원 + 체크, 4.4에 흐린 캡션 글자로 걸린 시간 · 진행 중 = 테두리 원 + 가운데 점, 깜빡임, 4.3 굵게, 4.4 청록 글자로 '진행 중' 또는 '{n} / {m}' · 실패 = 채운 빨간 원 + X, 4.3 굵게, 4.4 빨간 글자로 '{k} / {m}에서 멈춤'(조각 없는 단계는 '멈춤') · 대기 = 빈 원, 4.3·4.4 흐린 캡션 글자, 4.4 '—'. 모양은 VA-UI-001 4.2절 단계 표시, 색은 3.1절을 따른다.
- 4.5는 그 단계가 완료면 청록, 아니면 회색이고 마지막 단계에는 없다. 4.4의 시간과 조각 수는 누를 수 없는 고정폭 글자다. 2.3의 길이와 3.2의 조각 수·남은 시간은 일반 UI 글자다(VA-UI-001 4.4절).
- 3.1은 지금 단계를 말한다. 핵심 요약 단계는 '핵심 요약을 만드는 중', 받아쓰기 단계는 '받아쓰기 중', 받아쓰기 실패는 '받아쓰기가 멈췄어요'다.
- 보드에 없는 단계의 3.1은 같은 말투로 '자막을 가져오는 중' · '음성을 내려받는 중' · '음성을 추출하는 중' · '챕터를 만드는 중' · '추천 질문을 만드는 중'으로 쓴다 (VA-UI-001에 없음)
- 3.2는 정상일 때 남은 시간을 보인다. 받아쓰기 단계는 '조각 {n} / {m} · 남은 시간 {남은}', 핵심 요약 단계는 '{단계 수}단계 중 {i}단계 · 남은 시간 {남은}'이다.
- 받아쓰기가 아닌 나머지 단계(자막 가져오기·음성 내려받기·음성 추출·챕터·추천 질문)의 3.2도 '{단계 수}단계 중 {i}단계 · 남은 시간 {남은}' 형식을 쓴다 (VA-UI-001에 없음)
- {남은}은 1분 미만이면 '약 {s}초', 1분 이상이면 '약 {t}분'으로 적는다 (VA-UI-001에 없음)
- 숫자 규칙. 진행 중 '조각 {n} / {m}'과 4.4 '{n} / {m}'의 n은 완료한 조각 수다. 실패 때 '조각 {k} / {m}에서 실패'와 4.4 '{k} / {m}에서 멈춤'의 k는 실패한 조각 번호이고, 완료 수는 '완료한 {j}개는 저장됨'으로 따로 적는다. UI-1 목록 행도 같다.
- 받아쓰기 단계의 남은 시간 = 미완료 조각 수 × 지금까지 조각당 평균이다([[VA-UC-001#UC-S6]] 2번). 조각이 없는 단계의 남은 시간 계산은 아직 없고 MINISPEC에서 정한다.
- 3.3과 3.4는 같은 값이고, UI-1 진행 중 행의 작은 막대도 이 값을 쓴다. 조각 수와 동시 수도 서버 값을 그대로 보인다.
- 실패하면 3.3·3.4는 멈춘 때의 값을 그대로 둔다 (VA-UI-001에 없음)
- 4.6과 4.8은 받아쓰기 행 아래에만 붙는다. 조각 하나가 칸 하나(4.7)이고 한 줄에 15칸이다. 칸은 완료 · 받아쓰는 중(깜빡임) · 실패 · 대기 넷이고, 색은 VA-UI-001 4.2절 조각 칸을 따른다.
- 4.8에 상태별 칸 수를 적고, 4.6의 글 설명(aria-label)에 같은 내용을 글로 적는다. 예 '조각 {m}개 중 {n}개 완료, {c}개 받아쓰는 중' · '조각 {m}개 중 {j}개 완료, {f}개 실패'. 색만으로 전하지 않는다.
- 4.8은 칸이 하나 이상인 상태만 적는다. 보드의 진행 중 판에는 '실패'가, 실패 판에는 '받아쓰는 중'이 없다 (VA-UI-001에 없음)
- 받아쓰기가 끝난 뒤에도 4.6은 받아쓰기 행 아래에 모두 완료 칸으로 남는다 (VA-UI-001에 없음)
- 깜빡임은 진행 중인 4.2와 받아쓰는 중인 4.7 두 곳에만 붙는다. 운영체제에서 움직임 줄이기를 켜면 끈다(VA-UI-001 3.4절).
- 6.1은 지금 단계에서 무엇을 어느 모델로 보내는지 알린다. 받아쓰기 단계는 '음성 조각 → OpenAI {받아쓰기 모델} · 동시 {c}개', 핵심 요약·챕터·추천 질문 단계는 '스크립트 텍스트 → OpenAI {요약 모델}'이다. 전송 사실은 시작 전 UI-2와 진행 중인 여기에서 알린다.
- 받아쓰기 실패 상태의 6.1은 보내는 중인 조각이 없으므로 '· 동시 {c}개'를 뺀다. 보드 ProgressFailed 기준 (VA-UI-001에 없음)
- OpenAI로 보내는 것이 없는 단계(자막 가져오기·음성 내려받기·음성 추출)의 6.1은 '아직 OpenAI로 보내는 것이 없어요'로 쓴다 (VA-UI-001에 없음)
- 6.2는 요약 중 판에서 '끝나면 결과 화면이 바로 열려요. 닫아도 분석은 계속됩니다.', 받아쓰기 중 판에서 '이 화면을 닫아도 분석은 계속돼요.', 실패 때 '다시 시도하면 {r}번째 조각부터 이어서 받아씁니다.'다.
- 6.2의 정상 문구 둘은 핵심 요약·챕터·추천 질문 단계에서 '끝나면 결과 화면이 바로 열려요…'를, 그 앞 단계(자막 가져오기·음성 내려받기·음성 추출·받아쓰기)에서 '이 화면을 닫아도…'를 쓴다 (VA-UI-001에 없음)
- 실패하면 3.1·3.3·3.4가 빨강으로 바뀌고, 3.2는 남은 시간 대신 보존된 것을 알린다. 실패한 단계의 4.2가 X로 바뀌고, 받아쓰기 실패면 4.6에 실패 칸이 생기고, 4 아래에 5가 뜬다(role alert).
- 5.1은 무엇이 안 됐는지, 5.2는 어느 조각을 몇 번 다시 보냈고 왜 실패했는지와 무엇이 보존됐는지를 쓴다. 문구 규칙은 공통 1.6 실패 알림(VA-UI-001 4.5절)을 따른다.
- 한 조각은 자동으로 3번 다시 보낸 뒤 실패로 멈춘다. 이 횟수는 MINISPEC 값과 맞춘다.
- 5.4를 눌렀을 때 다른 영상이 분석 중이면 이 작업은 대기열 끝에 들어가고 화면은 대기 상태가 된다. 차례가 오면 멈춘 곳부터 이어 간다 (VA-UI-001에 없음)
- 5.4는 같은 작업을 이어간다([[VA-UC-001#UC-S3]] 3a3). 완료하지 않은 조각만 보내고, 5.4 문구와 6.2의 {r}은 완료하지 않은 첫 조각 번호다. 동시에 보내므로 실패한 조각 번호 {k}와 다를 수 있다. 누르면 주소는 그대로이고 5가 사라지며 진행 중 상태로 돌아간다.
- 핵심 요약·챕터·추천 질문 단계가 실패하면 같은 5에 '{단계}부터 다시 시도'를 둔다.
- 받아쓰기가 아닌 단계가 실패하면 3.1은 '{단계} 단계가 멈췄어요'다. 3.2는 '{단계 수}단계 중 {i}단계에서 실패'이고, 보존된 것이 있을 때만 뒤에 ' · 스크립트는 저장됨'을 붙인다(핵심 요약·챕터·추천 질문 단계). 그 단계의 4.4는 '멈춤'이다. 6.2는 '다시 시도하면 {단계}부터 이어서 합니다.'로 쓴다. 자막 가져오기·음성 내려받기·음성 추출 실패도 5.4는 '{단계}부터 다시 시도'다 (VA-UI-001에 없음)
- 5.4를 누른 뒤 서버가 받을 때까지 5.4를 다시 누를 수 없다 (VA-UI-001에 없음)
- 5.3으로 떠나도 작업은 실패 상태로 남는다. UI-1 실패 행을 누르면 이 화면이 실패 상태로 다시 열린다.

### 시나리오

**S-1 자막 있는 YouTube를 끝까지 지켜본다** — [[VA-UC-001#UC-H1]] 기본 흐름 3 · [[VA-UC-001#UC-H0]] 기본 흐름 4~8 · [[VA-UC-001#UC-S2]] 기본 흐름 1~2 · [[VA-UC-001#UC-S4]] 기본 흐름 1~6 · [[VA-UC-001#UC-S6]] 기본 흐름 1·3
1. UI-2 자막 있음 판에서 [분석 시작]을 누르면 이 화면이 열린다. 2.1은 링크 아이콘, 2.3은 'YouTube · 50:12 · 자막 있음'이다
2. 단계 목록(4)은 자막 가져오기 → 핵심 요약 → 챕터 → 추천 질문 넷이다. 첫 단계가 진행 중으로 시작한다
3. 자막 가져오기가 끝나면 그 행의 4.2가 체크, 4.4가 '3초'가 되고 연결선(4.5)이 완료 색으로 바뀐다
4. 핵심 요약이 진행 중이 된다. 3.1 '핵심 요약을 만드는 중', 3.2 '4단계 중 2단계 · 남은 시간 약 30초', 3.3 '55%', 그 행의 4.4 '진행 중'
5. 6.1은 '스크립트 텍스트 → OpenAI {요약 모델}', 6.2는 '끝나면 결과 화면이 바로 열려요. 닫아도 분석은 계속됩니다.'다
6. 1초마다 새 진행을 받아 챕터와 추천 질문이 차례로 완료된다
7. 추천 질문이 끝나면 UI-4가 저절로 열린다. 뒤로 가기를 눌러도 이 화면으로 돌아오지 않는다

**S-2 로컬 영상 파일을 받아쓴다** — [[VA-UC-001#UC-H2]] 기본 흐름 3 · [[VA-UC-001#UC-S2]] 확장 1b · [[VA-UC-001#UC-S3]] 기본 흐름 3, 확장 3b · [[VA-UC-001#UC-S6]] 기본 흐름 2~3
1. UI-2 받아쓰기 필요 판에서 [분석 시작]을 누르면 이 화면이 열린다. 2.1은 필름 아이콘, 2.2는 'workshop_0912.mp4', 2.3은 '로컬 파일 · 2:30:00 · 자막 없음'이다
2. 단계는 다섯이다. 음성 추출이 끝나 그 행의 4.4에 '18초'가 보인다
3. 받아쓰기가 진행 중이다. 3.1 '받아쓰기 중', 3.2 '조각 12 / 30 · 남은 시간 약 5분', 3.3 '38%', 받아쓰기 행의 4.4 '12 / 30'
4. 받아쓰기 행 아래 조각 격자(4.6)에 30칸이 두 줄로 보인다. 1~12번 완료, 13~15번 받아쓰는 중(깜빡임), 16~30번 대기다
5. 범례(4.8)는 '완료 12 · 받아쓰는 중 3 · 대기 15'이고, 4.6의 글 설명은 '조각 30개 중 12개 완료, 3개 받아쓰는 중'이다
6. 6.1은 '음성 조각 → OpenAI {받아쓰기 모델} · 동시 3개', 6.2는 '이 화면을 닫아도 분석은 계속돼요.'다
7. 조각이 끝날 때마다 칸이 완료로 바뀌고 3.2의 완료 수와 남은 시간, 3.3·3.4가 함께 바뀐다
8. 30개가 모두 끝나면 받아쓰기 행이 완료되고 핵심 요약이 진행 중이 된다. 4.6은 모두 완료 칸으로 남고, 6.1은 '스크립트 텍스트 → OpenAI {요약 모델}'로 바뀐다
9. 이후는 S-1의 6~7과 같다

**S-3 화면을 떠났다가 목록에서 다시 연다** — [[VA-UC-001#UC-S6]] 기본 흐름 1 · [[VA-UC-001#UC-S5]] 기본 흐름 1 · [[VA-UC-001#UC-H5]] 기본 흐름 1~2
1. 받아쓰기 중에 뒤로 링크(1)를 눌러 UI-1로 간다. 분석은 서버에서 계속된다
2. UI-1 목록 행에 '받아쓰기 중 · 14 / 30'과 작은 진행 막대가 보인다. 막대 값은 이 화면의 3.3과 같다
3. 그 행을 누르면 이 화면이 열리고 지금 진행이 바로 보인다
4. 같은 파일을 UI-1에서 다시 골라 분석을 눌러도 UI-2 없이 이 화면이 열린다
5. 새로 고치거나 주소로 들어왔을 때 분석이 이미 끝났으면 이 화면 대신 UI-4가 열린다
6. 결과 주소(UI-4)를 바로 열었는데 분석이 아직 진행 중이거나 실패 상태면 UI-4 대신 이 화면이 열린다

**S-4 받아쓰기가 멈추고 이어서 다시 시도한다** — [[VA-UC-001#UC-S3]] 확장 3a · [[VA-UC-001#UC-S6]] 확장 1a · [[VA-UC-001#UC-H0]] 확장 4a~6a
1. 16번째 조각을 자동으로 3번 다시 보냈지만 네트워크 시간 초과로 실패해 받아쓰기가 멈춘다
2. 3.1이 '받아쓰기가 멈췄어요', 3.2가 '조각 16 / 24에서 실패 · 완료한 15개는 저장됨'이 되고 3.1·3.3·3.4가 빨강으로 바뀐다. 3.3은 '41%'에 멈춰 있다
3. 받아쓰기 행의 4.2가 X, 4.4가 '16 / 24에서 멈춤'이다. 4.6은 1~15번 완료, 16번 실패, 17~24번 대기이고 4.8은 '완료 15 · 실패 1 · 대기 8'이다
4. 단계 목록 아래에 실패 알림(5)이 뜬다. 5.1 'OpenAI API에 연결하지 못했어요', 5.2는 16번째 조각을 3번 다시 보냈지만 시간 초과로 실패했고 완료한 15개는 저장돼 있다고 알린다
5. 6.1은 '음성 조각 → OpenAI {받아쓰기 모델}', 6.2는 '다시 시도하면 16번째 조각부터 이어서 받아씁니다.'다
6. 다시 시도(5.4) '16번째 조각부터 다시 시도'를 누른다. 같은 작업이 이어지고 완료하지 않은 조각만 보낸다
7. 5가 사라지고 3.1이 '받아쓰기 중'으로, 받아쓰기 행의 4.2가 진행 중으로 돌아간다. 1~15번 칸은 완료 그대로다

**S-5 실패한 채로 목록에 두었다가 나중에 이어 간다** — [[VA-UC-001#UC-S3]] 확장 3a · [[VA-UC-001#UC-H5]] 기본 흐름 1~2
1. 실패 상태에서 목록으로(5.3)를 누르면 UI-1로 간다. 작업은 실패 상태로 남는다
2. UI-1 목록 행에 '받아쓰기 16 / 24에서 멈춤'이 보인다
3. 나중에 그 행을 누르면 이 화면이 실패 상태 그대로 열린다
4. 다시 시도(5.4)를 누른다. 이후는 S-4의 7과 같다

**S-6 핵심 요약 단계가 멈춘다** — [[VA-UC-001#UC-S4]] 확장 1b~4b · [[VA-UC-001#UC-S6]] 확장 1a
1. 로컬 영상 파일의 받아쓰기는 끝났고 핵심 요약 호출이 재시도 뒤에도 실패한다
2. 핵심 요약 행의 4.2가 X, 4.4가 '멈춤'이 된다. 3.1은 '핵심 요약 단계가 멈췄어요', 3.2는 '5단계 중 3단계에서 실패 · 스크립트는 저장됨'이고 3.1·3.3·3.4가 빨강이다. 받아쓰기 행의 4.6은 모두 완료 칸 그대로다
3. 6.1은 '스크립트 텍스트 → OpenAI {요약 모델}', 6.2는 '다시 시도하면 핵심 요약부터 이어서 합니다.'다
4. 실패 알림(5)의 5.1·5.2가 무엇이 왜 안 됐는지와 스크립트가 저장돼 있다는 것을 알린다
5. 다시 시도(5.4)는 '핵심 요약부터 다시 시도'다. 누르면 받아쓰기를 다시 하지 않고 핵심 요약부터 이어 간다

**S-7 음성 추출이 멈춘다** — [[VA-UC-001#UC-S2]] 확장 1b·1d · [[VA-UC-001#UC-S6]] 확장 1a · [[VA-UC-001#UC-H0]] 확장 4a~6a
1. 로컬 영상 파일의 음성 추출이 진행 중이다. 3.1은 '음성을 추출하는 중', 6.1은 '아직 OpenAI로 보내는 것이 없어요', 6.2는 '이 화면을 닫아도 분석은 계속돼요.'다
2. 추출이 실패해 음성 추출 행의 4.2가 X, 4.4가 '멈춤'이 된다. 3.1은 '음성 추출 단계가 멈췄어요', 3.2는 보존된 것이 없어 '5단계 중 1단계에서 실패'다
3. 4 아래에 실패 알림(5)이 뜨고 5.1·5.2가 무엇이 왜 안 됐는지 알린다. 5.4는 '음성 추출부터 다시 시도', 6.2는 '다시 시도하면 음성 추출부터 이어서 합니다.'다
4. 5.4를 누르면 5가 사라지고 음성 추출 행의 4.2가 진행 중으로 돌아간다

**S-8 차례를 기다렸다가 시작된다** — [[VA-UC-001#UC-H0]] 확장 3b · [[VA-UC-001#UC-S6]] 기본 흐름 1
1. 다른 영상이 받아쓰기 중일 때 UI-2에서 [분석 시작]을 눌러 이 화면이 대기 상태로 열린다
2. 3.1은 '차례를 기다리는 중', 3.2는 '앞 영상 1개가 끝나면 시작해요', 3.3은 '0%'이고 3.4는 비어 있다. 단계 목록(4)의 네 행이 모두 대기(빈 원, '—')다
3. 6.1은 '아직 OpenAI로 보내는 것이 없어요', 6.2는 '이 화면을 닫아도 차례가 되면 시작돼요.'다
4. 뒤로 링크(1)로 UI-1에 가면 이 영상이 '대기 중 · 1번째' 행으로 보인다. 행을 누르면 이 화면이 다시 열린다
5. 앞 영상이 끝나면 같은 화면이 저절로 바뀐다. 3.1이 '자막을 가져오는 중'이 되고 첫 행의 4.2가 진행 중이 된다. 그 뒤는 S-1과 같다

---

## UI-4 결과

| 항목 | 내용 |
|---|---|
| 화면 설계 | [[VA-UI-001#UI-4]] |
| 경로 | `/videos/{id}` |
| 디자인 보드 | Result · ResultLong · ResultChat |
| 진입 | UI-3 끝남(자동) · UI-1 완료 행 · UI-1에서 이미 분석한 영상을 넣음 · UI-7 닫힘 · UI-6 취소 · 주소로 바로 |
| 유스케이스 | [[VA-UC-001#UC-H3]] 기본 흐름 1~6, 확장 3a, 4a (6a는 따르지 않음, VA-UI-001 8장) · [[VA-UC-001#UC-H4]] 기본 흐름 1~5, 확장 1a, 1b, 2a, 3a · [[VA-UC-001#UC-H5]] 기본 흐름 3, 확장 1a · [[VA-UC-001#UC-H6]] 기본 흐름 1~4, 확장 3a · [[VA-UC-001#UC-H7]] 기본 흐름 1~3 · [[VA-UC-001#UC-S2]] 기본 흐름 1~2, 확장 1a~1c (스크립트 출처) · [[VA-UC-001#UC-S4]] 기본 흐름 2~4, 확장 2a (요약·인사이트·챕터·추천 질문) |

### 배치

```html
<!-- 주 보드: 캔버스 Result(자막 있는 50분 발표 · [스크립트] 탭 · 12:40 선택). 오른쪽 패널은 창에 고정. 아래는 상태 보드 -->
<div style="width: 1440px; height: 2900px; box-sizing: border-box; background: #F6F4EF; display: flex; flex-direction: column;">
<header style="height: 64px; flex-shrink: 0; box-sizing: border-box; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2DDD3; background: #F6F4EF;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 10px; color: #1B1A17; text-decoration: none;">
<span style="width: 30px; height: 30px; border-radius: 8px; background: #1B1A17; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="#F6F4EF" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;">Video Agent</span>
</a>
<nav aria-label="주 메뉴" style="display: flex; align-items: center; gap: 4px;">
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; border-radius: 10px; color: #4A463F; font-size: 15px; font-weight: 600; text-decoration: none;">분석한 영상</a>
<a href="#" aria-label="설정" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 7h-9"></path><path d="M14 17H5"></path><circle cx="17" cy="17" r="3"></circle><circle cx="7" cy="7" r="3"></circle></svg>
</a>
</nav>
</header>
<div style="flex-grow: 1; display: grid; grid-template-columns: minmax(0, 1fr) 520px;">
<main style="min-width: 0; box-sizing: border-box; padding: 24px 64px 96px 96px; display: flex; flex-direction: column; gap: 48px;">
<div style="display: flex; flex-direction: column; gap: 18px;">
<div data-el="1" style="display: flex; align-items: center; justify-content: space-between; gap: 16px;">
<a data-el="1.1" href="#" style="height: 44px; display: flex; align-items: center; gap: 6px; color: #4A463F; font-size: 15px; text-decoration: none;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>
분석한 영상
</a>
<div style="display: flex; align-items: center; gap: 8px;">
<a data-el="1.2" href="#" style="height: 44px; box-sizing: border-box; padding: 0 16px; display: flex; align-items: center; gap: 8px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="m7 10 5 5 5-5"></path><path d="M12 15V3"></path></svg>
내보내기
</a>
<a data-el="1.3" href="#" aria-label="분석 결과 삭제" style="width: 44px; height: 44px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #A33A2B;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
</div>
<div data-el="2" style="display: flex; flex-direction: column; gap: 12px;">
<div data-el="2.1" style="display: flex; flex-wrap: wrap; gap: 6px;">
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">YouTube</span>
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">50:12</span>
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">자막 · 한국어</span>
</div>
<h1 data-el="2.2" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 36px; line-height: 1.3; font-weight: 600; letter-spacing: -0.02em;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</h1>
<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 14px; font-size: 15px; color: #5E5A52;">
<span data-el="2.3">[채널명] · 오늘 14:08 분석 · 요약 gpt-5-mini</span>
<a data-el="2.4" href="https://www.youtube.com/" style="display: flex; align-items: center; gap: 4px; color: #0F6E68; font-weight: 600; text-decoration: none;">
원본 영상 열기
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M15 3h6v6"></path><path d="M10 14 21 3"></path><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path></svg>
</a>
</div>
</div>
</div>
<section aria-labelledby="tldr-title" data-el="3" style="display: flex; flex-direction: column; gap: 10px;">
<h2 id="tldr-title" style="margin: 0; font-size: 14px; font-weight: 600; color: #5E5A52;">한 줄 요약</h2>
<p style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; line-height: 1.6; font-weight: 500; letter-spacing: -0.01em; color: #1B1A17;">RAG 서비스를 1년간 운영하며 겪은 검색 품질 문제와, 청킹과 pgvector 인덱스를 손봐 해결한 과정을 공유하는 발표.</p>
</section>
<section aria-labelledby="insight-title" data-el="4" style="display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="insight-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">핵심 인사이트</h2>
<span data-el="4.1" style="font-size: 14px; color: #6B665C;">8개</span>
</div>
<ol style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; border-top: 1px solid #E2DDD3;">
<li data-el="4.2" style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">01</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
틀린 답의 원인을 따라가 보니 생성 모델보다 검색 단계에서 엉뚱한 문서를 가져온 경우가 훨씬 많았다.
<button type="button" data-el="4.3" aria-label="04:30 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">04:30</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">02</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
평가 데이터 없이 튜닝하면 개선인지 착시인지 알 수 없어, 실제 질문 로그로 평가 세트부터 만들었다.
<button type="button" aria-label="09:05 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">09:05</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">03</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
파이프라인은 수집 → 청킹 → 임베딩 → 검색 → 재순위 → 생성의 여섯 단계로 단순하게 유지했다.
<button type="button" aria-label="12:40 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">12:40</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">04</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
청킹 크기를 512에서 256 토큰으로 줄이자 재현율이 12%p 올랐다.
<button type="button" aria-label="23:15 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">23:15</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">05</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
별도 벡터 DB 대신 PostgreSQL의 pgvector를 써서 원본 데이터와 같은 곳에서 관리했다.
<button type="button" aria-label="13:18 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">13:18</button>
<button type="button" aria-label="24:02 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">24:02</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">06</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
재순위 모델은 정확도를 올리지만 지연을 늘려, 재순위에 넘기는 후보 수를 줄여 균형을 맞췄다.
<button type="button" aria-label="31:48 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">31:48</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">07</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
문서가 바뀌면 바뀐 청크만 다시 임베딩하도록 청크마다 원본 버전을 기록했다.
<button type="button" aria-label="38:20 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">38:20</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">08</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
가장 효과가 컸던 것은 모델 교체가 아니라, 검색 결과를 사람이 직접 읽는 주간 리뷰였다.
<button type="button" aria-label="44:10 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">44:10</button>
</span>
</li>
</ol>
</section>
<section aria-labelledby="ask-title" data-el="5" style="display: flex; flex-direction: column; gap: 14px;">
<h2 id="ask-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">이런 걸 물어볼 수 있어요</h2>
<div style="display: flex; flex-wrap: wrap; gap: 10px;">
<button type="button" data-el="5.1" style="min-height: 44px; box-sizing: border-box; padding: 10px 16px; display: flex; align-items: center; gap: 8px; border-radius: 22px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; text-align: left; cursor: pointer;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0F6E68" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
<span>청킹 전략을 바꾼 근거는?</span>
</button>
<button type="button" style="min-height: 44px; box-sizing: border-box; padding: 10px 16px; display: flex; align-items: center; gap: 8px; border-radius: 22px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; text-align: left; cursor: pointer;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0F6E68" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
<span>pgvector 대신 검토한 대안은?</span>
</button>
<button type="button" style="min-height: 44px; box-sizing: border-box; padding: 10px 16px; display: flex; align-items: center; gap: 8px; border-radius: 22px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; text-align: left; cursor: pointer;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0F6E68" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
<span>운영 비용은 어떻게 달라졌나?</span>
</button>
</div>
</section>
<section aria-labelledby="chapter-title" data-el="6" style="display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="chapter-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">챕터</h2>
<span data-el="6.1" style="font-size: 14px; color: #6B665C;">9개</span>
</div>
<span data-el="6.2" style="font-size: 13px; color: #6B665C;">누르면 오른쪽 스크립트가 그 위치로 이동해요</span>
</div>
<div style="display: flex; flex-direction: column; gap: 6px;">
<button type="button" data-el="6.3" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">00:00</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">발표자 소개와 배경</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>사내 문서 검색 챗봇을 1년간 운영한 팀의 경험을 공유한다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>오늘 다룰 주제는 검색 품질이다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">04:30</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">문제 정의 — 검색이 왜 틀리나</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>틀린 답을 나눠 보니 검색 실패가 대부분이었다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>질문과 문서의 표현 차이가 주된 원인이었다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">09:05</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">평가 세트 만들기</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>실제 질문 로그에 정답 문서를 표시해 평가 세트를 만들었다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>바꿀 때마다 같은 세트로 재현율을 비교했다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid #9CCBC3; background: #FFFFFF; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">12:40</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">아키텍처 개요</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>수집부터 생성까지 여섯 단계 파이프라인</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>단계마다 입력과 출력을 로그로 남긴다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">19:30</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">청킹 전략</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>문단 경계를 지키면서 청크를 작게 나눴다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>청크 크기가 재현율에 가장 큰 영향을 줬다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">24:02</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">pgvector로 옮긴 이유</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>원본 데이터와 임베딩을 한 데이터베이스에서 관리한다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>인덱스 설정으로 속도와 정확도를 조절한다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">31:48</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">재순위와 지연</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>재순위로 정확도가 올랐지만 응답이 느려졌다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>후보 수를 줄여 지연을 되돌렸다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">38:20</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">운영 — 갱신과 모니터링</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>문서가 바뀌면 바뀐 청크만 다시 임베딩한다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>매주 검색 결과를 사람이 직접 읽는다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">46:30</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">질의응답</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>운영 비용, 다국어 문서, 권한 처리에 대한 질문이 이어졌다</span>
</span>
</span>
</button>
</div>
</section>
</main>
<aside aria-label="스크립트와 질문" data-el="7" style="min-width: 0; box-sizing: border-box; border-left: 1px solid #E2DDD3; background: #FBFAF7;">
<div style="position: sticky; top: 0; height: 896px; box-sizing: border-box; display: flex; flex-direction: column;">
<div style="height: 60px; flex-shrink: 0; box-sizing: border-box; padding: 0 20px; display: flex; align-items: flex-end; gap: 4px; border-bottom: 1px solid #E2DDD3;">
<button type="button" data-el="7.1" aria-pressed="true" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid #1B1A17; background: transparent; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
스크립트
</button>
<button type="button" data-el="7.2" aria-pressed="false" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: #6B665C; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
질문하기
<span data-el="7.3" style="min-width: 22px; height: 22px; box-sizing: border-box; padding: 0 7px; display: flex; align-items: center; justify-content: center; border-radius: 11px; background: #EFECE5; color: #4A463F; font-size: 12px; font-weight: 600;">3</span>
</button>
</div>
<div data-el="8" style="flex-grow: 1; min-height: 0; display: flex; flex-direction: column;">
<div style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 13px; color: #5E5A52;">
<span data-el="8.1">자막(수동) · 한국어</span>
<span data-el="8.2" style="font-family: 'IBM Plex Mono', monospace; font-weight: 600; color: #0F6E68;">12:40</span>
</div>
<div style="flex-grow: 1; min-height: 0; overflow: hidden; box-sizing: border-box; padding: 0 12px 16px; display: flex; flex-direction: column; gap: 2px;">
<button type="button" data-el="8.3" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">12:11</span>
<span style="font-size: 15px; line-height: 1.75;">그래서 그 분류 결과를 들고 구조를 처음부터 다시 봤습니다.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">12:24</span>
<span style="font-size: 15px; line-height: 1.75;">어디서 틀렸는지 모르는 상태로는 뭘 고쳐도 확신이 없었거든요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: #F8EDC4; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #7A5A00;">12:40</span>
<span style="font-size: 15px; line-height: 1.75;">지금 보시는 게 저희 전체 아키텍처입니다. 단계는 여섯 개로 단순하게 가져갔어요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">12:49</span>
<span style="font-size: 15px; line-height: 1.75;">첫 번째가 수집이고요, 사내 위키랑 드라이브 문서를 매일 새벽에 가져옵니다.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">12:58</span>
<span style="font-size: 15px; line-height: 1.75;">두 번째가 청킹인데, 이 부분은 뒤에서 따로 자세히 말씀드릴게요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:07</span>
<span style="font-size: 15px; line-height: 1.75;">세 번째 임베딩은 처음엔 외부 API를 쓰다가 나중에 모델을 바꿨고요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:18</span>
<span style="font-size: 15px; line-height: 1.75;">네 번째 검색은 PostgreSQL에 pgvector 확장을 올려서 하고 있습니다.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:29</span>
<span style="font-size: 15px; line-height: 1.75;">다섯 번째가 재순위인데, 여기서 지연 문제가 좀 있었습니다.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:41</span>
<span style="font-size: 15px; line-height: 1.75;">마지막이 생성이고, 검색된 청크 중 상위 다섯 개만 넣어요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:52</span>
<span style="font-size: 15px; line-height: 1.75;">중요한 건 단계마다 입력과 출력을 전부 로그로 남긴다는 거예요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">14:03</span>
<span style="font-size: 15px; line-height: 1.75;">그래야 답이 틀렸을 때 어느 단계에서 틀렸는지 거꾸로 따라갈 수 있거든요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">14:15</span>
<span style="font-size: 15px; line-height: 1.75;">실제로 이 로그 덕분에 앞에서 말씀드린 분류를 할 수 있었습니다.</span>
</button>
</div>
</div>
</div>
</aside>
</div>
</div>
<div class="row">
<div>
<div class="var" style="width: 520px;"><b>[질문하기] 탭</b> — 질문 턴 셋. 셋째는 영상에 없는 내용 · 캔버스 ResultChat 보드</div>
<div class="crop" style="width: 520px; padding: 0;">
<aside aria-label="스크립트와 질문" style="min-width: 0; box-sizing: border-box; border-left: 1px solid #E2DDD3; background: #FBFAF7;">
<div style="position: sticky; top: 0; height: 896px; box-sizing: border-box; display: flex; flex-direction: column;">
<div style="height: 60px; flex-shrink: 0; box-sizing: border-box; padding: 0 20px; display: flex; align-items: flex-end; gap: 4px; border-bottom: 1px solid #E2DDD3;">
<button type="button" aria-pressed="false" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: #6B665C; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
스크립트
</button>
<button type="button" aria-pressed="true" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid #1B1A17; background: transparent; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
질문하기
<span style="min-width: 22px; height: 22px; box-sizing: border-box; padding: 0 7px; display: flex; align-items: center; justify-content: center; border-radius: 11px; background: #EFECE5; color: #4A463F; font-size: 12px; font-weight: 600;">3</span>
</button>
</div>
<div style="flex-grow: 1; min-height: 0; display: flex; flex-direction: column;">
<div data-el="9" style="flex-grow: 1; min-height: 0; overflow: hidden; box-sizing: border-box; padding: 20px 24px; display: flex; flex-direction: column; gap: 26px;">
<div data-el="9.2" style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div data-el="9.3" style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">어떤 DB를 썼어?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span data-el="9.4" style="font-size: 15px; line-height: 1.75; color: #1B1A17;">PostgreSQL을 썼고, 벡터 검색은 pgvector 확장으로 처리했다고 합니다. 별도 벡터 DB를 두지 않은 이유로 원본 데이터와 임베딩을 한곳에서 관리할 수 있다는 점을 들었습니다.</span>
<span style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px;">
<span style="font-size: 13px; color: #6B665C;">근거</span>
<button type="button" data-el="9.5" aria-label="13:18 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">13:18</button>
<button type="button" aria-label="24:02 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">24:02</button>
</span>
</div>
</div>
<div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">그거 성능은 어땠대?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 15px; line-height: 1.75; color: #1B1A17;">pgvector 인덱스 설정을 바꿔 속도와 정확도 사이를 조절했다고 설명합니다. 구체적인 응답 시간 수치는 발표에서 말하지 않았습니다.</span>
<span style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px;">
<span style="font-size: 13px; color: #6B665C;">근거</span>
<button type="button" aria-label="25:40 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">25:40</button>
</span>
</div>
</div>
<div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">발표자 회사 매출은?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 15px; line-height: 1.75; color: #4A463F;">이 영상에서는 다루지 않는 내용입니다.</span>
<span data-el="9.6" style="align-self: flex-start; height: 24px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 12px; font-weight: 600;">영상에 없는 내용</span>
</div>
</div>
</div>
<div data-el="10" style="flex-shrink: 0; box-sizing: border-box; padding: 14px 20px 20px; border-top: 1px solid #E2DDD3; background: #FBFAF7; display: flex; flex-direction: column; gap: 10px;">
<div style="display: flex; gap: 6px; overflow: hidden;">
<button type="button" data-el="10.1" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">청킹 전략을 바꾼 근거는?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">pgvector 대신 검토한 대안은?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">운영 비용은 어떻게 달라졌나?</button>
</div>
<div style="position: relative; box-sizing: border-box; padding: 8px 8px 8px 14px; display: flex; align-items: flex-end; gap: 8px; border-radius: 14px; border: 1px solid #CFC8BB; background: #FFFFFF;">
<label for="ask-box" style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;">이 영상에 질문하기</label>
<span data-el="10.3" style="flex-grow: 1; min-width: 0; display: flex;"><textarea id="ask-box" rows="2" placeholder="이 영상에 대해 물어보세요" style="width: 100%; min-width: 0; box-sizing: border-box; padding: 6px 0; border: 0; resize: none; background: transparent; color: #1B1A17; font-size: 15px; line-height: 1.6;"></textarea></span>
<button type="button" aria-label="보내기" data-el="10.4" aria-disabled="false" style="width: 40px; height: 40px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border: 0; border-radius: 10px; background: #1B1A17; color: #F6F4EF; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m5 12 7-7 7 7"></path><path d="M12 19V5"></path></svg>
</button>
</div>
<span data-el="10.5" style="font-size: 12px; color: #6B665C;">질문, 앞선 대화, 관련 스크립트가 OpenAI로 전송됩니다.</span>
</div>
</div>
</div>
</aside>
</div>
</div>
<div>
<div class="var" style="width: 520px;"><b>질문이 아직 없음</b> — 빈 상태 상자(9.1) · 캔버스에 없음</div>
<div class="crop" style="width: 520px; padding: 0;">
<aside aria-label="스크립트와 질문" style="min-width: 0; box-sizing: border-box; border-left: 1px solid #E2DDD3; background: #FBFAF7;">
<div style="position: sticky; top: 0; height: 896px; box-sizing: border-box; display: flex; flex-direction: column;">
<div style="height: 60px; flex-shrink: 0; box-sizing: border-box; padding: 0 20px; display: flex; align-items: flex-end; gap: 4px; border-bottom: 1px solid #E2DDD3;">
<button type="button" aria-pressed="false" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: #6B665C; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
스크립트
</button>
<button type="button" aria-pressed="true" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid #1B1A17; background: transparent; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
질문하기
<span style="min-width: 22px; height: 22px; box-sizing: border-box; padding: 0 7px; display: flex; align-items: center; justify-content: center; border-radius: 11px; background: #EFECE5; color: #4A463F; font-size: 12px; font-weight: 600;">0</span>
</button>
</div>
<div style="flex-grow: 1; min-height: 0; display: flex; flex-direction: column;">
<div style="flex-grow: 1; min-height: 0; overflow: hidden; box-sizing: border-box; padding: 20px 24px; display: flex; flex-direction: column; gap: 26px;">
<div data-el="9.1" style="box-sizing: border-box; padding: 24px; border-radius: 14px; border: 1px dashed #CFC8BB; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 16px; font-weight: 600;">아직 질문이 없어요</span>
<span style="font-size: 14px; line-height: 1.6; color: #5E5A52;">아래 추천 질문을 누르거나 직접 물어보세요. 답에는 근거가 된 시각이 함께 붙습니다.</span>
</div>
</div>
<div style="flex-shrink: 0; box-sizing: border-box; padding: 14px 20px 20px; border-top: 1px solid #E2DDD3; background: #FBFAF7; display: flex; flex-direction: column; gap: 10px;">
<div style="display: flex; gap: 6px; overflow: hidden;">
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">청킹 전략을 바꾼 근거는?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">pgvector 대신 검토한 대안은?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">운영 비용은 어떻게 달라졌나?</button>
</div>
<div style="position: relative; box-sizing: border-box; padding: 8px 8px 8px 14px; display: flex; align-items: flex-end; gap: 8px; border-radius: 14px; border: 1px solid #CFC8BB; background: #FFFFFF;">
<label for="ask-box" style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;">이 영상에 질문하기</label>
<span style="flex-grow: 1; min-width: 0; display: flex;"><textarea id="ask-box" rows="2" placeholder="이 영상에 대해 물어보세요" style="width: 100%; min-width: 0; box-sizing: border-box; padding: 6px 0; border: 0; resize: none; background: transparent; color: #1B1A17; font-size: 15px; line-height: 1.6;"></textarea></span>
<button type="button" aria-label="보내기" aria-disabled="false" style="width: 40px; height: 40px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border: 0; border-radius: 10px; background: #1B1A17; color: #F6F4EF; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m5 12 7-7 7 7"></path><path d="M12 19V5"></path></svg>
</button>
</div>
<span style="font-size: 12px; color: #6B665C;">질문, 앞선 대화, 관련 스크립트가 OpenAI로 전송됩니다.</span>
</div>
</div>
</div>
</aside>
</div>
</div>
</div>
<div class="row">
<div>
<div class="var" style="width: 520px;"><b>답을 기다리는 중</b> — 마지막 턴의 답 자리에 대기 표시(9.7) · 캔버스에 없음</div>
<div class="crop" style="width: 520px; padding: 0;">
<aside aria-label="스크립트와 질문" style="min-width: 0; box-sizing: border-box; border-left: 1px solid #E2DDD3; background: #FBFAF7;">
<div style="position: sticky; top: 0; height: 896px; box-sizing: border-box; display: flex; flex-direction: column;">
<div style="height: 60px; flex-shrink: 0; box-sizing: border-box; padding: 0 20px; display: flex; align-items: flex-end; gap: 4px; border-bottom: 1px solid #E2DDD3;">
<button type="button" aria-pressed="false" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: #6B665C; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
스크립트
</button>
<button type="button" aria-pressed="true" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid #1B1A17; background: transparent; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
질문하기
<span style="min-width: 22px; height: 22px; box-sizing: border-box; padding: 0 7px; display: flex; align-items: center; justify-content: center; border-radius: 11px; background: #EFECE5; color: #4A463F; font-size: 12px; font-weight: 600;">3</span>
</button>
</div>
<div style="flex-grow: 1; min-height: 0; display: flex; flex-direction: column;">
<div style="flex-grow: 1; min-height: 0; overflow: hidden; box-sizing: border-box; padding: 20px 24px; display: flex; flex-direction: column; gap: 26px;">
<div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">어떤 DB를 썼어?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 15px; line-height: 1.75; color: #1B1A17;">PostgreSQL을 썼고, 벡터 검색은 pgvector 확장으로 처리했다고 합니다. 별도 벡터 DB를 두지 않은 이유로 원본 데이터와 임베딩을 한곳에서 관리할 수 있다는 점을 들었습니다.</span>
<span style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px;">
<span style="font-size: 13px; color: #6B665C;">근거</span>
<button type="button" aria-label="13:18 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">13:18</button>
<button type="button" aria-label="24:02 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">24:02</button>
</span>
</div>
</div>
<div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">그거 성능은 어땠대?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 15px; line-height: 1.75; color: #1B1A17;">pgvector 인덱스 설정을 바꿔 속도와 정확도 사이를 조절했다고 설명합니다. 구체적인 응답 시간 수치는 발표에서 말하지 않았습니다.</span>
<span style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px;">
<span style="font-size: 13px; color: #6B665C;">근거</span>
<button type="button" aria-label="25:40 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">25:40</button>
</span>
</div>
</div>
<div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">재순위 모델은 뭘 썼어?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span data-el="9.7" role="status" style="display: flex; align-items: center; gap: 10px; font-size: 14px; color: #6B665C;">
<span class="va-pulse" aria-hidden="true" style="display: flex; gap: 4px;">
<span style="width: 6px; height: 6px; border-radius: 50%; background: #948D80; display: block;"></span>
<span style="width: 6px; height: 6px; border-radius: 50%; background: #948D80; display: block;"></span>
<span style="width: 6px; height: 6px; border-radius: 50%; background: #948D80; display: block;"></span>
</span>
답을 만드는 중이에요
</span>
</div>
</div>
</div>
<div style="flex-shrink: 0; box-sizing: border-box; padding: 14px 20px 20px; border-top: 1px solid #E2DDD3; background: #FBFAF7; display: flex; flex-direction: column; gap: 10px;">
<div style="display: flex; gap: 6px; overflow: hidden;">
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">청킹 전략을 바꾼 근거는?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">pgvector 대신 검토한 대안은?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">운영 비용은 어떻게 달라졌나?</button>
</div>
<div style="position: relative; box-sizing: border-box; padding: 8px 8px 8px 14px; display: flex; align-items: flex-end; gap: 8px; border-radius: 14px; border: 1px solid #CFC8BB; background: #FFFFFF;">
<label for="ask-box" style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;">이 영상에 질문하기</label>
<span style="flex-grow: 1; min-width: 0; display: flex;"><textarea id="ask-box" rows="2" placeholder="이 영상에 대해 물어보세요" style="width: 100%; min-width: 0; box-sizing: border-box; padding: 6px 0; border: 0; resize: none; background: transparent; color: #1B1A17; font-size: 15px; line-height: 1.6;"></textarea></span>
<button type="button" aria-label="보내기" aria-disabled="false" style="width: 40px; height: 40px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border: 0; border-radius: 10px; background: #1B1A17; color: #F6F4EF; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m5 12 7-7 7 7"></path><path d="M12 19V5"></path></svg>
</button>
</div>
<span style="font-size: 12px; color: #6B665C;">질문, 앞선 대화, 관련 스크립트가 OpenAI로 전송됩니다.</span>
</div>
</div>
</div>
</aside>
</div>
</div>
<div>
<div class="var" style="width: 520px;"><b>답을 받지 못함</b> — 마지막 턴의 답 자리에 실패 한 줄과 [다시 시도](9.8 · 9.9) · 캔버스에 없음</div>
<div class="crop" style="width: 520px; padding: 0;">
<aside aria-label="스크립트와 질문" style="min-width: 0; box-sizing: border-box; border-left: 1px solid #E2DDD3; background: #FBFAF7;">
<div style="position: sticky; top: 0; height: 896px; box-sizing: border-box; display: flex; flex-direction: column;">
<div style="height: 60px; flex-shrink: 0; box-sizing: border-box; padding: 0 20px; display: flex; align-items: flex-end; gap: 4px; border-bottom: 1px solid #E2DDD3;">
<button type="button" aria-pressed="false" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: #6B665C; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
스크립트
</button>
<button type="button" aria-pressed="true" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid #1B1A17; background: transparent; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
질문하기
<span style="min-width: 22px; height: 22px; box-sizing: border-box; padding: 0 7px; display: flex; align-items: center; justify-content: center; border-radius: 11px; background: #EFECE5; color: #4A463F; font-size: 12px; font-weight: 600;">3</span>
</button>
</div>
<div style="flex-grow: 1; min-height: 0; display: flex; flex-direction: column;">
<div style="flex-grow: 1; min-height: 0; overflow: hidden; box-sizing: border-box; padding: 20px 24px; display: flex; flex-direction: column; gap: 26px;">
<div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">어떤 DB를 썼어?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 15px; line-height: 1.75; color: #1B1A17;">PostgreSQL을 썼고, 벡터 검색은 pgvector 확장으로 처리했다고 합니다. 별도 벡터 DB를 두지 않은 이유로 원본 데이터와 임베딩을 한곳에서 관리할 수 있다는 점을 들었습니다.</span>
<span style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px;">
<span style="font-size: 13px; color: #6B665C;">근거</span>
<button type="button" aria-label="13:18 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">13:18</button>
<button type="button" aria-label="24:02 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">24:02</button>
</span>
</div>
</div>
<div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">그거 성능은 어땠대?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 15px; line-height: 1.75; color: #1B1A17;">pgvector 인덱스 설정을 바꿔 속도와 정확도 사이를 조절했다고 설명합니다. 구체적인 응답 시간 수치는 발표에서 말하지 않았습니다.</span>
<span style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px;">
<span style="font-size: 13px; color: #6B665C;">근거</span>
<button type="button" aria-label="25:40 위치의 스크립트로 이동" style="height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer;">25:40</button>
</span>
</div>
</div>
<div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;">
<div style="align-self: flex-end; max-width: 84%; box-sizing: border-box; padding: 10px 14px; border-radius: 14px 14px 4px 14px; background: #1B1A17; color: #F6F4EF; font-size: 15px; line-height: 1.6;">재순위 모델은 뭘 썼어?</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
<span data-el="9.8" role="alert" style="font-size: 14px; line-height: 1.6; color: #A33A2B;">OpenAI API에 연결하지 못했어요 — 응답 시간 초과</span>
<button data-el="9.9" type="button" style="height: 32px; box-sizing: border-box; padding: 0 12px; border-radius: 8px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 13px; font-weight: 600; cursor: pointer;">다시 시도</button>
</span>
</div>
</div>
</div>
<div style="flex-shrink: 0; box-sizing: border-box; padding: 14px 20px 20px; border-top: 1px solid #E2DDD3; background: #FBFAF7; display: flex; flex-direction: column; gap: 10px;">
<div style="display: flex; gap: 6px; overflow: hidden;">
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">청킹 전략을 바꾼 근거는?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">pgvector 대신 검토한 대안은?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">운영 비용은 어떻게 달라졌나?</button>
</div>
<div style="position: relative; box-sizing: border-box; padding: 8px 8px 8px 14px; display: flex; align-items: flex-end; gap: 8px; border-radius: 14px; border: 1px solid #CFC8BB; background: #FFFFFF;">
<label for="ask-box" style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;">이 영상에 질문하기</label>
<span style="flex-grow: 1; min-width: 0; display: flex;"><textarea id="ask-box" rows="2" placeholder="이 영상에 대해 물어보세요" style="width: 100%; min-width: 0; box-sizing: border-box; padding: 6px 0; border: 0; resize: none; background: transparent; color: #1B1A17; font-size: 15px; line-height: 1.6;"></textarea></span>
<button type="button" aria-label="보내기" aria-disabled="false" style="width: 40px; height: 40px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border: 0; border-radius: 10px; background: #1B1A17; color: #F6F4EF; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m5 12 7-7 7 7"></path><path d="M12 19V5"></path></svg>
</button>
</div>
<span style="font-size: 12px; color: #6B665C;">질문, 앞선 대화, 관련 스크립트가 OpenAI로 전송됩니다.</span>
</div>
</div>
</div>
</aside>
</div>
</div>
</div>
<div class="row">
<div>
<div class="var" style="width: 520px;"><b>키 없이 질문하기</b> — 입력 영역에 키 없음 안내(10.2), [보내기]는 막힌 모양 · 캔버스에 없음</div>
<div class="crop" style="width: 520px; padding: 0;">
<div style="flex-shrink: 0; box-sizing: border-box; padding: 14px 20px 20px; border-top: 1px solid #E2DDD3; background: #FBFAF7; display: flex; flex-direction: column; gap: 10px;">
<div style="display: flex; gap: 6px; overflow: hidden;">
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">청킹 전략을 바꾼 근거는?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">pgvector 대신 검토한 대안은?</button>
<button type="button" style="height: 32px; flex-shrink: 0; box-sizing: border-box; padding: 0 12px; border-radius: 16px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #4A463F; font-size: 13px; white-space: nowrap; cursor: pointer;">운영 비용은 어떻게 달라졌나?</button>
</div>
<p data-el="10.2" style="margin: 0; font-size: 13px; line-height: 1.55; color: #7A2A1E;">API 키가 없어 질문할 수 없어요. <a href="#" style="color: #7A2A1E; font-weight: 600;">키 넣으러 가기</a></p>
<div style="position: relative; box-sizing: border-box; padding: 8px 8px 8px 14px; display: flex; align-items: flex-end; gap: 8px; border-radius: 14px; border: 1px solid #CFC8BB; background: #FFFFFF;">
<label for="ask-box" style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;">이 영상에 질문하기</label>
<span style="flex-grow: 1; min-width: 0; display: flex;"><textarea id="ask-box" rows="2" placeholder="이 영상에 대해 물어보세요" style="width: 100%; min-width: 0; box-sizing: border-box; padding: 6px 0; border: 0; resize: none; background: transparent; color: #1B1A17; font-size: 15px; line-height: 1.6;"></textarea></span>
<button type="button" aria-label="보내기" aria-disabled="true" style="width: 40px; height: 40px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border: 0; border-radius: 10px; background: #E2DDD3; color: #5E5A52; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m5 12 7-7 7 7"></path><path d="M12 19V5"></path></svg>
</button>
</div>
<span style="font-size: 12px; color: #6B665C;">질문, 앞선 대화, 관련 스크립트가 OpenAI로 전송됩니다.</span>
</div>
</div>
</div>
<div>
<div class="var" style="width: 420px;"><b>짧은 알림</b> — 이미 분석한 영상으로 열렸을 때(11). 위치는 정하지 않았다 · 캔버스에 없음</div>
<div class="crop">
<div role="status" data-el="11" style="display: inline-flex; align-items: center; gap: 10px; box-sizing: border-box; min-height: 48px; padding: 12px 18px; border-radius: 12px; background: #1B1A17; color: #F6F4EF; font-size: 15px; box-shadow: 0 12px 32px rgba(27, 26, 23, 0.24);">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8FC7BE" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 6 9 17l-5-5"></path></svg>
이미 분석한 영상입니다
</div>
</div>
</div>
</div>
<div class="var"><b>긴 영상 — 파트</b> — 1시간이 넘는 영상은 챕터를 파트로 묶고 첫 파트만 펼친다(6.4 ~ 6.6) · 캔버스 ResultLong 보드</div>
<div class="crop" style="width: 808px;">
<section aria-labelledby="chapter-title" style="display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="chapter-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">챕터</h2>
<span style="font-size: 14px; color: #6B665C;">25개 · 파트 4개</span>
</div>
<span style="font-size: 13px; color: #6B665C;">누르면 오른쪽 스크립트가 그 위치로 이동해요</span>
</div>
<div style="display: flex; flex-direction: column; gap: 12px;">
<div data-el="6.4" style="border-radius: 14px; border: 1px solid #E2DDD3; background: #FBFAF7; overflow: hidden;">
<button type="button" data-el="6.5" aria-expanded="true" style="width: 100%; min-height: 64px; box-sizing: border-box; padding: 12px 18px; display: flex; align-items: center; gap: 14px; border: 0; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 28px; height: 28px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; color: #4A463F; transform: rotate(90deg);">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m9 18 6-6-6-6"></path></svg>
</span>
<span style="flex-grow: 1; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">오전 세션 1 — 현황과 문제</span>
<span style="font-size: 13px; color: #6B665C;">챕터 6개</span>
</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #4A463F;">0:00:00 – 0:40:10</span>
</button>
<div style="box-sizing: border-box; padding: 0 10px 10px; display: flex; flex-direction: column; gap: 4px;">
<button type="button" data-el="6.6" style="width: 100%; box-sizing: border-box; padding: 12px 14px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 10px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">0:00:00</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 16px; line-height: 1.5; font-weight: 600;">워크숍 소개와 진행 방식</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>오늘 목표는 도입 범위와 운영 방식을 정하는 것</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>오전엔 논의, 오후엔 실습으로 나눈다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 12px 14px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 10px; border: 1px solid #9CCBC3; background: #FFFFFF; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">0:06:20</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 16px; line-height: 1.5; font-weight: 600;">데이터를 찾는 데 드는 시간</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>분석가들이 데이터 위치를 묻고 기다리는 시간이 길다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>같은 질문이 채널에 반복해서 올라온다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 12px 14px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 10px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">0:12:05</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 16px; line-height: 1.5; font-weight: 600;">지금 쓰는 위키 문서의 한계</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>문서가 실제 테이블과 금방 어긋난다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>누가 고쳐야 하는지 정해져 있지 않다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 12px 14px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 10px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">0:18:45</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 16px; line-height: 1.5; font-weight: 600;">같은 지표, 다른 정의</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>팀마다 활성 회원의 기준이 달랐다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>용어 합의를 카탈로그보다 먼저 한다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 12px 14px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 10px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">0:26:30</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 16px; line-height: 1.5; font-weight: 600;">다른 조직의 도입 사례</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>작게 시작해 넓힌 경우가 오래 유지됐다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 12px 14px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 10px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">0:31:10</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 16px; line-height: 1.5; font-weight: 600;">도구 선정 기준</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>웨어하우스 연동과 운영 부담을 먼저 본다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>기능 목록 비교는 마지막에 한다</span>
</span>
</span>
</button>
</div>
</div>
<div style="border-radius: 14px; border: 1px solid #E2DDD3; background: #FBFAF7; overflow: hidden;">
<button type="button" aria-expanded="false" style="width: 100%; min-height: 64px; box-sizing: border-box; padding: 12px 18px; display: flex; align-items: center; gap: 14px; border: 0; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 28px; height: 28px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; color: #4A463F; transform: rotate(0deg);">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m9 18 6-6-6-6"></path></svg>
</span>
<span style="flex-grow: 1; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">오전 세션 2 — 범위와 용어</span>
<span style="font-size: 13px; color: #6B665C;">챕터 6개</span>
</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #4A463F;">0:40:10 – 1:05:00</span>
</button>
</div>
<div style="border-radius: 14px; border: 1px solid #E2DDD3; background: #FBFAF7; overflow: hidden;">
<button type="button" aria-expanded="false" style="width: 100%; min-height: 64px; box-sizing: border-box; padding: 12px 18px; display: flex; align-items: center; gap: 14px; border: 0; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 28px; height: 28px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; color: #4A463F; transform: rotate(0deg);">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m9 18 6-6-6-6"></path></svg>
</span>
<span style="flex-grow: 1; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">오후 세션 1 — 수집 실습</span>
<span style="font-size: 13px; color: #6B665C;">챕터 7개</span>
</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #4A463F;">1:05:00 – 1:50:20</span>
</button>
</div>
<div style="border-radius: 14px; border: 1px solid #E2DDD3; background: #FBFAF7; overflow: hidden;">
<button type="button" aria-expanded="false" style="width: 100%; min-height: 64px; box-sizing: border-box; padding: 12px 18px; display: flex; align-items: center; gap: 14px; border: 0; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 28px; height: 28px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; color: #4A463F; transform: rotate(0deg);">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m9 18 6-6-6-6"></path></svg>
</span>
<span style="flex-grow: 1; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">오후 세션 2 — 운영과 다음 단계</span>
<span style="font-size: 13px; color: #6B665C;">챕터 6개</span>
</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #4A463F;">1:50:20 – 2:30:00</span>
</button>
</div>
</div>
</section>
</div>
```

### 요소

| # | 이름 | 종류 | 보여주는 것 | 누르면 |
|---|---|---|---|---|
| 1 | 머리 줄 | 영역 | 왼쪽에 뒤로 링크, 오른쪽에 내보내기와 휴지통 | — |
| 1.1 | 뒤로 링크 | 링크 | 왼쪽 화살표 + '분석한 영상' (VA-UI-001 4.2 뒤로 링크) | [[#UI-1]] |
| 1.2 | 내보내기 | 버튼 | 내려받기 아이콘 + '내보내기'. 공통 1.8의 보조 버튼 | [[#UI-7]] 다이얼로그가 이 화면 위에 뜬다 |
| 1.3 | 휴지통 | 버튼 | 빨간 휴지통 아이콘만. 공통 1.8의 테두리 아이콘 버튼, aria-label '분석 결과 삭제' | [[#UI-6]] 다이얼로그가 뜬다 |
| 2 | 제목 블록 | 영역 | 칩 셋, 영상 제목, 메타 줄과 원본 링크 | — |
| 2.1 | 칩 셋 | 칩 | VA-UI-001 4.2 메타 칩 세 개: 출처('YouTube' 또는 '로컬 파일') · 길이 · '자막 · {언어}' 또는 '받아쓰기 · {언어}' | — |
| 2.2 | 영상 제목 | 텍스트 | h1. YouTube는 영상 제목, 로컬 파일은 파일 이름 | — |
| 2.3 | 메타 줄 | 텍스트 | '{채널 또는 로컬 파일} · {분석 시각} 분석 · {모델}' | — |
| 2.4 | 원본 영상 열기 | 링크 | '원본 영상 열기' + 바깥 링크 아이콘. YouTube 결과에만 | YouTube 원본을 새 탭으로 연다 (앱 밖) |
| 3 | 한 줄 요약 | 영역 | 작은 라벨 '한 줄 요약'과 큰 세리프 문장 하나 | — |
| 4 | 핵심 인사이트 | 영역 | 섹션 제목 '핵심 인사이트', 개수, 인사이트 목록 | — |
| 4.1 | 인사이트 개수 | 텍스트 | '{n}개' | — |
| 4.2 | 인사이트 행 | 행 | 두 자리 번호(01, 02 …) · 문장 · 문장 끝 시각 칩 1개 이상. 행 사이 구분선 | — |
| 4.3 | 인사이트 시각 칩 | 칩 | 공통 1.3 시각 칩. 한 행에 둘 이상 붙을 수 있다. aria-label '{시각} 위치의 스크립트로 이동' | 시각 선택: 7.1 탭 · 8.3 강조와 스크롤 · 6.3/6.6 선택 · 8.2 바뀜 |
| 5 | 이런 걸 물어볼 수 있어요 | 영역 | 섹션 제목과 추천 질문 알약 3개. 줄바꿈된다 | — |
| 5.1 | 추천 질문 알약 | 버튼 | 공통 1.8의 큰 알약. 말풍선 아이콘 + 질문 문장 | 7.2 탭으로 바뀌고 그 문장이 바로 전송된다 |
| 6 | 챕터 | 영역 | 섹션 제목 '챕터', 개수, 안내, 챕터 카드 목록 또는 파트 카드 | — |
| 6.1 | 챕터 개수 | 텍스트 | '{n}개'. 파트로 묶었으면 '{n}개 · 파트 {m}개' | — |
| 6.2 | 챕터 안내 | 텍스트 | '누르면 오른쪽 스크립트가 그 위치로 이동해요' | — |
| 6.3 | 챕터 카드 | 행 | 1시간 이하 영상. 시작 시각(시각 칩 모양 표시) · 제목 · 가운뎃점 요점 2~3줄. 카드 전체가 버튼. 선택되면 흰 바탕과 선택 챕터 테두리 | 시각 선택: 카드의 시작 시각 |
| 6.4 | 파트 카드 | 영역 | 1시간 초과 영상. 파트 머리와, 펼쳤을 때 그 파트의 챕터 카드 | — |
| 6.5 | 파트 머리 | 버튼 | 화살표 · 파트 제목 · '챕터 {n}개' · '{시작} – {끝}'. aria-expanded | 그 파트만 펴거나 접는다 |
| 6.6 | 파트 안 챕터 카드 | 행 | 6.3과 같은 구성. 펼친 파트 안에만 | 시각 선택: 카드의 시작 시각 |
| 7 | 오른쪽 패널 | 영역 | 창에 고정된 패널. aria-label '스크립트와 질문'. 탭 바와 탭 내용(8 또는 9와 10) | — |
| 7.1 | 스크립트 탭 | 탭 | 목록 아이콘 + '스크립트'. 기본 탭 | 8을 보인다 |
| 7.2 | 질문하기 탭 | 탭 | 말풍선 아이콘 + '질문하기' + 7.3 | 9와 10을 보인다 |
| 7.3 | 질문 수 배지 | 배지 | 이 영상에 저장된 질문 수. 0도 보인다 | — |
| 8 | 스크립트 | 영역 | 머리줄(8.1 · 8.2)과 구간 목록. 패널 안에서 스크롤 | — |
| 8.1 | 스크립트 출처 | 텍스트 | '자막(수동) · {언어}', '자막(자동) · {언어}' 또는 '받아쓰기 {받아쓰기 모델} · {언어}' | — |
| 8.2 | 선택한 시각 | 텍스트 | 지금 선택한 시각. 선택이 없으면 비어 있다 | — |
| 8.3 | 스크립트 구간 | 행 | 시각 + 문장. 줄 전체가 버튼. 선택되면 형광 바탕과 형광 글자 시각 | 시각 선택: 그 구간의 시각 |
| 9 | 대화 목록 | 영역 | 질문 턴 목록 또는 빈 상태 상자. 패널 안에서 스크롤 | — |
| 9.1 | 빈 상태 상자 | 상자 | 공통 1.7 빈 상태 상자(질문하기 판). '아직 질문이 없어요'와 '아래 추천 질문을 누르거나 직접 물어보세요. 답에는 근거가 된 시각이 함께 붙습니다.' | — |
| 9.2 | 질문 턴 | 행 | 질문 하나와 그 답 | — |
| 9.3 | 질문 말풍선 | 텍스트 | 오른쪽에 붙은 검은 말풍선 안의 질문 문장 | — |
| 9.4 | 답 | 텍스트 | 답 문장. 근거가 없는 답은 흐린 글자 | — |
| 9.5 | 근거 칩 | 칩 | 작은 글자 '근거' 뒤 공통 1.3 시각 칩 1개 이상 | 시각 선택: 칩의 시각 |
| 9.6 | 영상에 없는 내용 | 배지 | '영상에 없는 내용'. 근거가 없는 답에만 | — |
| 9.7 | 답 대기 표시 | 텍스트 | 답을 기다리는 동안 9.4 자리에 | — |
| 9.8 | 답변 실패 | 텍스트 | 답을 받지 못했을 때 9.4 자리에 무엇이 왜 안 됐는지 한 줄 | — |
| 9.9 | 다시 시도 | 버튼 | '다시 시도' | 같은 질문을 다시 보내고 9.7로 돌아간다 |
| 10 | 질문 입력 영역 | 영역 | 패널 아래에 고정. 추천 칩, 키 없음 안내, 입력칸, 보내기, 전송 안내 | — |
| 10.1 | 추천 질문 칩 | 칩 | 공통 1.8의 작은 칩. 5.1과 같은 3개를 한 줄로, 넘치면 잘림 | 7.2 탭 그대로 그 문장이 바로 전송된다 |
| 10.2 | 키 없음 안내 | 텍스트 | 키가 없으면 'API 키가 없어 질문할 수 없어요.', 키 확인에 실패하면 '키를 확인하지 못해 질문할 수 없어요 — {이유}'. 끝에 '키 넣으러 가기' 링크. 인터넷이 없어 확인하지 못했으면 '연결을 확인하지 못했어요 — 인터넷이 되면 분석 버튼을 누를 때 다시 확인합니다'이고 링크는 없다 (VA-UI-001에 없음) | [[#UI-5]] |
| 10.3 | 질문 입력칸 | 입력 | 2줄 textarea. placeholder '이 영상에 대해 물어보세요', 숨은 라벨 '이 영상에 질문하기' | — |
| 10.4 | 보내기 | 버튼 | 위 화살표 아이콘만. aria-label '보내기' | 10.3 문장을 보내고 9 끝에 새 9.2가 생긴다 |
| 10.5 | 전송 안내 | 텍스트 | '질문, 앞선 대화, 관련 스크립트가 OpenAI로 전송됩니다.' | — |
| 11 | 짧은 알림 | 텍스트 | 공통 1.5 짧은 알림. '이미 분석한 영상입니다' 또는 내보내기 완료 문구('data/export/{파일 이름}.md에 저장했어요' / '클립보드에 복사했어요'). role status. 잠깐 보였다가 저절로 사라진다 | — |

### 규칙

- 두 열이다. 왼쪽 본문(1~6)은 페이지와 함께 스크롤되고, 오른쪽 패널(7)은 창에 고정돼 왼쪽을 스크롤해도 따라온다. 폭·높이는 VA-UI-001 3.3 레이아웃 크기를 따른다.
- 패널(7) 높이는 창 높이에서 헤더를 뺀 값이다. 스크립트(8)와 대화 목록(9)은 패널 안에서 스크롤되고, 질문 입력 영역(10)은 패널 아래에 붙어 함께 스크롤되지 않는다.
- 키 없음 배너(공통 1.4)가 떠 있으면 배너도 헤더와 함께 창 위에 남고, 패널(7) 높이는 창 높이에서 헤더 높이와 배너 높이를 뺀 값이다. 그래야 질문 입력 영역(10)과 키 없음 안내(10.2)가 창 밖으로 밀리지 않는다 (VA-UI-001에 없음)
- 왼쪽 본문은 머리 줄(1) → 제목 블록(2) → 한 줄 요약(3) → 핵심 인사이트(4) → 추천 질문(5) → 챕터(6) 순서다. [[VA-UC-001#UC-H3]] 1번과 달리 추천 질문(5)이 챕터(6) 앞에 오고, 스크립트와 질문창은 오른쪽 패널(7)로 옮겼다(VA-UI-001 7장 1, 8장).
- 헤더(공통 1.1)의 두 메뉴는 현재 위치로 표시하지 않는다.
- API 키가 없거나 키 확인에 실패한 동안 헤더 위에 공통 1.4 키 없음 배너를 둔다. 결과 읽기와 시각 이동은 그대로 되고 질문 보내기만 막힌다. 배너가 연결 문구일 때는 질문 보내기도 막지 않는다(공통 1.4).
- 주소는 `/videos/{id}`다. 이 주소로 들어왔는데 결과가 아직 없으면(진행 중·실패) UI-3으로 넘긴다.
- 내보내기(1.2)는 내려받기 아이콘을 붙인 보조 버튼, 휴지통(1.3)은 흰 바탕·테두리에 빨간 휴지통 아이콘인 테두리 아이콘 버튼이다(VA-UI-001 4.2).
- UI-7이 떠 있는 동안 이 화면은 덮개 아래 그대로 깔린다. UI-7이 닫히면 초점이 내보내기(1.2)로 돌아오고, 주 버튼으로 닫혔으면 짧은 알림(11)으로 완료를 알린다. 알림 모양은 보드에 없다.
- UI-6에서 [취소]나 Esc를 누르면 이 화면이 그대로 남고 초점이 휴지통(1.3)으로 돌아온다. [삭제]를 누르면 UI-1로 간다.
- UI-1에서 이미 분석한 영상을 넣어 이 화면이 열렸으면 짧은 알림(11)으로 '이미 분석한 영상입니다'를 알린다.
- 메타 줄(2.3)의 모델은 자막 결과면 '요약 {요약 모델}', 받아쓰기 결과면 '받아쓰기 {받아쓰기 모델}'이다.
- [[VA-UC-001#UC-S2]] 1번대로 수동 자막이 없어 자동 생성 자막으로 만든 결과는 스크립트 출처(8.1)를 '자막(자동) · {언어}'로 보이고, 칩 셋(2.1)은 '자막 · {언어}' 그대로다 (VA-UI-001에 없음)
- 원본 영상 열기(2.4)는 YouTube 결과에만 있고 새 탭으로 연다(새 탭은 보드에 없는 규칙). 로컬 파일 결과에는 없다.
- 길이와 이 화면의 모든 시각은 영상 길이로 형식을 정한다. 1시간 미만 영상은 mm:ss, 1시간 이상 영상은 h:mm:ss이고 한 영상 안에서는 모두 같다(VA-UI-001 4.4).
- 한 줄 요약(3)은 한 문장만 보인다.
- 인사이트 행(4.2)에는 이모지 카테고리를 붙이지 않는다. 인사이트는 1시간 이하 영상이면 5~8개, 넘으면 10개까지이고 인사이트 개수(4.1)는 실제 행 수다.
- 추천 질문 3개가 알약(5.1)과 칩(10.1) 두 곳에 같이 나온다. 어느 쪽이든 누르면 패널이 질문하기 탭(7.2)으로 바뀌고 그 문장이 바로 전송된다. 보드는 알약을 눌러 탭이 바뀌는 것까지만 그렸다.
- 챕터(6)는 영상이 1시간 이하면 챕터 카드(6.3) 목록, 1시간을 넘으면 파트 카드(6.4)로 묶는다. 챕터 개수(6.1)는 '{n}개' 또는 '{n}개 · 파트 {m}개'다.
- 챕터 카드(6.3·6.6)는 시작 시각 · 제목 · 가운뎃점 요점 2~3줄이다. 시작 시각은 시각 칩과 모양만 같은 표시이고 카드 전체가 버튼이다. 보드의 요점 1~2줄은 예시 데이터다.
- 파트 머리(6.5)를 누르면 그 파트만 펴고 접는다. 여러 파트를 함께 펼 수 있고, 처음에는 첫 파트만 펼친다. 화살표 회전과 aria-expanded가 함께 바뀌고 움직임은 없다(VA-UI-001 3.4).
- 시각을 누르는 네 곳, 인사이트 시각 칩(4.3) · 챕터 카드(6.3·6.6) · 근거 칩(9.5) · 스크립트 구간(8.3)은 모두 같은 동작을 한다(VA-UI-001 4.4).
- 시각 누르기 1: 패널이 스크립트 탭(7.1)으로 바뀐다.
- 시각 누르기 2: 그 시각이 든 스크립트 구간(8.3)이 형광 바탕과 형광 글자 시각으로 강조되고, 스크립트(8)가 그 구간으로 스크롤된다. 스크롤은 보드에 없는 규칙이다.
- 시각 누르기 3: 시작 시각이 같은 챕터 카드(6.3·6.6)가 흰 바탕과 선택 챕터 테두리로 바뀐다. 시작 시각이 같은 챕터가 없으면 선택된 카드가 없다.
- 시각 누르기 4: 선택한 시각(8.2)이 그 시각으로 바뀐다.
- 선택은 한 번에 하나다. 선택이 없는 챕터 카드와 구간은 바탕·테두리가 투명하다. 강조와 탭 전환은 바로 바뀐다.
- 처음 열면 선택한 시각이 없다. 선택한 시각(8.2) 자리는 비어 있고 스크립트(8)는 맨 위에서 시작한다. 보드의 12:40·0:06:20은 누른 뒤의 그림이다 (VA-UI-001에 없음)
- 선택된 챕터가 접힌 파트 안에 있어도 그 파트를 저절로 펴지 않는다 (VA-UI-001에 없음)
- 이 화면의 시각은 스크립트 이동에만 쓴다. YouTube 시점 링크는 여기 없고 내보내기(UI-7)에만 있다. [[VA-UC-001#UC-H3]] 6a와 달라 VA-UI-001 8장에 사용자 확인이 남아 있다.
- 패널(7)은 두 탭 중 하나만 보인다. 기본은 스크립트 탭(7.1)이다. 보드는 aria-pressed로 그렸고 코드에서는 tablist · tab · aria-selected로 옮긴다(VA-UI-001 4.6).
- 스크립트 구간(8.3)은 긴 영상도 조각 경계 없이 목록 하나로 보인다. 수천 구간을 한꺼번에 그리는 방법(가상 스크롤 등)은 뒤 단계에서 정한다.
- 질문 수 배지(7.3)는 이 영상에 저장된 질문 수이고, 0이어도 보인다.
- 다시 열면 기본 탭이 스크립트(7.1)라 이전 질문 기록은 질문 수 배지(7.3)로 알리고, 질문하기 탭(7.2)을 눌러야 보인다. [[VA-UC-001#UC-H5]] 3번의 '이전 질문·답변 기록이 함께 보인다'와 달라 VA-UI-001 8장에 갱신 요청이 있다.
- 질문 턴(9.2)은 오른쪽 검은 말풍선(9.3)과 그 아래 답(9.4)이다. 근거가 있는 답에는 '근거'와 근거 칩(9.5)이 붙고, 근거가 없는 답은 흐린 글자에 영상에 없는 내용 배지(9.6)가 붙는다.
- 앞 대화에 이어 묻는 질문도 맥락 안에서 답한다. 질문 기록은 다시 열어도 남는다.
- 빈 상태 상자(9.1)는 대화 목록(9)에 질문 턴(9.2)이 하나도 없을 때만 보이고, 입력 영역(10)은 그대로 있다. 답을 기다리거나 답을 받지 못한 턴도 턴으로 센다 (VA-UI-001에 없음)
- 질문 입력 영역(10)은 질문하기 탭에서만 보이고 패널 아래에 고정이다. 추천 질문 칩(10.1)은 줄바꿈 없이 한 줄이고 넘치면 잘린다.
- 전송 안내(10.5)는 '질문, 앞선 대화, 관련 스크립트가 OpenAI로 전송됩니다.'다. 보드 문구 '질문과 관련 스크립트가 OpenAI로 전송됩니다.'에 앞선 대화를 더했다.
- 답을 기다리는 동안 질문 입력칸(10.3)과 보내기(10.4)를 잠그고 답 자리에 답 대기 표시(9.7)를 둔다. 대기 모양은 보드에 없다.
- 답을 받지 못하면 답 자리에 답변 실패(9.8) 한 줄과 다시 시도(9.9)를 둔다. 문구는 무엇이 왜 안 됐는지 알린다(VA-UI-001 4.5).
- API 키가 없거나 키 확인에 실패하면 질문 입력칸(10.3)을 막고 UI-5로 가는 키 없음 안내(10.2)를 둔다. 이전 질문 기록은 그대로 보인다.
- 보내면 대화 목록(9) 끝에 새 질문 턴(9.2)이 생기고 입력칸이 비워진다. 답이 오면 질문 수 배지(7.3)가 1 늘고 잠금이 풀린다 (VA-UI-001에 없음)
- 새 턴이 생기거나 답이 오면 대화 목록(9)을 맨 아래로 스크롤한다 (VA-UI-001에 없음)
- 입력칸이 비어 있으면 보내기(10.4)를 눌러도 보내지 않는다. Enter는 보내기, Shift+Enter는 줄바꿈이고 한글 조합 중인 Enter는 보내지 않는다 (VA-UI-001에 없음)
- 답을 기다리는 동안이나 API 키가 없을 때는 보내기(10.4)와 함께 추천 질문 알약(5.1)과 칩(10.1)도 보내지 않는다. 알약은 탭만 바꾼다 (VA-UI-001에 없음)
- 답변 실패(9.8)가 뜨면 잠금을 푼다. 실패한 질문은 기록에 저장하지 않고 질문 수 배지(7.3)에도 세지 않는다 (VA-UI-001에 없음)
- 답변 실패(9.8)가 뜬 턴은 새 질문을 보내거나 화면을 다시 열면 대화 목록(9)에서 빠지고, 앞선 대화로 OpenAI에 보내지 않는다. 그래서 답변 실패(9.8)와 다시 시도(9.9)는 마지막 턴에만 있다 (VA-UI-001에 없음)
- 키 없음 안내(10.2)는 추천 질문 칩(10.1)과 입력칸(10.3) 사이에 한 줄로 두고 끝에 '키 넣으러 가기'를 붙인다. 보내기(10.4)도 함께 막는다. 연결 문구일 때는 링크를 붙이지 않고, 입력칸·보내기·추천 질문은 막지 않는다 — 보내면 그때 키를 다시 확인하고, 아직 안 되면 답변 실패(9.8)로 알린다(공통 1.4) (VA-UI-001에 없음)
- 누르는 영역은 VA-UI-001 4.6을 따른다. 시각 칩(4.3·9.5), 추천 질문 칩(10.1), 보내기(10.4), 원본 영상 열기(2.4)가 기본보다 작은 예외다.

### 시나리오

**S-1 요약을 읽고 인사이트 시각으로 스크립트를 찾는다** — [[VA-UC-001#UC-H3]] 기본 흐름 1~5
1. UI-3에서 분석이 끝나 이 화면이 저절로 열린다. 패널은 스크립트 탭(7.1)이고 선택한 시각이 없다.
2. 칩 셋(2.1) 'YouTube' '50:12' '자막 · 한국어'와 영상 제목(2.2), 메타 줄(2.3)로 어떤 영상인지 확인한다.
3. 한 줄 요약(3)과 인사이트 행(4.2) 여덟 개를 읽는다.
4. 챕터 카드(6.3) 아홉 개를 훑는다.
5. 셋째 인사이트 끝의 시각 칩(4.3) '12:40'을 누른다.
6. 12:40 스크립트 구간(8.3)이 형광 바탕으로 바뀌고 스크립트(8)가 그 구간으로 스크롤된다.
7. 시작 시각이 12:40인 챕터 카드(6.3) '아키텍처 개요'가 선택 모양이 되고 선택한 시각(8.2)이 '12:40'이 된다.
8. 챕터 카드(6.3) '청킹 전략'을 누른다. 선택이 19:30으로 옮겨 가고 12:40 선택은 풀린다.

**S-2 스크립트에서 거꾸로 찾는다** — [[VA-UC-001#UC-H3]] 확장 4a
1. 스크립트(8)를 내려 읽다가 13:18 스크립트 구간(8.3)을 누른다.
2. 그 구간이 강조되고 선택한 시각(8.2)이 '13:18'이 된다.
3. 13:18에 시작하는 챕터가 없어 선택된 챕터 카드(6.3)가 없다.

**S-3 긴 영상의 파트를 펴서 읽는다** — [[VA-UC-001#UC-H3]] 확장 3a
1. 2시간 30분 로컬 파일 결과를 연다. 칩 셋(2.1)이 '로컬 파일' '2:30:00' '받아쓰기 · 한국어'이고 원본 영상 열기(2.4)는 없다.
2. 메타 줄(2.3)은 '로컬 파일 · 오늘 15:21 분석 · 받아쓰기 whisper-1', 스크립트 출처(8.1)는 '받아쓰기 whisper-1 · 한국어'다. 모든 시각이 h:mm:ss다.
3. 인사이트 행(4.2)이 열 개, 챕터 개수(6.1)는 '25개 · 파트 4개'다. 파트 카드(6.4) 넷 중 첫 파트만 펴져 있다.
4. 셋째 파트의 파트 머리(6.5)를 누른다. 화살표가 돌고 그 파트의 챕터 카드(6.6) 일곱 개가 나온다. 첫 파트도 펴진 채다.
5. 챕터 카드(6.6) '1:22:40 비어 있는 설명과 소유자'를 누른다. 스크립트 구간(8.3)이 그 위치로 가고 선택한 시각(8.2)이 '1:22:40'이 된다.
6. 첫 파트의 파트 머리(6.5)를 다시 눌러 접는다.

**S-4 원본 영상에서 그 지점을 본다** — [[VA-UC-001#UC-H3]] 기본 흐름 6 (확장 6a와 다름, VA-UI-001 8장)
1. 인사이트 시각 칩(4.3) '24:02'를 눌러 스크립트(8)에서 앞뒤 맥락을 읽는다.
2. 원본 영상 열기(2.4)를 누른다. YouTube 원본이 새 탭으로 열린다.
3. 사용자가 YouTube에서 24:02로 직접 옮겨 본다. 이 화면의 시각은 YouTube 시점 링크가 아니다(6a와 다름, VA-UI-001 8장).

**S-5 추천 질문으로 묻고 근거를 따라간다** — [[VA-UC-001#UC-H4]] 기본 흐름 1~5, 확장 1a
1. 추천 질문 알약(5.1) 'pgvector 대신 검토한 대안은?'을 누른다.
2. 패널이 질문하기 탭(7.2)으로 바뀌고 그 문장이 바로 전송된다. 대화 목록(9) 끝에 질문 턴(9.2)이 생기고 답 자리에 답 대기 표시(9.7)가 뜬다.
3. 기다리는 동안 질문 입력칸(10.3)과 보내기(10.4)가 잠긴다.
4. 답이 오면 답 대기 표시 자리에 답(9.4)과 근거 칩(9.5)이 붙고, 질문 수 배지(7.3)가 3에서 4로 바뀌며 잠금이 풀린다.
5. 근거 칩(9.5)을 누른다. 패널이 스크립트 탭(7.1)으로 바뀌고 그 시각의 스크립트 구간(8.3)이 강조된다.
6. 질문하기 탭(7.2)을 다시 누른다. 대화 기록이 그대로 있다.

**S-6 이어서 묻고, 영상에 없는 것을 묻는다** — [[VA-UC-001#UC-H4]] 확장 1b, 3a
1. 질문 입력칸(10.3)에 '어떤 DB를 썼어?'를 쓰고 보내기(10.4)를 누른다. 답(9.4)에 근거 칩(9.5) '13:18' '24:02'가 붙는다.
2. 이어서 '그거 성능은 어땠대?'를 보낸다. 앞선 대화가 맥락으로 함께 가서 pgvector 성능에 대한 답이 온다.
3. '발표자 회사 매출은?'을 보낸다.
4. 답(9.4)이 흐린 글자로 보이고 근거 칩 대신 영상에 없는 내용 배지(9.6)가 붙는다. 누를 시각이 없어 스크립트(8)는 그대로다.

**S-7 기록이 없는 영상에서 처음 묻는다** — [[VA-UC-001#UC-H4]] 기본 흐름 1~4, 확장 1a
1. 질문 수 배지(7.3)가 0인 결과에서 질문하기 탭(7.2)을 누른다.
2. 대화 목록(9)에 빈 상태 상자(9.1)가 보이고, 아래 질문 입력 영역(10)은 그대로 있다.
3. 추천 질문 칩(10.1) '용어 합의는 누가 주도하기로 했어?'를 누른다. 그 문장이 바로 전송된다.
4. 빈 상태 상자(9.1)가 사라지고 첫 질문 턴(9.2)이 답 대기 표시(9.7)와 함께 생긴다.
5. 답(9.4)이 오면 질문 수 배지(7.3)가 0에서 1이 되고 잠금이 풀린다.

**S-8 답을 받지 못했다** — [[VA-UC-001#UC-H4]] 확장 2a
1. 질문을 보냈는데 OpenAI 호출이 실패한다.
2. 답 대기 표시(9.7) 자리에 답변 실패(9.8) 'OpenAI API에 연결하지 못했어요 — {이유}'와 다시 시도(9.9)가 뜨고 입력 잠금이 풀린다.
3. 앞선 질문 턴(9.2)과 질문 수 배지(7.3)는 그대로다.
4. 다시 시도(9.9)를 누른다. 같은 질문을 다시 보내고 답 대기 표시(9.7)로 돌아간다.

**S-9 API 키가 없을 때 결과를 연다** — [[VA-UC-001#UC-H4]] 사전조건 · [[VA-UC-001#UC-H5]] 기본 흐름 3
1. 키가 없는 상태에서 UI-1 완료 행을 눌러 이 화면을 연다. 헤더 위에 공통 1.4 키 없음 배너가 뜬다.
2. 본문(1~6)과 스크립트(8)는 그대로 읽고, 시각을 눌러 스크립트로 옮겨 갈 수 있다.
3. 질문하기 탭(7.2)을 누른다. 이전 질문 턴(9.2)은 보이고, 질문 입력칸(10.3)과 보내기(10.4)가 막히고 키 없음 안내(10.2)가 뜬다.
4. 추천 질문 칩(10.1)을 눌러도 보내지 않는다.
5. 키 없음 안내(10.2)의 '키 넣으러 가기'를 눌러 UI-5로 간다.

**S-10 이미 분석한 영상을 다시 연다** — [[VA-UC-001#UC-H5]] 기본 흐름 3, 확장 1a
1. UI-1에서 이미 분석한 YouTube 영상의 링크를 다른 URL 형식으로 넣는다.
2. UI-2를 거치지 않고 이 화면이 열리고 짧은 알림(11) '이미 분석한 영상입니다'가 잠깐 뜬다.
3. 패널은 스크립트 탭(7.1)이고 질문 수 배지(7.3)가 저장된 질문 수 3을 보인다.
4. 질문하기 탭(7.2)을 누르면 이전 질문 턴(9.2)이 그대로 보인다.

**S-11 마크다운으로 내보낸다** — [[VA-UC-001#UC-H7]] 기본 흐름 1~3
1. 내보내기(1.2)를 누른다. UI-7이 이 화면 위에 뜬다.
2. UI-7에서 방법을 고르고 주 버튼을 누른다.
3. UI-7이 닫히고 초점이 내보내기(1.2)로 돌아온다. 짧은 알림(11)으로 완료를 알린다.
4. 패널 탭과 선택한 시각(8.2)은 열기 전 그대로다.

**S-12 삭제를 취소하거나 지운다** — [[VA-UC-001#UC-H6]] 기본 흐름 1~4, 확장 3a
1. 휴지통(1.3)을 누른다. UI-6이 뜬다.
2. [취소]를 누른다. UI-6이 닫히고 이 화면이 그대로 남으며 초점은 휴지통(1.3)으로 돌아온다.
3. 휴지통(1.3)을 다시 누르고 UI-6에서 [삭제]를 누른다.
4. 결과가 지워지고 UI-1로 간다. 목록에서 그 행이 사라져 있다.

---

## UI-5 설정

| 항목 | 내용 |
|---|---|
| 화면 설계 | [[VA-UI-001#UI-5]] |
| 경로 | `/settings` |
| 디자인 보드 | Settings |
| 진입 | 헤더 설정 아이콘(모든 페이지) · UI-1 키 없음 배너 [키 넣으러 가기](첫 실행·키 없음·확인 실패) · UI-1 막힌 분석 버튼 · UI-3 막힌 다시 시도 · UI-3·UI-4 키 없음 배너 · UI-4 질문하기의 키 없음 안내 |
| 유스케이스 | [[VA-UC-001#UC-H8]] 기본 흐름 1~4, 확장 1a·3a |

### 배치

```html
<!-- 주 보드: 캔버스 Settings(키 확인됨). 아래는 키 카드의 다른 상태 -->
<div style="width: 1440px; min-height: 1400px; box-sizing: border-box; background: #F6F4EF; display: flex; flex-direction: column;">
<header style="height: 64px; flex-shrink: 0; box-sizing: border-box; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2DDD3; background: #F6F4EF;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 10px; color: #1B1A17; text-decoration: none;">
<span style="width: 30px; height: 30px; border-radius: 8px; background: #1B1A17; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="#F6F4EF" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;">Video Agent</span>
</a>
<nav aria-label="주 메뉴" style="display: flex; align-items: center; gap: 4px;">
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; border-radius: 10px; color: #4A463F; font-size: 15px; font-weight: 600; text-decoration: none;">분석한 영상</a>
<a href="#" aria-label="설정" aria-current="page" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; background: #EAE6DD; color: #1B1A17;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 7h-9"></path><path d="M14 17H5"></path><circle cx="17" cy="17" r="3"></circle><circle cx="7" cy="7" r="3"></circle></svg>
</a>
</nav>
</header>
<main style="flex-grow: 1; box-sizing: border-box; padding: 40px 280px 64px; display: flex; flex-direction: column; gap: 28px;">
<div data-el="1" style="display: flex; flex-direction: column; gap: 8px;">
<h1 style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 40px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em;">설정</h1>
<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #5E5A52;">키와 모델 설정은 이 PC에만 저장됩니다.</p>
</div>
<section aria-labelledby="key-title" data-el="2" style="box-sizing: border-box; padding: 28px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: center; gap: 10px;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4A463F" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="7.5" cy="15.5" r="5.5"></circle><path d="m21 2-9.6 9.6"></path><path d="m15.5 7.5 3 3L22 7l-3-3"></path></svg>
<h2 id="key-title" style="margin: 0; font-size: 19px; font-weight: 600;">OpenAI API 키</h2>
</div>
<span data-el="2.1" style="height: 28px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; gap: 6px; border-radius: 14px; background: #E1EFEC; color: #134E49; font-size: 13px; font-weight: 600;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 3; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 6 9 17l-5-5"></path></svg>
확인됨 · 오늘 14:02
</span>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 14px; font-weight: 600; color: #4A463F;">지금 쓰는 키</span>
<div data-el="2.2" style="height: 48px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; border-radius: 10px; background: #F6F4EF;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 15px; color: #1B1A17;">sk-proj-••••••••••••••••3Fq2</span>
<span style="font-size: 13px; color: #6B665C;">.env에 저장됨</span>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="new-key" style="font-size: 14px; font-weight: 600; color: #4A463F;">새 키로 바꾸기</label>
<div style="display: flex; gap: 10px;">
<span data-el="2.3" style="flex-grow: 1; min-width: 0; display: flex;"><input id="new-key" type="password" placeholder="sk-로 시작하는 키를 붙여 넣으세요" value="" style="width: 100%; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FBFAF7; color: #1B1A17; font-size: 15px;">
</span>
<button data-el="2.4" type="button" style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 18px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">확인하고 저장</button>
</div>
<span data-el="2.6" style="font-size: 13px; line-height: 1.55; color: #6B665C;">붙여 넣으면 가벼운 요청으로 먼저 확인한 뒤 저장합니다. 키는 저장소에 커밋되지 않아요.</span>
</div>
</section>
<section aria-labelledby="model-title" data-el="3" style="box-sizing: border-box; padding: 28px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<h2 id="model-title" style="margin: 0; font-size: 19px; font-weight: 600;">모델</h2>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px;">
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="stt-model" style="font-size: 14px; font-weight: 600; color: #4A463F;">받아쓰기</label>
<span data-el="3.1" style="display: flex;"><select id="stt-model" style="flex-grow: 1; height: 48px; box-sizing: border-box; padding: 0 12px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FBFAF7; color: #1B1A17; font-size: 15px;">
<option>whisper-1</option>
</select></span>
<span data-el="3.2" style="font-size: 13px; line-height: 1.55; color: #6B665C;">분당 $0.006 · 구간 시각을 주는 모델만 고를 수 있어요</span>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="llm-model" style="font-size: 14px; font-weight: 600; color: #4A463F;">요약 · 챕터 · 질문</label>
<span data-el="3.3" style="display: flex;"><select id="llm-model" style="flex-grow: 1; height: 48px; box-sizing: border-box; padding: 0 12px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FBFAF7; color: #1B1A17; font-size: 15px;">
<option>gpt-5-mini</option>
<option>gpt-5.4-mini</option>
<option>gpt-5.4</option>
</select></span>
<span data-el="3.4" style="font-size: 13px; line-height: 1.55; color: #6B665C;">100만 토큰당 입력 $0.25 · 출력 $2.00</span>
</div>
</div>
</section>
<section aria-labelledby="inbox-title" data-el="4" style="box-sizing: border-box; padding: 28px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 14px;">
<h2 id="inbox-title" style="margin: 0; font-size: 19px; font-weight: 600;">로컬 파일 폴더</h2>
<div data-el="4.1" style="height: 48px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 10px; border-radius: 10px; background: #F6F4EF;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4A463F" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"></path></svg>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 15px;">~/video-agent/inbox</span>
<span style="margin-left: auto; font-size: 13px; color: #6B665C;">읽기 전용</span>
</div>
<span style="font-size: 13px; line-height: 1.55; color: #6B665C;">이 폴더의 파일을 읽기만 하고 고치거나 지우지 않아요. 위치는 docker-compose.yml에서 바꿀 수 있습니다.</span>
</section>
<section aria-labelledby="data-title" data-el="5" style="box-sizing: border-box; padding: 28px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 14px;">
<h2 id="data-title" style="margin: 0; font-size: 19px; font-weight: 600;">밖으로 나가는 데이터</h2>
<div data-el="5.1"><table style="width: 100%; border-collapse: collapse; font-size: 15px;">
<thead>
<tr>
<th scope="col" style="width: 120px; padding: 10px 12px 10px 0; border-bottom: 1px solid #E2DDD3; text-align: left; font-size: 13px; font-weight: 600; color: #5E5A52;">어디로</th>
<th scope="col" style="padding: 10px 12px; border-bottom: 1px solid #E2DDD3; text-align: left; font-size: 13px; font-weight: 600; color: #5E5A52;">무엇이</th>
<th scope="col" style="padding: 10px 0 10px 12px; border-bottom: 1px solid #E2DDD3; text-align: left; font-size: 13px; font-weight: 600; color: #5E5A52;">언제</th>
</tr>
</thead>
<tbody>
<tr>
<td style="padding: 12px 12px 12px 0; border-bottom: 1px solid #EFECE5; font-weight: 600;">OpenAI</td>
<td style="padding: 12px; border-bottom: 1px solid #EFECE5;">음성 조각</td>
<td style="padding: 12px 0 12px 12px; border-bottom: 1px solid #EFECE5; color: #4A463F;">자막 없는 영상을 받아쓸 때</td>
</tr>
<tr>
<td style="padding: 12px 12px 12px 0; border-bottom: 1px solid #EFECE5; font-weight: 600;">OpenAI</td>
<td style="padding: 12px; border-bottom: 1px solid #EFECE5;">스크립트 텍스트</td>
<td style="padding: 12px 0 12px 12px; border-bottom: 1px solid #EFECE5; color: #4A463F;">요약 · 챕터 · 추천 질문을 만들 때</td>
</tr>
<tr>
<td style="padding: 12px 12px 12px 0; border-bottom: 1px solid #EFECE5; font-weight: 600;">OpenAI</td>
<td style="padding: 12px; border-bottom: 1px solid #EFECE5;">질문, 앞선 대화, 관련 스크립트</td>
<td style="padding: 12px 0 12px 12px; border-bottom: 1px solid #EFECE5; color: #4A463F;">질문할 때</td>
</tr>
<tr>
<td style="padding: 12px 12px 12px 0; font-weight: 600;">YouTube</td>
<td style="padding: 12px;">영상 주소</td>
<td style="padding: 12px 0 12px 12px; color: #4A463F;">정보 · 자막 · 음성을 받을 때</td>
</tr>
</tbody>
</table></div>
<span data-el="5.2" style="font-size: 13px; line-height: 1.55; color: #6B665C;">원본 영상 파일, 분석 결과, API 키는 이 PC 밖으로 나가지 않습니다.</span>
</section>
<div data-el="6" style="display: flex; justify-content: flex-end; gap: 10px;">
<a data-el="6.1" href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">취소</a>
<a data-el="6.2" href="#" style="height: 44px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">저장</a>
</div>
</main>
</div>
<div class="row">
<div>
<div class="var" style="width: 928px;"><b>키 확인 실패</b> — 새 키가 확인을 통과하지 못했을 때(2.5). 전에 쓰던 키는 그대로 · 캔버스에 없음</div>
<div class="crop" style="width: 928px;">
<section aria-labelledby="key-title" style="box-sizing: border-box; padding: 28px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: center; gap: 10px;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4A463F" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="7.5" cy="15.5" r="5.5"></circle><path d="m21 2-9.6 9.6"></path><path d="m15.5 7.5 3 3L22 7l-3-3"></path></svg>
<h2 id="key-title" style="margin: 0; font-size: 19px; font-weight: 600;">OpenAI API 키</h2>
</div>
<span style="height: 28px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 14px; background: #F7E6E2; color: #7A2A1E; font-size: 13px; font-weight: 600;">확인 실패</span>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 14px; font-weight: 600; color: #4A463F;">지금 쓰는 키</span>
<div style="height: 48px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; border-radius: 10px; background: #F6F4EF;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 15px; color: #1B1A17;">sk-proj-••••••••••••••••3Fq2</span>
<span style="font-size: 13px; color: #6B665C;">.env에 저장됨</span>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="new-key" style="font-size: 14px; font-weight: 600; color: #4A463F;">새 키로 바꾸기</label>
<div style="display: flex; gap: 10px;">
<span style="flex-grow: 1; min-width: 0; display: flex;"><input id="new-key" type="password" placeholder="sk-로 시작하는 키를 붙여 넣으세요" value="sk-proj-wrongkey000000000000" style="width: 100%; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 10px; border: 1px solid #A33A2B; background: #FBFAF7; color: #1B1A17; font-size: 15px;">
</span>
<button type="button" style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 18px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">확인하고 저장</button>
</div>
<span data-el="2.5" role="alert" style="font-size: 13px; line-height: 1.55; color: #A33A2B;">키를 확인하지 못했어요 — 인증 실패</span>
<span style="font-size: 13px; line-height: 1.55; color: #6B665C;">붙여 넣으면 가벼운 요청으로 먼저 확인한 뒤 저장합니다. 키는 저장소에 커밋되지 않아요.</span>
</div>
</section>
</div>
</div>
</div>
<div class="row">
<div>
<div class="var" style="width: 928px;"><b>키 없음</b> — 저장된 키가 없을 때. 지금 쓰는 키(2.2)가 없고 라벨이 '키 넣기' · 캔버스에 없음</div>
<div class="crop" style="width: 928px;">
<section aria-labelledby="key-title" style="box-sizing: border-box; padding: 28px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: center; gap: 10px;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4A463F" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><circle cx="7.5" cy="15.5" r="5.5"></circle><path d="m21 2-9.6 9.6"></path><path d="m15.5 7.5 3 3L22 7l-3-3"></path></svg>
<h2 id="key-title" style="margin: 0; font-size: 19px; font-weight: 600;">OpenAI API 키</h2>
</div>
<span style="height: 28px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 14px; background: #F7E6E2; color: #7A2A1E; font-size: 13px; font-weight: 600;">키 없음</span>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="new-key" style="font-size: 14px; font-weight: 600; color: #4A463F;">키 넣기</label>
<div style="display: flex; gap: 10px;">
<span style="flex-grow: 1; min-width: 0; display: flex;"><input id="new-key" type="password" placeholder="sk-로 시작하는 키를 붙여 넣으세요" value="" style="width: 100%; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FBFAF7; color: #1B1A17; font-size: 15px;">
</span>
<button type="button" style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 18px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">확인하고 저장</button>
</div>
<span style="font-size: 13px; line-height: 1.55; color: #6B665C;">붙여 넣으면 가벼운 요청으로 먼저 확인한 뒤 저장합니다. 키는 저장소에 커밋되지 않아요.</span>
</div>
</section>
</div>
</div>
</div>
```

### 요소

| # | 이름 | 종류 | 보여주는 것 | 누르면 |
|---|---|---|---|---|
| 1 | 제목과 안내 | 텍스트 | 페이지 제목 '설정'과 안내 '키와 모델 설정은 이 PC에만 저장됩니다.' | — |
| 2 | OpenAI API 키 카드 | 영역 | 열쇠 아이콘 + 카드 제목 'OpenAI API 키'. 키 상태(2.1) · 지금 쓰는 키(2.2) · 새 키 입력(2.3~2.6) | — |
| 2.1 | 키 상태 배지 | 배지 | 카드 머리 줄 오른쪽 끝. 확인됨: 체크 + '확인됨 · {확인 시각}' / 키 없음: '키 없음' / 확인 실패: '확인 실패' | — |
| 2.2 | 지금 쓰는 키 | 상자 | 라벨 '지금 쓰는 키' 아래 읽기 전용 값 상자. 앞부분과 끝 4자만 보이는 가린 키 + 오른쪽 저장 위치 캡션 '.env에 저장됨'(고정). 저장된 키가 없으면 그리지 않는다 | — |
| 2.3 | 새 키 입력칸 | 입력 | 라벨 '새 키로 바꾸기'(키 없음이면 '키 넣기'). password 형식, placeholder 'sk-로 시작하는 키를 붙여 넣으세요' | — |
| 2.4 | 확인하고 저장 | 버튼 | 입력칸 오른쪽 공통 1.8의 보조 버튼. 확인하는 동안 대기 표시 | 2.3의 키를 가벼운 요청으로 확인한다. 통과 → 저장하고 2.1 '확인됨 · {시각}'·2.2 갱신 / 실패 → 2.1 '확인 실패'·2.5 표시 |
| 2.5 | 키 확인 오류 | 텍스트 | 확인에 실패했을 때만 입력칸 바로 아래 한 줄. '키를 확인하지 못했어요 — {이유}'. 이유는 형식 오류·인증 실패·잔액 없음 | — |
| 2.6 | 키 도움말 | 텍스트 | '붙여 넣으면 가벼운 요청으로 먼저 확인한 뒤 저장합니다. 키는 저장소에 커밋되지 않아요.' | — |
| 3 | 모델 카드 | 영역 | 카드 제목 '모델'. 두 칸 나란히: 왼쪽 받아쓰기, 오른쪽 요약 · 챕터 · 질문 | — |
| 3.1 | 받아쓰기 모델 | 선택 | 라벨 '받아쓰기'. select, 선택지 whisper-1 하나 | 선택지 목록을 연다 |
| 3.2 | 받아쓰기 모델 도움말 | 텍스트 | '분당 {단가} · 구간 시각을 주는 모델만 고를 수 있어요'. 단가는 3.1에서 고른 모델 값 | — |
| 3.3 | 요약 모델 | 선택 | 라벨 '요약 · 챕터 · 질문'. select, 선택지 gpt-5-mini · gpt-5.4-mini · gpt-5.4 | 선택지 목록을 연다. 고르면 3.4가 그 모델 값으로 바뀐다 |
| 3.4 | 요약 모델 도움말 | 텍스트 | '100만 토큰당 입력 {단가} · 출력 {단가}'. 3.3에서 고른 모델 값 | — |
| 4 | 로컬 파일 폴더 카드 | 영역 | 카드 제목 '로컬 파일 폴더'와 안내 '이 폴더의 파일을 읽기만 하고 고치거나 지우지 않아요. 위치는 docker-compose.yml에서 바꿀 수 있습니다.' | — |
| 4.1 | 폴더 경로 | 상자 | 읽기 전용 값 상자. 폴더 아이콘 + `{inbox 경로}` + 오른쪽 캡션 '읽기 전용'. 바꾸는 입력칸 없음 | — |
| 5 | 밖으로 나가는 데이터 카드 | 영역 | 카드 제목 '밖으로 나가는 데이터', 표(5.1), 끝 문장(5.2) | — |
| 5.1 | 데이터 표 | 표 | 열 어디로 · 무엇이 · 언제. 고정 네 줄: OpenAI · 음성 조각 · 자막 없는 영상을 받아쓸 때 / OpenAI · 스크립트 텍스트 · 요약 · 챕터 · 추천 질문을 만들 때 / OpenAI · 질문, 앞선 대화, 관련 스크립트 · 질문할 때 / YouTube · 영상 주소 · 정보 · 자막 · 음성을 받을 때 | — |
| 5.2 | 나가지 않는 것 | 텍스트 | '원본 영상 파일, 분석 결과, API 키는 이 PC 밖으로 나가지 않습니다.' | — |
| 6 | 버튼 줄 | 영역 | 페이지 맨 아래 오른쪽 정렬. 왼쪽 취소, 오른쪽 끝 저장 | — |
| 6.1 | 취소 | 버튼 | 공통 1.8의 보조 버튼 | 모델 변경을 버리고 [[#UI-1]]. 키는 되돌리지 않는다 |
| 6.2 | 저장 | 버튼 | 공통 1.8의 주 버튼 | 모델 선택(3.1·3.3)을 저장하고 [[#UI-1]] |

### 규칙

- 페이지이고 주소는 `/settings`다. 한 화면보다 길어 헤더 아래 내용 영역이 스크롤된다(VA-UI-001 4.1절).
- 공통 1.1 헤더에서 설정 아이콘이 현재 위치로 표시된다(aria-current="page"). '분석한 영상' 메뉴는 그대로 보이지만 현재 위치로 표시하지 않는다.
- 위에서 아래로 제목(1) · 키 카드(2) · 모델 카드(3) · 로컬 파일 폴더 카드(4) · 밖으로 나가는 데이터 카드(5) · 버튼 줄(6) 순서다. 카드·값 상자·입력칸·select·배지·버튼 모양은 VA-UI-001 3장과 4.2절을 따른다.
- 공통 1.4 키 없음 배너는 이 화면에 두지 않는다. 키가 없거나 확인에 실패한 사실은 2.1과 2.5가 보인다 (VA-UI-001에 없음)
- 2.1은 저장된 키(2.2)의 마지막 확인 결과다. 2.4가 실패한 직후에만 새로 넣은 키의 결과를 보인다. 키는 앱이 시작할 때와 분석 버튼을 누를 때(VA-UI-001 UI-1 규칙), 그리고 확인하고 저장(2.4)을 누를 때 확인한다. 이 화면을 여는 것만으로는 다시 확인하지 않는다 (VA-UI-001에 없음)
- 2.1 확인됨은 청록 톤 배지에 체크 아이콘과 '확인됨 · {확인 시각}'이다(VA-UI-001 4.2절 배지). {확인 시각}은 UI-1 목록 행처럼 '{날짜 또는 오늘 HH:MM}'으로 쓴다 (VA-UI-001에 없음)
- 2.1 키 없음은 '키 없음', 확인 실패는 '확인 실패'이고 둘 다 위험 톤(VA-UI-001 3.1절 위험 바탕·위험 진함)에 체크 아이콘이 없다. 디자인 보강 전 임시 모양이다 (VA-UI-001에 없음)
- 2.2는 입력칸이 아니라 읽기 전용 값 상자다. 앞부분과 끝 4자만 보이게 가리고 전체를 다시 보여 주지 않는다.
- 서버도 2.2에 쓸 가린 값만 화면에 준다 (VA-UI-001에 없음)
- 2.2 오른쪽 캡션은 키를 저장한 곳이고 늘 '.env에 저장됨'이다. 이 화면에서 넣은 키도 앱이 `.env` 파일의 그 줄에 쓴다([[VA-INFRA-001#C6]]). 모델 선택도 같은 파일에 쓴다.
- 환경 변수에 키가 이미 있으면 그 키를 2.2에 보이고 2.1은 그 키의 확인 결과다([[VA-UC-001#UC-H8]] 1a) (VA-UI-001에 없음)
- 환경 변수 키가 있을 때 2.2 캡션과, 2.4로 새 키를 저장하면 어느 키를 쓸지는 VA-UI-001 8장의 키 저장 위치 결정을 따른다.
- 저장된 키가 없으면 2.2를 그리지 않고, 2.1은 '키 없음', 2.3 라벨은 '키 넣기'로 보인다 (VA-UI-001에 없음)
- 2.3은 password 형식이고 placeholder는 'sk-로 시작하는 키를 붙여 넣으세요'다.
- 2.3이 비어 있으면 2.4를 눌러도 확인 요청을 보내지 않는다 (VA-UI-001에 없음)
- 확인하고 저장(2.4)은 **키만** 다룬다. 가벼운 요청으로 먼저 확인하고, 통과하면 곧바로 저장하고 2.1을 '확인됨 · {시각}'으로 바꾼다. 키는 저장소에 커밋되지 않는다.
- 확인하는 동안 2.3과 2.4를 잠그고 2.4에 대기 표시를 한다. 2.1은 결과가 올 때까지 그대로다 (VA-UI-001에 없음)
- 통과하면 2.2가 새 키의 가린 값으로 바뀌고, 2.3을 비우고, 2.5를 숨긴다 (VA-UI-001에 없음)
- 실패하면 키를 저장하지 않는다. 2.1을 '확인 실패'로 바꾸고 2.5에 이유(형식 오류·인증 실패·잔액 없음)를 보인다([[VA-UC-001#UC-H8]] 3a). 2.2는 전에 쓰던 키 그대로다.
- 2.4가 실패해도 저장된 키와 그 확인 결과는 바뀌지 않는다. 키 없음 배너(공통 1.4)와 분석 버튼·UI-4 질문 입력 막힘은 저장된 키의 확인 결과만 따르고, 이 화면을 다시 열면 2.1은 저장된 키의 마지막 확인 결과로 돌아가고 2.5는 저장된 키가 확인에 실패했을 때만 그 이유를 보인다 (VA-UI-001에 없음)
- 2.5는 입력칸 바로 아래 한 줄이고 화면을 바꾸지 않는다(VA-UI-001 4.5절 입력 오류). 문구 '키를 확인하지 못했어요 — {이유}'는 UI-1 배너 문구를 그대로 썼다 (VA-UI-001에 없음)
- 앱 시작이나 분석 버튼에서 저장된 키의 확인이 실패했으면, 이 화면을 열 때 2.1은 '확인 실패'이고 2.5에 그 이유가 보인다 (VA-UI-001에 없음)
- 키 없음·확인 중·확인 실패일 때 키 카드(2) 모양은 보드에 없다. 그때의 2.1 배지·2.2 숨김·2.3 라벨·확인 중 잠금과 대기 표시·2.5 모양은 디자인 보강 전 임시 규칙이다(VA-UI-001 8장).
- 받아쓰기 모델(3.1)은 whisper-1 하나다. 구간 시각을 주는 모델만 목록에 나온다([[VA-INFRA-001#C3]]).
- 요약 모델(3.3)은 gpt-5-mini(첫 값) · gpt-5.4-mini · gpt-5.4 중에서 고른다.
- 처음 열면 3.1과 3.3에 저장된 모델이 골라져 있다 (VA-UI-001에 없음)
- 3.2와 3.4의 단가는 고른 모델의 값이다(보드는 gpt-5-mini 값 하나만 있다). UI-2 예상 비용도 같은 단가를 쓴다.
- 3.1·3.3을 바꿔도 저장(6.2)을 누르기 전에는 저장되지 않는다. 화면에서 모델을 바꾸는 유스케이스는 아직 없다(VA-UI-001 8장).
- 폴더 경로(4.1)는 경로와 '읽기 전용'만 보이고 바꾸는 입력칸이 없다. 위치는 docker-compose.yml에서 바꾼다고 카드(4)에 안내한다([[VA-INFRA-001#C4]]).
- 데이터 표(5.1)는 고정 네 줄이고 누를 것이 없다. 끝에 5.2를 둔다. 이 목록은 [[VA-PRD-001#N3]]·[[VA-INFRA-001#C9]]보다 넓다(VA-UI-001 8장).
- 저장(6.2)은 **모델 선택**을 저장하고 UI-1로 간다. 취소(6.1)는 모델 변경을 버리고 UI-1로 간다. 키는 이미 2.4에서 저장됐으므로 6.1이 되돌리지 않는다.
- 저장하지 않은 모델 변경이 있을 때 헤더 로고나 '분석한 영상'으로 떠나면 취소(6.1)와 같이 버린다 (VA-UI-001에 없음)

### 시나리오

**S-1 첫 실행에서 키를 넣는다** — [[VA-UC-001#UC-H8]] 기본 흐름 1~4
1. UI-1 첫 실행 상태에서 공통 1.4 키 없음 배너의 [키 넣으러 가기]를 눌러 들어온다.
2. 2.1이 '키 없음'이고 지금 쓰는 키(2.2)는 없다. 데이터 표(5.1)에서 무엇이 OpenAI로 나가는지 읽는다.
3. 새 키 입력칸(2.3)에 키를 붙여 넣는다. 글자는 가려진다.
4. 확인하고 저장(2.4)을 누른다. 2.3과 2.4가 잠기고 2.4에 대기 표시가 뜬다.
5. 확인이 통과한다. 키가 저장되고 2.1이 '확인됨 · 오늘 14:02'로 바뀌고, 2.2에 가린 새 키가 보이고, 2.3은 비워진다.
6. 저장(6.2)을 누른다. UI-1로 돌아가면 배너가 사라지고 두 분석 버튼이 켜져 있다.

**S-2 붙여 넣은 키가 틀렸다** — [[VA-UC-001#UC-H8]] 확장 3a
1. 키가 저장돼 확인된 상태(2.1 '확인됨')에서 새 키 입력칸(2.3)에 다른 키를 붙여 넣고 확인하고 저장(2.4)을 누른다.
2. 확인이 인증 실패로 끝난다. 키는 저장되지 않는다.
3. 2.1이 '확인 실패'로 바뀌고 2.5에 '키를 확인하지 못했어요 — 인증 실패'가 보인다. 2.2는 전에 쓰던 키 그대로이고, 분석과 질문은 그 키를 계속 쓴다.
4. 2.3의 키를 고쳐 붙이고 2.4를 다시 누른다.
5. 통과하면 2.5가 사라지고 2.1이 '확인됨 · {시각}'으로 바뀐다.

**S-3 저장된 키가 확인에 실패했다** — [[VA-UC-001#UC-H8]] 확장 3a
1. 앱이 시작할 때 키 확인이 잔액 없음으로 실패해 UI-1에 공통 1.4 키 없음 배너 '키를 확인하지 못했어요 — 잔액 없음'이 떠 있다.
2. 배너의 [키 넣으러 가기]를 눌러 들어온다.
3. 2.1은 '확인 실패', 2.2는 그 키의 가린 값이고, 2.5에 '키를 확인하지 못했어요 — 잔액 없음'이 보인다.
4. 다른 키를 2.3에 붙여 넣고 2.4를 누른다. 통과하면 S-1의 5~6과 같다.

**S-4 환경 변수에 키가 이미 있다** — [[VA-UC-001#UC-H8]] 확장 1a
1. 헤더 설정 아이콘을 눌러 들어온다.
2. 2.1이 '확인됨 · {시각}'이고 2.2에 환경 변수 키의 가린 값과 저장 위치 캡션이 보인다.
3. 넣을 키가 없으므로 취소(6.1)를 눌러 UI-1로 돌아간다.

**S-5 요약 모델을 바꾼다** — [[VA-UC-001#UC-H8]] 트리거(설정 화면을 열었다). 모델 바꾸기는 유스케이스 갱신 요청 중(VA-UI-001 8장)
1. 헤더 설정 아이콘을 눌러 들어온다. 요약 모델(3.3)에 저장된 gpt-5-mini가 골라져 있다.
2. 3.3에서 gpt-5.4를 고른다. 3.4의 단가가 gpt-5.4 값으로 바뀐다.
3. 저장(6.2)을 누른다. 모델 선택이 저장되고 UI-1로 간다.
4. 다음 분석의 사전 안내(UI-2) 예상 비용이 이 단가로 계산된다.

**S-6 키를 바꾼 뒤 취소한다** — [[VA-UC-001#UC-H8]] 기본 흐름 2~4
1. 새 키 입력칸(2.3)에 새 키를 넣고 2.4를 누른다. 확인이 통과해 키가 이때 저장된다.
2. 요약 모델(3.3)을 다른 모델로 바꾼다.
3. 취소(6.1)를 누른다. 모델 변경은 버려지고 UI-1로 간다.
4. 키는 되돌려지지 않는다. 다음 분석과 질문에 새 키가 쓰인다.

---

## UI-6 삭제 확인

| 항목 | 내용 |
|---|---|
| 화면 설계 | [[VA-UI-001#UI-6]] |
| 경로 | (다이얼로그) |
| 디자인 보드 | Delete |
| 진입 | UI-1 목록 행 휴지통 · UI-4 머리 휴지통 |
| 유스케이스 | [[VA-UC-001#UC-H6]] 기본 흐름 1~4 · 확장 3a |

### 배치

```html
<!-- 주 보드: 캔버스 Delete(UI-1 홈 위). 아래는 상태 보드 -->
<div style="width: 1440px; height: 960px; position: relative; overflow: hidden; background: #F6F4EF;">
<div style="position: absolute; left: 0; top: 0; width: 1440px; height: 960px;">
<div style="width: 1440px; height: 960px; box-sizing: border-box; background: #F6F4EF; display: flex; flex-direction: column; overflow: hidden;">
<header style="height: 64px; flex-shrink: 0; box-sizing: border-box; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2DDD3; background: #F6F4EF;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 10px; color: #1B1A17; text-decoration: none;">
<span style="width: 30px; height: 30px; border-radius: 8px; background: #1B1A17; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="#F6F4EF" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;">Video Agent</span>
</a>
<nav aria-label="주 메뉴" style="display: flex; align-items: center; gap: 4px;">
<a href="#" aria-current="page" style="height: 44px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; border-radius: 10px; background: #EAE6DD; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">분석한 영상</a>
<a href="#" aria-label="설정" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 7h-9"></path><path d="M14 17H5"></path><circle cx="17" cy="17" r="3"></circle><circle cx="7" cy="7" r="3"></circle></svg>
</a>
</nav>
</header>
<main style="flex-grow: 1; min-height: 0; box-sizing: border-box; padding: 44px 160px 0; display: flex; flex-direction: column; gap: 44px;">
<section aria-labelledby="home-title" style="display: flex; flex-direction: column; gap: 24px;">
<div style="display: flex; flex-direction: column; gap: 8px;">
<h1 id="home-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 40px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em;">어떤 영상을 읽어 볼까요?</h1>
<p style="margin: 0; font-size: 16px; line-height: 1.6; color: #5E5A52;">YouTube 링크를 붙여 넣거나 inbox 폴더의 파일을 고르세요. 분석 결과는 이 PC에만 저장됩니다.</p>
</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px;">
<div style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #E1EFEC; color: #0F6E68; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">YouTube 링크</span>
<span style="font-size: 13px; color: #6B665C;">watch · youtu.be · shorts 주소를 받아요</span>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">
<label for="yt-url" style="font-size: 14px; font-weight: 600; color: #4A463F;">영상 주소</label>
<div style="display: flex; gap: 10px;">
<span style="flex-grow: 1; min-width: 0; display: flex;"><input id="yt-url" type="url" placeholder="https://www.youtube.com/watch?v=…" value="" style="width: 100%; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FBFAF7; color: #1B1A17; font-size: 15px;"></span>
<a href="#" aria-disabled="false" style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">분석</a>
</div>
</div>
<p style="margin: 0; font-size: 13px; line-height: 1.55; color: #6B665C;">자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.</p>
</div>
<div style="box-sizing: border-box; padding: 24px; border-radius: 16px; border: 1px solid #E2DDD3; background: #FFFFFF; display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: center; gap: 12px;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 17px; font-weight: 600;">내 파일</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #6B665C;">~/video-agent/inbox</span>
</div>
</div>
<div role="group" aria-label="inbox 파일" style="display: flex; flex-direction: column; gap: 6px;">
<button type="button" aria-pressed="true" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #0F6E68; background: #E1EFEC; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #0F6E68; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: #0F6E68;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">workshop_0912.mp4</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">2:30:00</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">1.8 GB</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #E2DDD3; background: #FBFAF7; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: transparent;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">meetup_0901.mp4</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">1:58:20</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">1.4 GB</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 44px; box-sizing: border-box; padding: 0 12px; display: flex; align-items: center; gap: 12px; border-radius: 10px; border: 1px solid #E2DDD3; background: #FBFAF7; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="width: 18px; height: 18px; flex-shrink: 0; box-sizing: border-box; border-radius: 50%; border: 2px solid #948D80; display: flex; align-items: center; justify-content: center;">
<span style="width: 8px; height: 8px; border-radius: 50%; background: transparent;"></span>
</span>
<span style="flex-grow: 1; min-width: 0; font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">interview_0903.m4a</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: #5E5A52;">1:04:12</span>
<span style="width: 60px; font-size: 13px; color: #6B665C; text-align: right;">58 MB</span>
</button>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
<span style="font-size: 13px; color: #6B665C;">mp4 · mkv · mov · webm · mp3 · m4a · wav</span>
<a href="#" aria-disabled="false" style="height: 44px; flex-shrink: 0; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">선택한 파일 분석</a>
</div>
</div>
</div>
</section>
<section aria-labelledby="list-title" style="display: flex; flex-direction: column; gap: 12px;">
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="list-title" tabindex="-1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">분석한 영상</h2>
<span style="font-size: 14px; color: #6B665C;">5개</span>
</div>
<span style="font-size: 13px; color: #6B665C;">최근 순</span>
</div>
<div style="border-top: 1px solid #E2DDD3; display: flex; flex-direction: column;">
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">벡터 검색 튜닝 실전</span>
<span style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">38:05</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 600; color: #6B665C;">대기 중 · 1번째</span>
</span>
</a>
<a href="#" aria-label="벡터 검색 튜닝 실전 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</span>
<span style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">50:12</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 400; color: #6B665C;">오늘 14:08 분석</span>
</span>
</a>
<a href="#" aria-label="RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">workshop_0912.mp4</span>
<span style="font-size: 13px; color: #6B665C;">로컬 파일</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">2:30:00</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 600; color: #0F6E68;">받아쓰기 중 · 12 / 30</span>
<span style="width: 160px; height: 4px; border-radius: 2px; background: #E2DDD3; display: block; overflow: hidden;">
<span style="width: 40%; height: 4px; display: block; background: #0F6E68;"></span>
</span>
</span>
</a>
<a href="#" aria-label="workshop_0912.mp4 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M7 3v18"></path><path d="M17 3v18"></path><path d="M3 7.5h4"></path><path d="M3 12h18"></path><path d="M3 16.5h4"></path><path d="M17 7.5h4"></path><path d="M17 16.5h4"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">meetup_0901.mp4</span>
<span style="font-size: 13px; color: #6B665C;">로컬 파일</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">1:58:20</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 600; color: #A33A2B;">받아쓰기 16 / 24에서 멈춤</span>
</span>
</a>
<a href="#" aria-label="meetup_0901.mp4 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
<div style="box-sizing: border-box; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #E2DDD3;">
<a href="#" style="flex-grow: 1; min-width: 0; min-height: 64px; box-sizing: border-box; padding: 10px 0; display: flex; align-items: center; gap: 16px; color: #1B1A17; text-decoration: none;">
<span style="width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px; background: #EFECE5; color: #4A463F; display: flex; align-items: center; justify-content: center;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
</span>
<span style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px;">
<span style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">LLM 에이전트 설계 패턴 정리</span>
<span style="font-size: 13px; color: #6B665C;">YouTube · [채널명]</span>
</span>
<span style="width: 88px; flex-shrink: 0; font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #4A463F; text-align: right;">1:12:40</span>
<span style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
<span style="font-size: 14px; font-weight: 400; color: #6B665C;">9월 12일 분석</span>
</span>
</a>
<a href="#" aria-label="LLM 에이전트 설계 패턴 정리 분석 결과 삭제" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #6B665C;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
</div>
</section>
</main>
</div>
</div>
<div style="position: absolute; left: 0; top: 0; width: 1440px; height: 960px; box-sizing: border-box; padding-top: 180px; display: flex; justify-content: center; align-items: flex-start; background: rgba(27, 26, 23, 0.52);">
<div role="alertdialog" aria-modal="true" aria-labelledby="del-title" aria-describedby="del-desc" data-el="1" style="width: 540px; box-sizing: border-box; padding: 32px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 28px 80px rgba(27, 26, 23, 0.32); display: flex; flex-direction: column; gap: 20px;">
<span data-el="1.1" style="width: 48px; height: 48px; border-radius: 12px; background: #F7E6E2; color: #A33A2B; display: flex; align-items: center; justify-content: center;">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 8px;">
<h2 id="del-title" data-el="1.2" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 26px; line-height: 1.3; font-weight: 600; letter-spacing: -0.01em;">분석 결과를 지울까요?</h2>
<p id="del-desc" data-el="1.3" style="margin: 0; font-size: 16px; line-height: 1.6; color: #4A463F;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</p>
</div>
<div data-el="2" style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;">
<div data-el="2.1" style="box-sizing: border-box; padding: 16px; border-radius: 12px; background: #F7E6E2; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #7A2A1E;">지워지는 것</span>
<span style="font-size: 14px; line-height: 1.6; color: #5C2418;">스크립트, 핵심 요약, 챕터, 추천 질문, 질문 기록 3개</span>
</div>
<div data-el="2.2" style="box-sizing: border-box; padding: 16px; border-radius: 12px; background: #F6F4EF; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #4A463F;">남는 것</span>
<span style="font-size: 14px; line-height: 1.6; color: #4A463F;">YouTube 원본 영상. 다시 넣으면 처음부터 분석합니다.</span>
</div>
</div>
<div data-el="3" style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
<a data-el="3.2" href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">취소</a>
<a data-el="3.3" href="#" style="height: 44px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #A33A2B; color: #FFFFFF; font-size: 15px; font-weight: 600; text-decoration: none;">삭제</a>
</div>
</div>
</div>
</div>
<div class="var"><b>지우지 못함</b> — 지우기에 실패했을 때 버튼 줄 왼쪽에 실패 한 줄(3.1) · 캔버스에 없음</div>
<div class="crop dim">
<div role="alertdialog" aria-modal="true" aria-labelledby="del-title" aria-describedby="del-desc" style="width: 540px; box-sizing: border-box; padding: 32px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 28px 80px rgba(27, 26, 23, 0.32); display: flex; flex-direction: column; gap: 20px;">
<span style="width: 48px; height: 48px; border-radius: 12px; background: #F7E6E2; color: #A33A2B; display: flex; align-items: center; justify-content: center;">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</span>
<div style="display: flex; flex-direction: column; gap: 8px;">
<h2 id="del-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 26px; line-height: 1.3; font-weight: 600; letter-spacing: -0.01em;">분석 결과를 지울까요?</h2>
<p id="del-desc" style="margin: 0; font-size: 16px; line-height: 1.6; color: #4A463F;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</p>
</div>
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;">
<div style="box-sizing: border-box; padding: 16px; border-radius: 12px; background: #F7E6E2; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #7A2A1E;">지워지는 것</span>
<span style="font-size: 14px; line-height: 1.6; color: #5C2418;">스크립트, 핵심 요약, 챕터, 추천 질문, 질문 기록 3개</span>
</div>
<div style="box-sizing: border-box; padding: 16px; border-radius: 12px; background: #F6F4EF; display: flex; flex-direction: column; gap: 6px;">
<span style="font-size: 13px; font-weight: 600; color: #4A463F;">남는 것</span>
<span style="font-size: 14px; line-height: 1.6; color: #4A463F;">YouTube 원본 영상. 다시 넣으면 처음부터 분석합니다.</span>
</div>
</div>
<div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
<span data-el="3.1" role="alert" style="margin-right: auto; font-size: 14px; line-height: 1.5; color: #A33A2B;">분석 결과를 지우지 못했어요 — 권한 없음</span>
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">취소</a>
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #A33A2B; color: #FFFFFF; font-size: 15px; font-weight: 600; text-decoration: none;">삭제</a>
</div>
</div>
</div>
```

### 요소

| # | 이름 | 종류 | 보여주는 것 | 누르면 |
|---|---|---|---|---|
| 1 | 다이얼로그 | 다이얼로그 | UI-1 또는 UI-4 위에 뜨는 경고 다이얼로그. 틀은 공통 1.2 다이얼로그 틀의 UI-6 판이다 — 닫기(X) 대신 머리에 아이콘 타일 1.1. 이름은 1.2, 설명은 1.3 | 덮개(바깥)를 눌러도 닫히지 않는다 · Esc는 3.2와 같다 |
| 1.1 | 아이콘 타일 | 아이콘 | 빨간 톤 타일 안의 휴지통 아이콘. 아이콘은 aria-hidden | — |
| 1.2 | 제목 | 텍스트 | '분석 결과를 지울까요?'. 다이얼로그 이름(aria-labelledby) | — |
| 1.3 | 대상 제목 | 텍스트 | 지울 영상의 제목. UI-1 목록 행·UI-4 제목과 같은 값. 다이얼로그 설명(aria-describedby) | — |
| 2 | 지울 것과 남는 것 | 영역 | 두 칸 나란히. 왼쪽 2.1, 오른쪽 2.2 | — |
| 2.1 | 지워지는 것 | 상자 | 빨간 톤 상자. 라벨 '지워지는 것'과 '스크립트, 핵심 요약, 챕터, 추천 질문, 질문 기록 {n}개'. 진행 중·실패 영상이면 '임시 음성 파일'이 더해진다 | — |
| 2.2 | 남는 것 | 상자 | 회색 톤 상자. 라벨 '남는 것'과 '{YouTube 원본 영상 또는 inbox 원본 파일}. 다시 넣으면 처음부터 분석합니다.' | — |
| 3 | 버튼 줄 | 영역 | 오른쪽 정렬. 3.2 취소, 오른쪽 끝 3.3. 지우기에 실패했을 때만 왼쪽 끝에 3.1 | — |
| 3.1 | 실패 한 줄 | 텍스트 | 지우기에 실패했을 때만 보인다. '분석 결과를 지우지 못했어요 — {이유}'. 무엇이 왜 안 됐는지 한 줄(VA-UI-001 4.5 문구 규칙). role alert | — |
| 3.2 | 취소 | 버튼 | 보조 버튼 '취소'(공통 1.8). 열리면 처음 초점이 여기 있다 | 아무것도 지우지 않고 닫힘. 연 화면 그대로 — [[#UI-1]] 또는 [[#UI-4]]. 초점은 연 휴지통으로 |
| 3.3 | 삭제 | 버튼 | 위험 버튼 '삭제'(공통 1.8) | 그 영상에 딸린 저장물을 모두 지우고 닫힘. 진행 중이면 작업을 먼저 멈춘다. [[#UI-1]]로 가고(UI-4에서 열었으면 방문 기록을 바꿔치기) 목록에서 그 행이 사라진다. 실패하면 열린 채 3.1을 보이고 3.2·3.3을 다시 푼다 |

### 규칙

- UI-1 목록 행 휴지통(aria-label '{제목} 분석 결과 삭제')이나 UI-4 머리 휴지통(aria-label '분석 결과 삭제')을 누르면 연 페이지 위에 뜬다. 주소는 바뀌지 않고 뒤 페이지는 덮개 아래 그대로 남는다. 주소가 없으므로 새로 고치면 1이 닫히고 연 페이지(UI-1 또는 UI-4)가 열린다(VA-UI-001 6장)
- 1은 경고 다이얼로그다. role="alertdialog"·aria-modal="true"이고, 이름은 1.2를 aria-labelledby로, 설명은 1.3을 aria-describedby로 잇는다
- 닫기(X)가 없다. 덮개(바깥)를 눌러도 닫히지 않고, Esc는 3.2와 같다(VA-UI-001 4.3)
- 열리면 처음 초점은 3.2다. 초점은 1 밖으로 나가지 않고, 3.2나 Esc로 닫히면 연 휴지통 버튼으로 돌아간다
- 1.3은 제목 바로 아래에 지울 영상의 제목을 보인다. 사용자가 무엇을 지우는지 확인하는 자리다([[VA-UC-001#UC-H6]] 기본 흐름 2)
- 2.1은 '스크립트, 핵심 요약, 챕터, 추천 질문, 질문 기록 {n}개'다. {n}은 그 영상의 질문 수다
- 분석이 끝나지 않은 영상(진행 중·실패)이면 2.1에 '임시 음성 파일'을 더한다
- 2.2는 YouTube 영상이면 'YouTube 원본 영상', 로컬 파일이면 'inbox 원본 파일'이고 뒤에 '다시 넣으면 처음부터 분석합니다.'를 붙인다. 로컬 파일 문구는 보드에 없다
- inbox의 원본 파일은 지우지 않는다. 앱은 inbox 폴더를 읽기만 한다([[VA-INFRA-001#C4]], [[VA-UC-001#UC-H6]] 성공 보장)
- 3.3을 누르면 그 영상에 딸린 저장물(스크립트·요약·챕터·추천 질문·질문 기록·내려받은 음성)을 모두 지우고 목록에서 뺀다. 다른 영상의 결과는 건드리지 않는다([[VA-UC-001#UC-H6]] 성공 보장·최소 보장)
- 진행 중인 영상은 작업을 먼저 멈추고 지운다. 실패한 영상은 보존된 조각까지 지운다. 분석 취소 버튼이 따로 없어 분석을 멈추는 길은 이것뿐이다(VA-UI-001 7장 13). [[VA-UC-001#UC-H6]] 사전조건과 확장에 이 경우를 넣어 달라고 요청해 두었다(VA-UI-001 8장)
- 지우고 나면 1을 닫고 UI-1로 간다. UI-1에서 열었으면 그 행이 사라지고 목록 머리의 개수가 하나 줄어든다. UI-4에서 열었으면 그 영상이 빠진 UI-1이 열린다
- UI-4에서 열어 지운 뒤 UI-1로 갈 때는 방문 기록을 바꿔치기해서 뒤로 가기가 지운 영상의 UI-4 주소로 돌아오지 않게 한다 (VA-UI-001에 없음)
- 마지막 영상을 지워 목록이 비면 UI-1은 목록 대신 빈 상태 상자(공통 1.7)를 보인다
- 3.2와 Esc는 아무것도 지우지 않고 닫는다. 연 화면(UI-1 또는 UI-4)이 그대로 남는다. 보드는 두 버튼을 모두 UI-1로 이었지만 규칙은 연 화면이다(VA-UI-001 7장 15)
- 되돌릴 수 없는 동작이라 3.3은 위험 버튼, 3.2는 보조 버튼이다(공통 1.8). 3 안에서 3.2가 3.3 왼쪽, 3.3이 오른쪽 끝이다
- 키 없음 배너(공통 1.4)가 떠 있어도 휴지통과 이 다이얼로그는 막지 않는다. VA-UI-001이 키가 없을 때 막는 것은 분석 버튼과 UI-4 질문 입력뿐이다 (VA-UI-001에 없음)
- 모양 값(폭·위 여백·타일·상자 간격·색·글자)은 여기 적지 않는다. VA-UI-001 3장에서 삭제·UI-6을 적은 줄과 4.2 위험 버튼·보조 버튼, 4.3 다이얼로그를 따른다
- 3.3을 누른 뒤 서버가 지우는 동안 3.2·3.3을 잠그고 3.3에 대기 표시를 둔다. 그동안 Esc도 받지 않는다 (VA-UI-001에 없음)
- 지우기에 실패하면 1을 닫지 않고 3.1에 무엇이 왜 안 됐는지 한 줄을 보이고 3.2·3.3을 다시 푼다. 문구는 VA-UI-001 4.5 문구 규칙을 따른다 (VA-UI-001에 없음)
- 지운 뒤에는 연 휴지통이 없어진다. UI-1에서 열었으면 초점은 UI-1 규칙대로 바로 아래 행의 행 링크로 가고, 아래 행이 없으면 바로 위 행의 행 링크로, 목록이 비면 「분석한 영상」 섹션 제목으로 간다. UI-4에서 열어 지운 뒤 UI-1이 열릴 때의 초점은 2장 미결이다 (VA-UI-001에 없음)

### 시나리오

**S-1 홈 목록에서 끝난 영상을 지운다** — [[VA-UC-001#UC-H6]] 기본 흐름 1~4
1. UI-1 「분석한 영상」에서 완료 행의 휴지통을 누른다. UI-1 위에 다이얼로그(1)가 뜨고 초점은 취소(3.2)에 있다
2. 대상 제목(1.3)을 보고 지울 영상이 맞는지 확인한다
3. 지워지는 것(2.1) '스크립트, 핵심 요약, 챕터, 추천 질문, 질문 기록 3개'와 남는 것(2.2) 'YouTube 원본 영상. 다시 넣으면 처음부터 분석합니다.'를 읽는다
4. 삭제(3.3)를 누른다. 지우는 동안 두 버튼이 잠긴다
5. 다이얼로그(1)가 닫히고 UI-1 목록에서 그 행이 사라지며 목록 머리의 개수가 하나 줄어든다

**S-2 읽던 로컬 파일 결과를 지운다** — [[VA-UC-001#UC-H6]] 기본 흐름 1~4
1. UI-4에서 로컬 파일 결과를 읽다가 머리의 휴지통을 누른다. UI-4 위에 다이얼로그(1)가 뜬다
2. 남는 것(2.2)이 'inbox 원본 파일. 다시 넣으면 처음부터 분석합니다.'다. 원본 파일은 지워지지 않는다
3. 삭제(3.3)를 누른다
4. 다이얼로그(1)가 닫히고 UI-1이 열린다. 목록에 그 영상이 없고, 「내 파일」 카드의 inbox 목록에는 원본 파일이 그대로 있다

**S-3 지우려다 그만둔다** — [[VA-UC-001#UC-H6]] 확장 3a
1. UI-4 머리의 휴지통을 누른다. 다이얼로그(1)가 뜨고 초점은 취소(3.2)에 있다
2. 지워지는 것(2.1)을 보고 질문 기록까지 지워진다는 것을 알아 그만두기로 한다
3. 덮개를 눌러 보지만 닫히지 않는다. 취소(3.2)를 누르거나 Esc를 누른다
4. 아무것도 지워지지 않는다. 다이얼로그(1)가 닫히고 UI-4가 읽던 자리 그대로 남으며 초점은 휴지통으로 돌아온다

**S-4 분석 중인 영상을 지워 멈춘다** — [[VA-UC-001#UC-H6]] 기본 흐름 1~4 (진행 중 영상 삭제는 UC-H6 갱신 요청 중, VA-UI-001 8장)
1. 잘못 넣은 영상이 UI-1 목록에서 '받아쓰기 중 · 12 / 30'으로 돌고 있다. 그 행의 휴지통을 누른다
2. 지워지는 것(2.1) 끝에 '임시 음성 파일'이 붙어 있다
3. 삭제(3.3)를 누른다. 서버가 작업을 먼저 멈추고 그 영상의 저장물을 지운다
4. 다이얼로그(1)가 닫히고 UI-1 목록에서 그 행이 사라진다

**S-5 실패한 영상을 지운다** — [[VA-UC-001#UC-H6]] 기본 흐름 1~4 (실패 영상 삭제는 UC-H6 갱신 요청 중, VA-UI-001 8장)
1. UI-1 목록의 '받아쓰기 16 / 24에서 멈춤' 행에서 휴지통을 누른다
2. 지워지는 것(2.1) 끝에 '임시 음성 파일'이 붙어 있다
3. 삭제(3.3)를 누른다. 완료해 저장해 둔 조각까지 모두 지워진다
4. 다이얼로그(1)가 닫히고 그 행이 사라진다. 같은 영상을 다시 넣으면 이미 분석한 영상으로 보지 않고 UI-2부터 처음 분석한다

---

## UI-7 내보내기

| 항목 | 내용 |
|---|---|
| 화면 설계 | [[VA-UI-001#UI-7]] |
| 경로 | (다이얼로그) |
| 디자인 보드 | Export |
| 진입 | UI-4 머리 [내보내기] |
| 유스케이스 | [[VA-UC-001#UC-H7]] 기본 흐름 1~3, 확장 2a·2b |

### 배치

```html
<!-- 주 보드: 캔버스 Export(UI-4 결과 위, 파일로 저장 선택). 아래는 상태 보드 -->
<div style="width: 1440px; height: 960px; position: relative; overflow: hidden; background: #F6F4EF;">
<div style="position: absolute; left: 0; top: 0; width: 1440px; height: 2900px;">
<div style="width: 1440px; height: 2900px; box-sizing: border-box; background: #F6F4EF; display: flex; flex-direction: column;">
<header style="height: 64px; flex-shrink: 0; box-sizing: border-box; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2DDD3; background: #F6F4EF;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 10px; color: #1B1A17; text-decoration: none;">
<span style="width: 30px; height: 30px; border-radius: 8px; background: #1B1A17; display: flex; align-items: center; justify-content: center;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="#F6F4EF" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z"></path></svg>
</span>
<span style="font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 20px; font-weight: 600; letter-spacing: -0.01em;">Video Agent</span>
</a>
<nav aria-label="주 메뉴" style="display: flex; align-items: center; gap: 4px;">
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; border-radius: 10px; color: #4A463F; font-size: 15px; font-weight: 600; text-decoration: none;">분석한 영상</a>
<a href="#" aria-label="설정" style="width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M20 7h-9"></path><path d="M14 17H5"></path><circle cx="17" cy="17" r="3"></circle><circle cx="7" cy="7" r="3"></circle></svg>
</a>
</nav>
</header>
<div style="flex-grow: 1; display: grid; grid-template-columns: minmax(0, 1fr) 520px;">
<main style="min-width: 0; box-sizing: border-box; padding: 24px 64px 96px 96px; display: flex; flex-direction: column; gap: 48px;">
<div style="display: flex; flex-direction: column; gap: 18px;">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px;">
<a href="#" style="height: 44px; display: flex; align-items: center; gap: 6px; color: #4A463F; font-size: 15px; text-decoration: none;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>
분석한 영상
</a>
<div style="display: flex; align-items: center; gap: 8px;">
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 16px; display: flex; align-items: center; gap: 8px; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="m7 10 5 5 5-5"></path><path d="M12 15V3"></path></svg>
내보내기
</a>
<a href="#" aria-label="분석 결과 삭제" style="width: 44px; height: 44px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #A33A2B;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
</a>
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 12px;">
<div style="display: flex; flex-wrap: wrap; gap: 6px;">
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">YouTube</span>
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">50:12</span>
<span style="height: 26px; box-sizing: border-box; padding: 0 10px; display: flex; align-items: center; border-radius: 6px; background: #EFECE5; color: #4A463F; font-size: 13px; font-weight: 500;">자막 · 한국어</span>
</div>
<h1 style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 36px; line-height: 1.3; font-weight: 600; letter-spacing: -0.02em;">RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나</h1>
<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 14px; font-size: 15px; color: #5E5A52;">
<span>[채널명] · 오늘 14:08 분석 · 요약 gpt-5-mini</span>
<a href="https://www.youtube.com/" style="display: flex; align-items: center; gap: 4px; color: #0F6E68; font-weight: 600; text-decoration: none;">
원본 영상 열기
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M15 3h6v6"></path><path d="M10 14 21 3"></path><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path></svg>
</a>
</div>
</div>
</div>
<section aria-labelledby="tldr-title" style="display: flex; flex-direction: column; gap: 10px;">
<h2 id="tldr-title" style="margin: 0; font-size: 14px; font-weight: 600; color: #5E5A52;">한 줄 요약</h2>
<p style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; line-height: 1.6; font-weight: 500; letter-spacing: -0.01em; color: #1B1A17;">RAG 서비스를 1년간 운영하며 겪은 검색 품질 문제와, 청킹과 pgvector 인덱스를 손봐 해결한 과정을 공유하는 발표.</p>
</section>
<section aria-labelledby="insight-title" style="display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="insight-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">핵심 인사이트</h2>
<span style="font-size: 14px; color: #6B665C;">8개</span>
</div>
<ol style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; border-top: 1px solid #E2DDD3;">
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">01</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
틀린 답의 원인을 따라가 보니 생성 모델보다 검색 단계에서 엉뚱한 문서를 가져온 경우가 훨씬 많았다.
<button type="button" aria-label="04:30 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">04:30</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">02</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
평가 데이터 없이 튜닝하면 개선인지 착시인지 알 수 없어, 실제 질문 로그로 평가 세트부터 만들었다.
<button type="button" aria-label="09:05 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">09:05</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">03</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
파이프라인은 수집 → 청킹 → 임베딩 → 검색 → 재순위 → 생성의 여섯 단계로 단순하게 유지했다.
<button type="button" aria-label="12:40 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">12:40</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">04</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
청킹 크기를 512에서 256 토큰으로 줄이자 재현율이 12%p 올랐다.
<button type="button" aria-label="23:15 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">23:15</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">05</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
별도 벡터 DB 대신 PostgreSQL의 pgvector를 써서 원본 데이터와 같은 곳에서 관리했다.
<button type="button" aria-label="13:18 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">13:18</button>
<button type="button" aria-label="24:02 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">24:02</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">06</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
재순위 모델은 정확도를 올리지만 지연을 늘려, 재순위에 넘기는 후보 수를 줄여 균형을 맞췄다.
<button type="button" aria-label="31:48 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">31:48</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">07</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
문서가 바뀌면 바뀐 청크만 다시 임베딩하도록 청크마다 원본 버전을 기록했다.
<button type="button" aria-label="38:20 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">38:20</button>
</span>
</li>
<li style="box-sizing: border-box; padding: 14px 0; display: grid; grid-template-columns: 36px minmax(0, 1fr); column-gap: 8px; border-bottom: 1px solid #E2DDD3;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 14px; line-height: 1.8; font-weight: 600; color: #6B665C;">08</span>
<span style="font-size: 16px; line-height: 1.8; color: #1B1A17;">
가장 효과가 컸던 것은 모델 교체가 아니라, 검색 결과를 사람이 직접 읽는 주간 리뷰였다.
<button type="button" aria-label="44:10 위치의 스크립트로 이동" style="margin-left: 6px; height: 26px; box-sizing: border-box; padding: 0 8px; border: 0; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; cursor: pointer; vertical-align: 1px;">44:10</button>
</span>
</li>
</ol>
</section>
<section aria-labelledby="ask-title" style="display: flex; flex-direction: column; gap: 14px;">
<h2 id="ask-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">이런 걸 물어볼 수 있어요</h2>
<div style="display: flex; flex-wrap: wrap; gap: 10px;">
<button type="button" style="min-height: 44px; box-sizing: border-box; padding: 10px 16px; display: flex; align-items: center; gap: 8px; border-radius: 22px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; text-align: left; cursor: pointer;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0F6E68" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
<span>청킹 전략을 바꾼 근거는?</span>
</button>
<button type="button" style="min-height: 44px; box-sizing: border-box; padding: 10px 16px; display: flex; align-items: center; gap: 8px; border-radius: 22px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; text-align: left; cursor: pointer;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0F6E68" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
<span>pgvector 대신 검토한 대안은?</span>
</button>
<button type="button" style="min-height: 44px; box-sizing: border-box; padding: 10px 16px; display: flex; align-items: center; gap: 8px; border-radius: 22px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; text-align: left; cursor: pointer;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0F6E68" aria-hidden="true" style="flex-shrink: 0; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
<span>운영 비용은 어떻게 달라졌나?</span>
</button>
</div>
</section>
<section aria-labelledby="chapter-title" style="display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h2 id="chapter-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 24px; font-weight: 600;">챕터</h2>
<span style="font-size: 14px; color: #6B665C;">9개</span>
</div>
<span style="font-size: 13px; color: #6B665C;">누르면 오른쪽 스크립트가 그 위치로 이동해요</span>
</div>
<div style="display: flex; flex-direction: column; gap: 6px;">
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">00:00</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">발표자 소개와 배경</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>사내 문서 검색 챗봇을 1년간 운영한 팀의 경험을 공유한다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>오늘 다룰 주제는 검색 품질이다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">04:30</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">문제 정의 — 검색이 왜 틀리나</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>틀린 답을 나눠 보니 검색 실패가 대부분이었다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>질문과 문서의 표현 차이가 주된 원인이었다</span>
</span>
</span>
</button>
<button type="button" style="width: 100%; box-sizing: border-box; padding: 14px 16px; display: grid; grid-template-columns: 84px minmax(0, 1fr); column-gap: 12px; border-radius: 12px; border: 1px solid transparent; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="align-self: start; justify-self: start; height: 26px; box-sizing: border-box; padding: 0 8px; display: flex; align-items: center; border-radius: 6px; background: #E1EFEC; color: #0F6E68; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600;">09:05</span>
<span style="display: flex; flex-direction: column; gap: 4px;">
<span style="font-size: 17px; line-height: 1.5; font-weight: 600;">평가 세트 만들기</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>실제 질문 로그에 정답 문서를 표시해 평가 세트를 만들었다</span>
</span>
<span style="display: flex; gap: 8px; font-size: 15px; line-height: 1.65; color: #4A463F;">
<span aria-hidden="true" style="color: #948D80;">·</span>
<span>바꿀 때마다 같은 세트로 재현율을 비교했다</span>
</span>
</span>
</button>
</div>
</section>
</main>
<aside aria-label="스크립트와 질문" style="min-width: 0; box-sizing: border-box; border-left: 1px solid #E2DDD3; background: #FBFAF7;">
<div style="position: sticky; top: 0; height: 896px; box-sizing: border-box; display: flex; flex-direction: column;">
<div style="height: 60px; flex-shrink: 0; box-sizing: border-box; padding: 0 20px; display: flex; align-items: flex-end; gap: 4px; border-bottom: 1px solid #E2DDD3;">
<button type="button" aria-pressed="true" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid #1B1A17; background: transparent; color: #1B1A17; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path></svg>
스크립트
</button>
<button type="button" aria-pressed="false" style="height: 52px; box-sizing: border-box; padding: 0 14px; display: flex; align-items: center; gap: 8px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: #6B665C; font-size: 15px; font-weight: 600; cursor: pointer;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path></svg>
질문하기
<span style="min-width: 22px; height: 22px; box-sizing: border-box; padding: 0 7px; display: flex; align-items: center; justify-content: center; border-radius: 11px; background: #EFECE5; color: #4A463F; font-size: 12px; font-weight: 600;">3</span>
</button>
</div>
<div style="flex-grow: 1; min-height: 0; display: flex; flex-direction: column;">
<div style="height: 48px; flex-shrink: 0; box-sizing: border-box; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 13px; color: #5E5A52;">
<span>자막(수동) · 한국어</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-weight: 600; color: #0F6E68;">12:40</span>
</div>
<div style="flex-grow: 1; min-height: 0; overflow: hidden; box-sizing: border-box; padding: 0 12px 16px; display: flex; flex-direction: column; gap: 2px;">
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">12:11</span>
<span style="font-size: 15px; line-height: 1.75;">그래서 그 분류 결과를 들고 구조를 처음부터 다시 봤습니다.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">12:24</span>
<span style="font-size: 15px; line-height: 1.75;">어디서 틀렸는지 모르는 상태로는 뭘 고쳐도 확신이 없었거든요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: #F8EDC4; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #7A5A00;">12:40</span>
<span style="font-size: 15px; line-height: 1.75;">지금 보시는 게 저희 전체 아키텍처입니다. 단계는 여섯 개로 단순하게 가져갔어요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">12:49</span>
<span style="font-size: 15px; line-height: 1.75;">첫 번째가 수집이고요, 사내 위키랑 드라이브 문서를 매일 새벽에 가져옵니다.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">12:58</span>
<span style="font-size: 15px; line-height: 1.75;">두 번째가 청킹인데, 이 부분은 뒤에서 따로 자세히 말씀드릴게요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:07</span>
<span style="font-size: 15px; line-height: 1.75;">세 번째 임베딩은 처음엔 외부 API를 쓰다가 나중에 모델을 바꿨고요.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:18</span>
<span style="font-size: 15px; line-height: 1.75;">네 번째 검색은 PostgreSQL에 pgvector 확장을 올려서 하고 있습니다.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:29</span>
<span style="font-size: 15px; line-height: 1.75;">다섯 번째가 재순위인데, 여기서 지연 문제가 좀 있었습니다.</span>
</button>
<button type="button" style="width: 100%; flex-shrink: 0; box-sizing: border-box; padding: 10px 12px; display: grid; grid-template-columns: 64px minmax(0, 1fr); column-gap: 10px; border: 0; border-radius: 10px; background: transparent; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.75; font-weight: 600; color: #6B665C;">13:41</span>
<span style="font-size: 15px; line-height: 1.75;">마지막이 생성이고, 검색된 청크 중 상위 다섯 개만 넣어요.</span>
</button>
</div>
</div>
</div>
</aside>
</div>
</div>
</div>
<div style="position: absolute; left: 0; top: 0; width: 1440px; height: 960px; box-sizing: border-box; padding-top: 80px; display: flex; justify-content: center; align-items: flex-start; background: rgba(27, 26, 23, 0.52);">
<div role="dialog" aria-modal="true" aria-labelledby="exp-title" data-el="1" style="width: 660px; box-sizing: border-box; padding: 32px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 28px 80px rgba(27, 26, 23, 0.32); display: flex; flex-direction: column; gap: 20px;">
<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;">
<div style="display: flex; flex-direction: column; gap: 6px;">
<h2 id="exp-title" data-el="1.1" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 28px; line-height: 1.3; font-weight: 600; letter-spacing: -0.01em;">마크다운으로 내보내기</h2>
<span data-el="1.2" style="font-size: 15px; color: #5E5A52;">시각은 [12:40] 형태로 남고, YouTube 영상이면 그 시점 링크가 걸려요.</span>
</div>
<a data-el="1.3" href="#" aria-label="닫기" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
</a>
</div>
<div role="group" aria-label="내보내는 방법" data-el="2" style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px;">
<button type="button" data-el="2.1" aria-pressed="true" style="min-height: 84px; box-sizing: border-box; padding: 14px 16px; display: flex; flex-direction: column; align-items: flex-start; gap: 6px; border-radius: 12px; border: 2px solid #0F6E68; background: #E1EFEC; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="m7 10 5 5 5-5"></path><path d="M12 15V3"></path></svg>
파일로 저장
</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #5E5A52;">data/export/rag-서비스-1년-운영기.md</span>
</button>
<button type="button" data-el="2.2" aria-pressed="false" style="min-height: 84px; box-sizing: border-box; padding: 14px 16px; display: flex; flex-direction: column; align-items: flex-start; gap: 6px; border-radius: 12px; border: 2px solid #E2DDD3; background: #FFFFFF; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="8" y="8" width="14" height="14" rx="2"></rect><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path></svg>
클립보드에 복사
</span>
<span style="font-size: 13px; color: #5E5A52;">노트 앱에 바로 붙여 넣기</span>
</button>
</div>
<label data-el="3" style="min-height: 44px; display: flex; align-items: center; gap: 10px; font-size: 15px; cursor: pointer;">
<input type="checkbox" style="width: 18px; height: 18px; margin: 0; accent-color: #0F6E68;">
<span>질문 기록 3개도 넣기</span>
</label>
<div data-el="4" style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 13px; font-weight: 600; color: #5E5A52;">미리 보기</span>
<pre data-el="4.1" style="margin: 0; max-height: 220px; overflow: hidden; box-sizing: border-box; padding: 16px 18px; border-radius: 12px; background: #1B1A17; color: #EDEAE3; font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.7; white-space: pre-wrap;"># RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나
원본: https://youtu.be/[영상ID] · 50:12

&gt; RAG 서비스를 1년간 운영하며 겪은 검색 품질 문제와, 청킹과 pgvector 인덱스를 손봐 해결한 과정을 공유하는 발표.

## 핵심 인사이트
1. 틀린 답의 원인을 따라가 보니 생성 모델보다 검색 단계에서 … [04:30](https://youtu.be/[영상ID]?t=270)
2. 평가 데이터 없이 튜닝하면 개선인지 착시인지 알 수 없어 … [09:05](https://youtu.be/[영상ID]?t=545)

## 챕터
### [00:00](https://youtu.be/[영상ID]?t=0) 발표자 소개와 배경
- 사내 문서 검색 챗봇을 1년간 운영한 팀의 경험을 공유한다</pre>
</div>
<div data-el="5" style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
<a data-el="5.2" href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">취소</a>
<a data-el="5.3" href="#" style="height: 44px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">파일로 저장</a>
</div>
</div>
</div>
</div>
<div class="var"><b>저장하지 못함</b> — 파일 쓰기나 클립보드 복사가 실패했을 때 버튼 줄 왼쪽에 실패 한 줄(5.1) · 캔버스에 없음</div>
<div class="crop dim">
<div role="dialog" aria-modal="true" aria-labelledby="exp-title" style="width: 660px; box-sizing: border-box; padding: 32px; border-radius: 18px; background: #FFFFFF; box-shadow: 0 28px 80px rgba(27, 26, 23, 0.32); display: flex; flex-direction: column; gap: 20px;">
<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;">
<div style="display: flex; flex-direction: column; gap: 6px;">
<h2 id="exp-title" style="margin: 0; font-family: 'Hahmlet', 'Noto Serif KR', serif; font-size: 28px; line-height: 1.3; font-weight: 600; letter-spacing: -0.01em;">마크다운으로 내보내기</h2>
<span style="font-size: 15px; color: #5E5A52;">시각은 [12:40] 형태로 남고, YouTube 영상이면 그 시점 링크가 걸려요.</span>
</div>
<a href="#" aria-label="닫기" style="width: 44px; height: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 10px; color: #4A463F;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
</a>
</div>
<div role="group" aria-label="내보내는 방법" style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px;">
<button type="button" aria-pressed="true" style="min-height: 84px; box-sizing: border-box; padding: 14px 16px; display: flex; flex-direction: column; align-items: flex-start; gap: 6px; border-radius: 12px; border: 2px solid #0F6E68; background: #E1EFEC; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="m7 10 5 5 5-5"></path><path d="M12 15V3"></path></svg>
파일로 저장
</span>
<span style="font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #5E5A52;">data/export/rag-서비스-1년-운영기.md</span>
</button>
<button type="button" aria-pressed="false" style="min-height: 84px; box-sizing: border-box; padding: 14px 16px; display: flex; flex-direction: column; align-items: flex-start; gap: 6px; border-radius: 12px; border: 2px solid #E2DDD3; background: #FFFFFF; color: #1B1A17; text-align: left; cursor: pointer;">
<span style="display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true" style="stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><rect x="8" y="8" width="14" height="14" rx="2"></rect><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path></svg>
클립보드에 복사
</span>
<span style="font-size: 13px; color: #5E5A52;">노트 앱에 바로 붙여 넣기</span>
</button>
</div>
<label style="min-height: 44px; display: flex; align-items: center; gap: 10px; font-size: 15px; cursor: pointer;">
<input type="checkbox" style="width: 18px; height: 18px; margin: 0; accent-color: #0F6E68;">
<span>질문 기록 3개도 넣기</span>
</label>
<div style="display: flex; flex-direction: column; gap: 8px;">
<span style="font-size: 13px; font-weight: 600; color: #5E5A52;">미리 보기</span>
<pre style="margin: 0; max-height: 220px; overflow: hidden; box-sizing: border-box; padding: 16px 18px; border-radius: 12px; background: #1B1A17; color: #EDEAE3; font-family: 'IBM Plex Mono', monospace; font-size: 13px; line-height: 1.7; white-space: pre-wrap;"># RAG 서비스 1년 운영기: 검색 품질은 어디서 무너지나
원본: https://youtu.be/[영상ID] · 50:12

&gt; RAG 서비스를 1년간 운영하며 겪은 검색 품질 문제와, 청킹과 pgvector 인덱스를 손봐 해결한 과정을 공유하는 발표.

## 핵심 인사이트
1. 틀린 답의 원인을 따라가 보니 생성 모델보다 검색 단계에서 … [04:30](https://youtu.be/[영상ID]?t=270)
2. 평가 데이터 없이 튜닝하면 개선인지 착시인지 알 수 없어 … [09:05](https://youtu.be/[영상ID]?t=545)

## 챕터
### [00:00](https://youtu.be/[영상ID]?t=0) 발표자 소개와 배경
- 사내 문서 검색 챗봇을 1년간 운영한 팀의 경험을 공유한다</pre>
</div>
<div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
<span data-el="5.1" role="alert" style="margin-right: auto; font-size: 14px; line-height: 1.5; color: #A33A2B;">파일을 저장하지 못했어요 — 디스크 공간 부족</span>
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 18px; display: flex; align-items: center; border-radius: 10px; border: 1px solid #CFC8BB; background: #FFFFFF; color: #1B1A17; font-size: 15px; font-weight: 600; text-decoration: none;">취소</a>
<a href="#" style="height: 44px; box-sizing: border-box; padding: 0 22px; display: flex; align-items: center; border-radius: 10px; background: #1B1A17; color: #F6F4EF; font-size: 15px; font-weight: 600; text-decoration: none;">파일로 저장</a>
</div>
</div>
</div>
```

### 요소

| # | 이름 | 종류 | 보여주는 것 | 누르면 |
|---|---|---|---|---|
| 1 | 다이얼로그 | 다이얼로그 | UI-4 위에 뜨는 내보내기 창. 공통 1.2 다이얼로그 틀. role dialog · aria-modal · 제목 1.1에 aria-labelledby. 뒤의 UI-4는 덮개 아래 그대로 | 창 안은 —. 덮개(바깥)를 누르거나 Esc → 취소와 같다, UI-4. 내보내는 중에는 받지 않음 |
| 1.1 | 제목 | 텍스트 | '마크다운으로 내보내기' | — |
| 1.2 | 부제 | 텍스트 | '시각은 [12:40] 형태로 남고, YouTube 영상이면 그 시점 링크가 걸려요.' YouTube·로컬 파일 모두 같은 문구 | — |
| 1.3 | 닫기 | 버튼 | X 아이콘만. 공통 1.8의 아이콘 버튼. aria-label '닫기' | 취소와 같다. 닫힘 → UI-4 |
| 2 | 내보내는 방법 | 영역 | 2.1과 2.2를 나란히 둔 묶음. role group · aria-label '내보내는 방법' | — |
| 2.1 | 파일로 저장 칸 | 버튼 | 내려받기 아이콘 + '파일로 저장', 아래 줄에 저장 경로 `data/export/{파일 이름}.md`(고정폭 글자). aria-pressed. 열 때 눌린 상태 | 방법 = 파일. 2.1 눌림 · 2.2 풀림, 5.3 글자 '파일로 저장'. 방법이 바뀌면 5.1이 떠 있을 때 지움 |
| 2.2 | 클립보드에 복사 칸 | 버튼 | 복사 아이콘 + '클립보드에 복사', 아래 줄에 '노트 앱에 바로 붙여 넣기'. aria-pressed | 방법 = 클립보드. 2.2 눌림 · 2.1 풀림, 5.3 글자 '복사하기'. 방법이 바뀌면 5.1이 떠 있을 때 지움 |
| 3 | 질문 기록 넣기 | 체크박스 | '질문 기록 {n}개도 넣기'. n은 UI-4 [질문하기] 배지 수. 기본 꺼짐. 라벨 줄 전체가 누르는 곳. 질문 기록이 0개면 없음 | 켬 / 끔. 4.1이 따라 바뀜 |
| 4 | 미리 보기 | 영역 | 작은 라벨 '미리 보기'와 4.1 | — |
| 4.1 | 마크다운 상자 | 상자 | 내보낼 마크다운의 앞부분 그대로. 고정폭 글자, 어두운 바탕. 최대 높이를 넘는 뒷부분은 잘리고 스크롤 없음. 읽기 전용 | — |
| 5 | 버튼 줄 | 영역 | 오른쪽 정렬. 5.2 취소, 오른쪽 끝에 5.3 주 버튼. 실패했을 때만 왼쪽 끝에 5.1 | — |
| 5.1 | 실패 한 줄 | 텍스트 | 저장이나 복사에 실패했을 때만. '파일을 저장하지 못했어요 — {이유}' 또는 '클립보드에 복사하지 못했어요 — {이유}'. role alert | — |
| 5.2 | 취소 | 버튼 | '취소'. 공통 1.8의 보조 버튼 | 아무것도 쓰거나 복사하지 않고 닫힘 → UI-4 |
| 5.3 | 주 버튼 | 버튼 | 2.1을 고르면 '파일로 저장', 2.2를 고르면 '복사하기'. 공통 1.8의 주 버튼 | 고른 방법으로 내보냄. 끝날 때까지 1 안의 요소가 잠기고 5.3에 대기 표시. 끝나면 닫힘 → UI-4 + 공통 1.5 짧은 알림. 실패하면 열린 채 5.1, 잠금이 풀림 |

### 규칙

- 1은 UI-4 머리 [내보내기]로만 열린다. 주소를 바꾸지 않고, 뒤의 UI-4는 보던 상태 그대로 덮개 아래 남는다. 주소가 없으므로 새로 고치면 1은 닫히고 UI-4가 열린다(VA-UI-001 6장)
- 모양은 공통 1.2 다이얼로그 틀을 따르고, 값은 VA-UI-001 3장 토큰, VA-UI-001 4.2의 내보내기 선택지·체크박스, VA-UI-001 4.3 다이얼로그에 있다
- 형식은 마크다운 하나다. 형식을 고르는 요소는 없다 ([[VA-PRD-001#R10]])
- 방법은 2.1과 2.2 중 하나만 눌린 상태다(aria-pressed). 눌린 칸을 다시 눌러도 풀리지 않는다. 기본은 2.1이다
- 1을 열 때마다 2.1이 눌린 상태로 시작한다. 지난번에 고른 방법을 기억하지 않는다 (VA-UI-001에 없음)
- 고른 칸은 청록 테두리와 연한 청록 바탕, 고르지 않은 칸은 회색 테두리와 흰 바탕이다
- 5.3 글자는 고른 방법을 따라간다. 2.1이면 '파일로 저장', 2.2이면 '복사하기'
- 2.1로 내보내면 서버가 2.1 아래에 보인 경로 `data/export/{파일 이름}.md`에 쓴다. 브라우저 다운로드는 없다
- 파일 이름은 영상 제목에서 만들고, 만드는 규칙은 MINISPEC에서 정한다
- 2.2로 내보내면 4.1에 보이는 앞부분이 아니라 마크다운 전체가 클립보드에 들어간다
- 방법을 바꿔도 4.1은 바뀌지 않는다. 두 방법이 내보내는 내용은 같다
- 3의 n은 UI-4 [질문하기] 탭 배지 수와 같다. 3은 기본으로 꺼져 있다
- 질문 기록이 0개인 결과에서는 3을 그리지 않는다 (VA-UI-001에 없음 — 8장 디자인 보강 항목)
- 3을 켜면 질문 기록이 마크다운 맨 끝에 붙고 4.1도 따라 바뀐다. 끄면 빠진다
- 4.1은 실제로 내보낼 내용의 앞부분이다. 최대 높이(VA-UI-001 3.3)에서 잘리고 스크롤하지 않는다. 그래서 스크립트와 질문 기록은 보통 보이지 않는다
- 내용 순서는 `# {제목}` → `원본: {링크} · {길이}` → `> {한 줄 요약}` → `## 핵심 인사이트` 번호 목록(문장 끝에 시각) → `## 챕터`(챕터마다 `### [{시각}]({링크}) {제목}`과 `- {요점}`) → 스크립트 → 3을 켰으면 질문 기록
- 시각은 `[MM:SS]`, 1시간 이상 영상은 `[H:MM:SS]` 글자로 남는다(VA-UI-001 4.4). YouTube 영상이면 `https://youtu.be/{영상ID}?t={초}` 링크가 걸리고, 로컬 파일이면 링크 없이 글자만 남는다
- 로컬 파일 결과의 원본 줄은 링크 대신 `원본: {파일 이름} · {길이}`로 쓴다 (VA-UI-001에 없음)
- 내보내는 중이 아닐 때 닫는 길은 1.3, 5.2, Esc, 덮개 누름 넷이고 모두 취소다. 파일도 클립보드도 건드리지 않는다
- 1이 열리면 초점은 고른 방법 칸(열 때는 2.1)에 두고 1 밖으로 나가지 않는다. 1이 닫히면 초점은 UI-4 [내보내기]로 돌아간다
- 5.2는 보조 버튼으로 왼쪽, 5.3은 주 버튼으로 오른쪽 끝이다
- 5.3을 누르면 고른 방법으로 내보내고, 끝나면 1을 닫고 UI-4에서 공통 1.5 짧은 알림으로 완료를 알린다([[VA-UC-001#UC-H7]] 3번)
- 짧은 알림은 모양이 보드에 없어 VA-UI-001 4.5 짧은 알림 규칙대로 만든다. 문구는 파일이면 'data/export/{파일 이름}.md에 저장했어요', 클립보드면 '클립보드에 복사했어요'다 (VA-UI-001에 없음 — 8장 디자인 보강 항목)
- 5.3을 누른 뒤 내보내기가 끝날 때까지 2.1·2.2·3·1.3·5.2·5.3을 잠그고 5.3에 대기 표시를 둔다. 그동안 Esc와 덮개 누름도 받지 않는다 (VA-UI-001에 없음)
- 저장이나 복사에 실패하면 1을 닫지 않고 5.1에 무엇이 왜 안 됐는지 한 줄로 보이고(VA-UI-001 4.5 문구 규칙) 잠근 요소를 다시 푼다. 5.3을 다시 누르면 다시 시도한다. 5.3을 다시 누르거나 2.1·2.2로 방법을 바꾸면 5.1은 사라진다 (VA-UI-001에 없음)
- 공통 1.4 키 없음 배너가 떠 있어도(키 없음·키 확인 실패) UI-4 [내보내기]와 1은 막지 않는다. 내보내기는 OpenAI로 아무것도 보내지 않고, VA-UI-001 UI-1 규칙에서 키가 없을 때 막는 것은 분석 버튼과 UI-4 질문 입력뿐이다 (VA-UI-001에 없음)
- 내보내기는 저장된 분석 결과를 바꾸지 않는다([[VA-UC-001#UC-H7]] 최소 보장)

### 시나리오

**S-1 YouTube 결과를 파일로 저장한다** — [[VA-UC-001#UC-H7]] 기본 흐름 1~3, 확장 2a
1. UI-4 머리 [내보내기]를 누르면 다이얼로그(1)가 뜬다. 뒤의 UI-4는 덮개 아래 그대로다
2. 파일로 저장 칸(2.1)이 눌린 채이고 초점도 거기 있다. 칸 아래에 저장 경로 `data/export/{파일 이름}.md`가 보인다
3. 미리 보기(4.1)에서 제목, 원본 링크, 한 줄 요약, 핵심 인사이트, 챕터 순서를 확인한다. 시각마다 `?t={초}` 링크가 걸려 있다
4. 주 버튼(5.3) '파일로 저장'을 누른다. 서버가 그 경로에 스크립트까지 든 마크다운 파일을 쓴다
5. 다이얼로그가 닫히고 UI-4에 짧은 알림 'data/export/{파일 이름}.md에 저장했어요'가 잠깐 보인다. 초점은 [내보내기]로 돌아간다

**S-2 클립보드에 복사한다** — [[VA-UC-001#UC-H7]] 기본 흐름 1~3
1. UI-4에서 [내보내기]를 눌러 다이얼로그(1)를 연다
2. 클립보드에 복사 칸(2.2)을 누른다. 2.2가 눌리고 2.1은 풀린다. 주 버튼(5.3) 글자가 '복사하기'로 바뀐다
3. 미리 보기(4.1)는 그대로다. 두 방법이 내보내는 내용은 같다
4. 복사하기(5.3)를 누르면 마크다운 전체가 클립보드에 들어가고 다이얼로그가 닫힌다
5. UI-4에 짧은 알림 '클립보드에 복사했어요'가 보인다. 노트 앱에 붙여 넣는다(도구 밖)

**S-3 질문 기록도 넣는다** — [[VA-UC-001#UC-H7]] 확장 2b
1. [질문하기] 배지가 3인 결과(UI-4)에서 다이얼로그(1)를 연다. 체크박스(3)에 '질문 기록 3개도 넣기'가 꺼진 채 보인다
2. 체크박스(3)를 켠다. 미리 보기(4.1)가 질문 기록을 넣은 내용으로 바뀐다. 질문 기록은 맨 끝이라 잘린 부분에 있다
3. 주 버튼(5.3)을 누른다. 스크립트 뒤에 질문과 답이 붙은 마크다운이 저장되거나 복사된다

**S-4 로컬 파일 결과를 내보낸다** — [[VA-UC-001#UC-H7]] 기본 흐름 1~3
1. 받아쓰기로 만든 1시간 넘는 로컬 파일 결과(UI-4)에서 다이얼로그(1)를 연다
2. 미리 보기(4.1)의 원본 줄이 링크 없이 파일 이름과 길이로 보인다
3. 미리 보기(4.1)의 시각이 링크 없이 `[0:06:20]`처럼 글자로만 남는다
4. 부제(1.2)는 YouTube 결과와 같은 문구다
5. 주 버튼(5.3)을 눌러 저장하거나 복사한다. 그 뒤는 S-1, S-2와 같다

**S-5 내보내지 않고 닫는다** — [[VA-UC-001#UC-H7]] 최소 보장
1. 다이얼로그(1)를 열고 미리 보기(4.1)만 훑어본다
2. 취소(5.2), 닫기(1.3), Esc, 덮개 누름 중 하나로 닫는다
3. 파일도 클립보드도 바뀌지 않는다. UI-4가 열기 전 그대로 보이고 초점은 [내보내기]로 돌아간다

**S-6 저장에 실패한다** — [[VA-UC-001#UC-H7]] 기본 흐름 3에서 갈라짐, 최소 보장 (실패 확장은 유스케이스에 없음)
1. 파일로 저장 칸(2.1)을 고른 채 주 버튼(5.3)을 누른다. 끝날 때까지 1 안의 요소가 잠기고 5.3에 대기 표시가 보인다
2. 서버가 파일을 쓰지 못한다. 다이얼로그(1)는 닫히지 않고 짧은 알림도 뜨지 않는다
3. 실패 한 줄(5.1)에 '파일을 저장하지 못했어요 — {이유}'가 보이고 잠긴 요소가 풀린다
4. 주 버튼(5.3)을 다시 눌러 다시 시도하거나, 클립보드에 복사 칸(2.2)으로 바꿔 복사한다. 방법을 바꾸면 실패 한 줄(5.1)이 사라진다