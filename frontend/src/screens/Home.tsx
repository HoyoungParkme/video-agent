/**
 * VA-UI-002#UI-1 홈 — 카드 A는 첫 실행 상태까지: 2 제목 영역(2.1 · 2.2) · 3 YouTube 링크 카드(3.1 · 3.2 ·
 * 3.3 분석 · 3.5) · 4 내 파일 카드(4.1 · 4.2 · 4.5 · 4.6 선택한 파일 분석) · 5 목록 머리(5.1 · 5.2 · 5.3) ·
 * 7 빈 상태 상자(7.1 · 7.2). 키 없음 배너(1)는 layout의 공통 1.4다.
 * 입력 카드 동작(3.3 · 3.4 · 4.3 · 4.4 · 4.6)과 inbox 목록은 B1 · B2, 분석한 영상 목록(6)은 B1에서 채운다.
 */
"use client";

import { useRouter } from "next/navigation";

import { keyBlocks, useSettings } from "@/api/client";
import { Button } from "@/components/buttons";
import EmptyBox from "@/components/EmptyBox";

const EMPTY_TITLE = "아직 분석한 영상이 없어요";
const EMPTY_BODY = "위에 링크를 붙여 넣거나 inbox 폴더에 파일을 넣어 보세요.";
const EMPTY_BODY_NO_KEY = `설정에서 OpenAI API 키를 넣은 뒤, ${EMPTY_BODY}`;

export default function Home() {
  const router = useRouter();
  const settings = useSettings();
  // 키를 받기 전에는 막지 않는다 — 받은 뒤 막힘이 정해진다
  const blocked = settings ? keyBlocks(settings.key) : false;
  const noKey = settings?.key.state === "missing";

  // 막힌 분석 버튼은 형식 검사 · 정보 확인 없이 설정으로 간다(공통 1.8). 켜진 버튼의 동작은 B1 · B2
  function toSettingsIfBlocked() {
    if (blocked) router.push("/settings");
  }

  return (
    <main className="home">
      <section aria-labelledby="home-title" className="home-intro">
        <div className="home-heading" data-el="2">
          <h1 id="home-title" className="page-title" data-el="2.1">
            어떤 영상을 읽어 볼까요?
          </h1>
          <p className="page-lead" data-el="2.2">
            YouTube 링크를 붙여 넣거나 inbox 폴더의 파일을 고르세요. 분석 결과는 이 PC에만
            저장됩니다.
          </p>
        </div>
        <div className="home-cards">
          <div className="card home-card home-card-yt" data-el="3">
            <div className="card-head" data-el="3.1">
              <span className="icon-tile icon-tile-teal">
                <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                </svg>
              </span>
              <div className="card-head-text">
                <span className="card-head-title">YouTube 링크</span>
                <span className="card-head-sub">watch · youtu.be · shorts 주소를 받아요</span>
              </div>
            </div>
            <div className="field">
              <label htmlFor="yt-url" className="field-label">
                영상 주소
              </label>
              <div className="field-row">
                <span className="field-wrap" data-el="3.2">
                  <input
                    id="yt-url"
                    type="url"
                    className="field-input"
                    placeholder="https://www.youtube.com/watch?v=…"
                  />
                </span>
                <Button
                  kind="primary"
                  tall
                  blocked={blocked}
                  el="3.3"
                  onClick={toSettingsIfBlocked}
                >
                  분석
                </Button>
              </div>
            </div>
            <p className="field-help" data-el="3.5">
              자막이 있는 영상은 받아쓰기 없이 1분 안에 끝나요.
            </p>
          </div>

          <div className="card home-card home-card-files" data-el="4">
            <div className="card-head" data-el="4.1">
              <span className="icon-tile">
                <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
                </svg>
              </span>
              <div className="card-head-text">
                <span className="card-head-title">내 파일</span>
                <span className="card-head-path">{settings?.inbox_path}</span>
              </div>
            </div>
            {/* inbox 파일 행(4.3)과 빈 안내(4.4)는 B2의 GET /api/inbox로 채운다 */}
            <div role="group" aria-label="inbox 파일" className="home-files" data-el="4.2" />
            <div className="home-files-foot">
              <span className="caption" data-el="4.5">
                mp4 · mkv · mov · webm · mp3 · m4a · wav
              </span>
              <Button
                kind="primary"
                className="btn-wide"
                blocked={blocked}
                el="4.6"
                onClick={toSettingsIfBlocked}
              >
                선택한 파일 분석
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section aria-labelledby="list-title" className="home-list">
        <div className="home-list-head" data-el="5">
          <div className="home-list-title">
            <h2 id="list-title" tabIndex={-1} className="section-title" data-el="5.1">
              분석한 영상
            </h2>
            {/* 목록은 B1의 GET /api/videos로 채운다 — 그때까지는 빈 결과 */}
            <span className="home-list-count" data-el="5.2">
              0개
            </span>
          </div>
          <span className="caption" data-el="5.3">
            최근 순
          </span>
        </div>
        <EmptyBox
          title={EMPTY_TITLE}
          body={noKey ? EMPTY_BODY_NO_KEY : EMPTY_BODY}
          el="7"
          elTitle="7.1"
          elBody="7.2"
        />
      </section>
    </main>
  );
}
