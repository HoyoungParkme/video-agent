/**
 * VA-UI-002#UI-4 결과 — 왼쪽 본문: 1 머리 줄(1.1 뒤로 링크) · 2 제목 블록(2.1 칩 셋 · 2.2 제목 · 2.3 메타 줄 ·
 * 2.4 원본 영상 열기) · 3 한 줄 요약 · 4 핵심 인사이트(4.1 · 4.2 · 4.3 시각 칩) · 5 추천 질문(5.1 알약) ·
 * 6 챕터(6.1 · 6.2 · 6.3 카드). 오른쪽 7 패널 — 7.1 스크립트 탭 · 8 스크립트(8.1 출처 · 8.2 선택한 시각 · 8.3 구간).
 * 11 짧은 알림 — UI-1에서 이미 분석한 영상을 넣어 열렸을 때.
 * 시각을 누르는 곳(4.3 · 6.3 · 8.3)은 모두 같은 동작이다 — 스크립트 탭 · 그 시각이 든 구간 강조와 스크롤 ·
 * 시작 시각이 같은 챕터 선택 · 8.2(공통 1.3). 결과가 아직 없으면 UI-3으로, 영상이 없으면 UI-1로,
 * 서버에 잠깐 닿지 못하면 2초 뒤 다시 받는다.
 * B1이 채우지 않은 것: 내보내기(1.2) · 휴지통(1.3)은 B4, 파트(6.4 ~ 6.6)는 B2, 질문하기 탭(7.2 · 7.3 · 9 · 10)과
 * 추천 질문 전송은 B3 — 알약(5.1)은 보이되 누르면 아무 일도 없다.
 */
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { api, ApiError, type Result as ResultData } from "@/api/client";
import TimeChip, { durationLabel, isLong, timeLabel } from "@/components/TimeChip";
import Toast, { takeFlash } from "@/components/Toast";
import { analyzedLabel, languageName } from "@/labels";

// 결과를 받지 못했는데 서버에 잠깐 닿지 못한 것이면 다시 받는 간격(UI-4 규칙)
const RETRY_MS = 2000;

/** 스크립트 출처(8.1) — '자막(수동) · 한국어' · '자막(자동) · 한국어' · '받아쓰기 {모델} · {언어}'. */
function sourceLabel(r: ResultData): string {
  const lang = languageName(r.transcript.language);
  switch (r.transcript.source) {
    case "caption_manual":
      return `자막(수동) · ${lang}`;
    case "caption_auto":
      return `자막(자동) · ${lang}`;
    default:
      return `받아쓰기 ${r.transcript.model ?? ""} · ${lang}`;
  }
}

/** 그 시각이 든 구간 — 시작이 그 시각 이하인 마지막 구간. */
function segmentAt(r: ResultData, sec: number): number | null {
  let found: number | null = null;
  for (const s of r.transcript.segments) {
    if (s.start_sec <= sec) found = s.seq;
    else break;
  }
  return found ?? r.transcript.segments[0]?.seq ?? null;
}

export default function Result({ id }: { id: number }) {
  const router = useRouter();
  const [result, setResult] = useState<ResultData | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const script = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const got = await api.result(id);
        if (!alive) return;
        setResult(got);
        setNotice(takeFlash()); // UI-1에서 이미 분석한 영상을 넣어 열렸으면
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError) {
          const status = e.body.video_status;
          if (e.kind === "result-not-ready" && (status === "in_progress" || status === "failed")) {
            router.replace(`/videos/${id}/progress`);
            return;
          }
          if (e.status === 404 || e.status === 409 || e.status === 422) {
            router.replace("/");
            return;
          }
        }
        timer = setTimeout(load, RETRY_MS); // 연결 끊김 · 서버 오류 — 빈 화면으로 멈추지 않게
      }
    };
    void load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [id, router]);

  const segSeq = result && selected !== null ? segmentAt(result, selected) : null;

  // 고른 구간을 패널 안에서 보이게 — 창 전체는 움직이지 않는다
  useEffect(() => {
    if (segSeq === null || !script.current) return;
    const row = script.current.querySelector<HTMLElement>(`[data-seq="${segSeq}"]`);
    if (!row) return;
    const box = script.current; // position: relative — 행의 offsetTop이 이 상자 기준이다
    box.scrollTop = row.offsetTop - box.clientHeight / 2 + row.clientHeight / 2;
  }, [segSeq]);

  if (!result) return <main className="result" aria-busy="true" />;

  const { video } = result;
  const long = isLong(video.duration_sec);
  const select = (sec: number) => setSelected(sec);
  const model =
    result.transcript.source === "stt"
      ? `받아쓰기 ${result.models.stt ?? ""}`
      : `요약 ${result.models.text}`;
  const kindChip = result.transcript.source === "stt" ? "받아쓰기" : "자막";

  return (
    <div className="result">
      <main className="result-main">
        <div className="result-top">
          <div className="result-head" data-el="1">
            <Link href="/" className="back-link" data-el="1.1">
              <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                <path d="m12 19-7-7 7-7" />
                <path d="M19 12H5" />
              </svg>
              분석한 영상
            </Link>
          </div>
          <div className="result-title-block" data-el="2">
            <div className="chips" data-el="2.1">
              <span className="chip">
                {video.source_kind === "youtube" ? "YouTube" : "로컬 파일"}
              </span>
              <span className="chip">{durationLabel(video.duration_sec)}</span>
              <span className="chip">
                {kindChip} · {languageName(result.transcript.language)}
              </span>
            </div>
            <h1 className="result-title" data-el="2.2">
              {video.title}
            </h1>
            <div className="result-meta">
              <span data-el="2.3">
                {video.channel ?? "로컬 파일"} · {analyzedLabel(result.analyzed_at)} 분석 · {model}
              </span>
              {video.source_kind === "youtube" && (
                <a
                  href={video.origin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="result-origin"
                  data-el="2.4"
                >
                  원본 영상 열기
                  <svg
                    className="icon"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path d="M15 3h6v6" />
                    <path d="M10 14 21 3" />
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  </svg>
                </a>
              )}
            </div>
          </div>
        </div>

        <section aria-labelledby="tldr-title" className="result-tldr" data-el="3">
          <h2 id="tldr-title" className="label-title">
            한 줄 요약
          </h2>
          <p className="result-one-liner">{result.summary.one_liner}</p>
        </section>

        <section aria-labelledby="insight-title" className="result-section" data-el="4">
          <div className="result-section-head">
            <h2 id="insight-title" className="section-title">
              핵심 인사이트
            </h2>
            <span className="count" data-el="4.1">
              {result.summary.insights.length}개
            </span>
          </div>
          <ol className="insights">
            {result.summary.insights.map((ins, i) => (
              <li key={ins.seq} className="insight" data-el={i === 0 ? "4.2" : undefined}>
                <span className="insight-no mono">{String(ins.seq).padStart(2, "0")}</span>
                <span className="insight-text">
                  {ins.text}
                  {ins.source_secs.map((sec, j) => (
                    <TimeChip
                      key={sec}
                      sec={sec}
                      long={long}
                      onSelect={select}
                      el={i === 0 && j === 0 ? "4.3" : undefined}
                    />
                  ))}
                </span>
              </li>
            ))}
          </ol>
        </section>

        <section aria-labelledby="ask-title" className="result-section" data-el="5">
          <h2 id="ask-title" className="section-title">
            이런 걸 물어볼 수 있어요
          </h2>
          <div className="pills">
            {result.suggested_questions.map((q, i) => (
              // 질문하기 탭은 B3 — 지금은 누르면 아무 일도 없다
              <button
                key={q.seq}
                type="button"
                className="pill"
                data-el={i === 0 ? "5.1" : undefined}
              >
                <svg className="icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
                </svg>
                <span>{q.text}</span>
              </button>
            ))}
          </div>
        </section>

        <section aria-labelledby="chapter-title" className="result-section" data-el="6">
          <div className="result-section-head result-section-head-split">
            <div className="result-section-head">
              <h2 id="chapter-title" className="section-title">
                챕터
              </h2>
              <span className="count" data-el="6.1">
                {result.chapters.length}개
              </span>
            </div>
            <span className="caption" data-el="6.2">
              누르면 오른쪽 스크립트가 그 위치로 이동해요
            </span>
          </div>
          <div className="chapters">
            {result.chapters.map((c, i) => (
              <button
                key={c.seq}
                type="button"
                className={`chapter${selected === c.start_sec ? " is-selected" : ""}`}
                aria-pressed={selected === c.start_sec}
                data-el={i === 0 ? "6.3" : undefined}
                onClick={() => select(c.start_sec)}
              >
                <span className="chapter-time mono">{timeLabel(c.start_sec, long)}</span>
                <span className="chapter-body">
                  <span className="chapter-title">{c.title}</span>
                  {c.bullets.map((b) => (
                    <span key={b} className="chapter-bullet">
                      <span aria-hidden="true" className="chapter-dot">
                        ·
                      </span>
                      <span>{b}</span>
                    </span>
                  ))}
                </span>
              </button>
            ))}
          </div>
        </section>
      </main>

      <aside aria-label="스크립트와 질문" className="panel" data-el="7">
        <div className="panel-inner">
          <div role="tablist" aria-label="스크립트와 질문" className="tabs">
            <button type="button" role="tab" aria-selected="true" className="tab" data-el="7.1">
              <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M8 6h13" />
                <path d="M8 12h13" />
                <path d="M8 18h13" />
                <path d="M3 6h.01" />
                <path d="M3 12h.01" />
                <path d="M3 18h.01" />
              </svg>
              스크립트
            </button>
          </div>
          <div role="tabpanel" className="script" data-el="8">
            <div className="script-head">
              <span data-el="8.1">{sourceLabel(result)}</span>
              <span className="script-now mono" data-el="8.2">
                {selected === null ? "" : timeLabel(selected, long)}
              </span>
            </div>
            <div ref={script} className="script-body">
              {result.transcript.segments.map((s, i) => (
                <button
                  key={s.seq}
                  type="button"
                  className={`segment${segSeq === s.seq ? " is-selected" : ""}`}
                  aria-pressed={segSeq === s.seq}
                  data-seq={s.seq}
                  data-el={i === 0 ? "8.3" : undefined}
                  onClick={() => select(s.start_sec)}
                >
                  <span className="segment-time mono">{timeLabel(s.start_sec, long)}</span>
                  <span className="segment-text">{s.text}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {notice && <Toast el="11" message={notice} onDone={() => setNotice(null)} />}
    </div>
  );
}
