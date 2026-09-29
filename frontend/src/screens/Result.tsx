/**
 * VA-UI-002#UI-4 결과 — 왼쪽 본문: 1 머리 줄(1.1 뒤로 링크) · 2 제목 블록(2.1 칩 셋 · 2.2 제목 · 2.3 메타 줄 ·
 * 2.4 원본 영상 열기) · 3 한 줄 요약 · 4 핵심 인사이트(4.1 · 4.2 · 4.3 시각 칩) · 5 추천 질문(5.1 알약) ·
 * 6 챕터(6.1 · 6.2 · 6.3 카드, 1시간 넘으면 6.4 파트 카드 · 6.5 파트 머리 · 6.6 파트 안 챕터 카드).
 * 오른쪽 7 패널 — 7.1 스크립트 탭 · 7.2 질문하기 탭(7.3 질문 수 배지) · 8 스크립트(8.1 출처 · 8.2 선택한 시각 ·
 * 8.3 구간) · 9 대화 목록(9.1 빈 상태 · 9.2 턴 · 9.3 질문 말풍선 · 9.4 답 · 9.5 근거 칩 · 9.6 영상에 없는 내용 ·
 * 9.7 답 대기 · 9.8 답변 실패 · 9.9 다시 시도) · 10 질문 입력(10.1 추천 칩 · 10.2 키 없음 안내 · 10.3 입력칸 ·
 * 10.4 보내기 · 10.5 전송 안내). 11 짧은 알림 — UI-1에서 이미 분석한 영상을 넣어 열렸을 때.
 * 시각을 누르는 곳(4.3 · 6.3 · 6.6 · 8.3 · 9.5)은 모두 같은 동작이다 — 스크립트 탭 · 그 시각이 든 구간 강조와
 * 스크롤 · 시작 시각이 같은 챕터 선택 · 8.2(공통 1.3). 결과가 아직 없으면 UI-3으로, 영상이 없으면 UI-1로,
 * 서버에 잠깐 닿지 못하면 2초 뒤 다시 받는다.
 * 파트는 처음에 첫 파트만 펼친다. 선택된 챕터가 접힌 파트 안에 있어도 저절로 펴지 않는다.
 * 질문 기록은 질문하기 탭을 처음 열 때 받는다. 추천 질문(5.1 · 10.1)을 누르면 그 탭으로 바뀌고 바로 보낸다.
 * 기록과 답은 id로 합친다 — 기록을 받는 사이에 온 답도 한 번씩 보인다.
 * 답을 기다리는 동안이나 키가 막혔을 때는 보내지 않는다(알약은 탭만 바꾼다). 실패한 질문은 저장되지 않아
 * 마지막 턴에만 실패 줄과 다시 시도가 있고, 새 질문을 보내면 빠진다.
 * 머리의 내보내기(1.2)는 UI-7, 휴지통(1.3)은 UI-6을 연다. 내보내면 짧은 알림(11)으로 알리고, 지우면
 * UI-1로 방문 기록을 바꿔치기해 가며 그 화면의 「분석한 영상」 제목에 초점을 둔다(UI-6 규칙).
 */
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import {
  api,
  ApiError,
  keyBlocks,
  loadSettings,
  useSettings,
  type Chapter,
  type ChatTurn,
  type KeyStatus,
  type Result as ResultData,
} from "@/api/client";
import { Button } from "@/components/buttons";
import EmptyBox from "@/components/EmptyBox";
import { OFFLINE } from "@/components/KeyBanner";
import TimeChip, { durationLabel, isLong, timeLabel } from "@/components/TimeChip";
import Toast, { takeFlash } from "@/components/Toast";
import Delete, { markListFocus, TrashIcon } from "@/screens/Delete";
import Export, { DownloadIcon } from "@/screens/Export";
import { analyzedLabel, languageName } from "@/labels";

// 결과를 받지 못했는데 서버에 잠깐 닿지 못한 것이면 다시 받는 간격(UI-4 규칙)
const RETRY_MS = 2000;

type Tab = "script" | "chat";
/** 보낸 질문 — error가 null이면 답을 기다리는 중, 아니면 답변 실패 한 줄(9.8) */
interface Pending {
  question: string;
  error: string | null;
}

/** 턴을 id로 합친다 — 이미 있는 것은 두 번 넣지 않는다. 새 턴은 끝에 붙는다. */
function merged(list: ChatTurn[], more: ChatTurn[]): ChatTurn[] {
  const ids = new Set(list.map((t) => t.id));
  return [...list, ...more.filter((t) => !ids.has(t.id))];
}

/** 답변 실패(9.8) — 까닭으로 고른다(UI-4 규칙). {이유}는 서버가 준 한 줄. */
function failureText(e: unknown): string {
  // 우리 서버의 답(problem+json)이 아니면 — 끊김 · 웹이 api에 닿지 못함
  if (!(e instanceof ApiError) || e.kind === "unknown")
    return "답을 받지 못했어요 — 서버에 연결할 수 없음";
  const why = e.reason.replace(/[.。]\s*$/, "");
  if (e.kind === "llm-unavailable") return `OpenAI API에 연결하지 못했어요 — ${why}`;
  if (e.kind === "key-missing") return "API 키가 없어 답을 받지 못했어요";
  if (e.kind === "key-invalid")
    return e.body.reason_kind === "network"
      ? `연결을 확인하지 못했어요 — ${why}`
      : `키를 확인하지 못해 답을 받지 못했어요 — ${why}`;
  return `답을 받지 못했어요 — ${why}`;
}

/** 키 없음 안내(10.2) — 키가 없거나 확인에 실패했을 때. 연결 문구는 링크가 없고 막지도 않는다. */
function keyNotice(key: KeyStatus): { text: string; link: boolean } | null {
  if (key.state === "missing") return { text: "API 키가 없어 질문할 수 없어요.", link: true };
  if (key.state !== "invalid") return null;
  if (key.reason_kind === "network") return { text: OFFLINE, link: false }; // 배너와 같은 문장
  return { text: `키를 확인하지 못해 질문할 수 없어요 — ${key.reason ?? ""}`, link: true };
}

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

/** 챕터 카드(6.3 · 6.6) — 시작 시각 · 제목 · 요점. 카드 전체가 시각 누르기다(공통 1.3). */
function ChapterCard({
  c,
  long,
  selected,
  onSelect,
  el,
}: {
  c: Chapter;
  long: boolean;
  selected: boolean;
  onSelect: (sec: number) => void;
  el?: string;
}) {
  return (
    <button
      type="button"
      className={`chapter${selected ? " is-selected" : ""}`}
      aria-pressed={selected}
      data-el={el}
      onClick={() => onSelect(c.start_sec)}
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
  );
}

/**
 * 질문 턴(9.2) — 오른쪽 검은 말풍선(9.3)과 답(9.4). 근거가 있으면 '근거'와 시각 칩(9.5),
 * 없으면 흐린 답과 '영상에 없는 내용'(9.6). 요소 번호는 첫 턴에만 붙인다.
 */
function TurnView({
  turn,
  long,
  onSelect,
  first,
}: {
  turn: ChatTurn;
  long: boolean;
  onSelect: (sec: number) => void;
  first: boolean;
}) {
  const cited = turn.cited_secs.length > 0;
  return (
    <div className="turn" data-el={first ? "9.2" : undefined}>
      <div className="turn-question" data-el={first ? "9.3" : undefined}>
        {turn.question}
      </div>
      <div className="turn-reply">
        <span
          className={`turn-answer${cited ? "" : " is-dim"}`}
          data-el={first ? "9.4" : undefined}
        >
          {turn.answer}
        </span>
        {cited ? (
          <span className="turn-cites">
            <span className="turn-cites-label">근거</span>
            {turn.cited_secs.map((sec, j) => (
              <TimeChip
                key={sec}
                sec={sec}
                long={long}
                onSelect={onSelect}
                el={first && j === 0 ? "9.5" : undefined}
              />
            ))}
          </span>
        ) : (
          <span className="turn-none" data-el={first ? "9.6" : undefined}>
            영상에 없는 내용
          </span>
        )}
      </div>
    </div>
  );
}

export default function Result({ id }: { id: number }) {
  const router = useRouter();
  const [result, setResult] = useState<ResultData | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  // 펼친 파트 — 처음에는 첫 파트만(UI-4 규칙)
  const [open, setOpen] = useState<Set<number>>(() => new Set([1]));
  const [tab, setTab] = useState<Tab>("script");
  // 머리에서 연 다이얼로그 — 내보내기(UI-7) · 삭제 확인(UI-6)
  const [dialog, setDialog] = useState<"export" | "delete" | null>(null);
  // 질문 기록 — 질문하기 탭을 처음 열 때 받는다(받기 전에는 null)
  const [turns, setTurns] = useState<ChatTurn[] | null>(null);
  // 이 화면에서 받은 답 — 기록이 답보다 늦게 오거나 저장 전에 읽은 것이어도 받을 때 합친다
  const answered = useRef<ChatTurn[]>([]);
  const [pending, setPending] = useState<Pending | null>(null);
  // 이 화면에서 늘어난 질문 수 — 배지(7.3) = 저장된 수 + 이것
  const [asked, setAsked] = useState(0);
  const [draft, setDraft] = useState("");
  const script = useRef<HTMLDivElement>(null);
  const chatList = useRef<HTMLDivElement>(null);
  const settings = useSettings();

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

  // 질문하기 탭을 처음 열 때 기록을 받는다 — 잠깐 닿지 못하면 다시
  useEffect(() => {
    if (tab !== "chat" || turns !== null) return;
    let alive = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = async () => {
      try {
        const got = await api.chat(id);
        if (alive) setTurns(merged(got, answered.current));
      } catch {
        if (alive) timer = setTimeout(load, RETRY_MS);
      }
    };
    void load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [tab, turns, id]);

  // 새 턴 · 대기 · 실패가 생기면 대화 목록의 끝을 보인다 — 창 전체는 움직이지 않는다
  useEffect(() => {
    const box = chatList.current;
    if (box) box.scrollTop = box.scrollHeight;
  }, [turns, pending, tab]);

  if (!result) return <main className="result" aria-busy="true" />;

  const { video } = result;
  const long = isLong(video.duration_sec);
  // 시각 누르기 — 패널은 스크립트 탭으로(공통 1.3)
  const select = (sec: number) => {
    setSelected(sec);
    setTab("script");
  };
  const keyBlocked = settings ? keyBlocks(settings.key) : false;
  const keyNote = settings ? keyNotice(settings.key) : null;
  const waiting = pending !== null && pending.error === null;

  // 질문 보내기 — 입력칸 · 추천 질문 · 다시 시도가 같은 길. 기다리는 동안이나 키가 막혔으면 보내지 않는다
  async function ask(question: string) {
    const q = question.trim();
    if (!q || waiting || keyBlocked) return;
    setTab("chat");
    setPending({ question: q, error: null });
    try {
      const turn = await api.ask(id, q);
      answered.current.push(turn);
      // 기록을 받기 전이면 받을 때 합친다. 저장 뒤에 읽은 기록에 이미 있으면 두 번 넣지 않는다
      setTurns((prev) => (prev === null ? prev : merged(prev, [turn])));
      setAsked((n) => n + 1);
      setPending(null);
    } catch (e) {
      if (e instanceof ApiError && (e.kind === "key-missing" || e.kind === "key-invalid")) {
        void loadSettings(); // 배너와 키 없음 안내(10.2)가 뜬다
      }
      setPending({ question: q, error: failureText(e) });
    }
  }

  function submit() {
    if (!draft.trim() || waiting || keyBlocked) return;
    const q = draft;
    setDraft(""); // 보내면 입력칸을 비운다
    void ask(q);
  }
  const parts = result.parts;
  // 그 파트만 펴고 접는다 — 여러 파트를 함께 펼 수 있다
  const toggle = (seq: number) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(seq)) next.delete(seq);
      else next.add(seq);
      return next;
    });
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
            <div className="result-head-actions">
              <Button kind="secondary" el="1.2" onClick={() => setDialog("export")}>
                <DownloadIcon />
                내보내기
              </Button>
              <button
                type="button"
                className="icon-btn is-outline is-danger"
                aria-label="분석 결과 삭제"
                data-el="1.3"
                onClick={() => setDialog("delete")}
              >
                <TrashIcon />
              </button>
            </div>
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
              // 질문하기 탭으로 바꾸고 바로 보낸다 — 보낼 수 없으면 탭만 바뀐다
              <button
                key={q.seq}
                type="button"
                className="pill"
                data-el={i === 0 ? "5.1" : undefined}
                onClick={() => {
                  setTab("chat");
                  void ask(q.text);
                }}
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
                {parts.length
                  ? `${result.chapters.length}개 · 파트 ${parts.length}개`
                  : `${result.chapters.length}개`}
              </span>
            </div>
            <span className="caption" data-el="6.2">
              누르면 오른쪽 스크립트가 그 위치로 이동해요
            </span>
          </div>
          <div className="chapters">
            {parts.length === 0
              ? result.chapters.map((c, i) => (
                  <ChapterCard
                    key={c.seq}
                    c={c}
                    long={long}
                    selected={selected === c.start_sec}
                    onSelect={select}
                    el={i === 0 ? "6.3" : undefined}
                  />
                ))
              : parts.map((p, pi) => {
                  const expanded = open.has(p.seq);
                  return (
                    <div key={p.seq} className="part" data-el={pi === 0 ? "6.4" : undefined}>
                      <button
                        type="button"
                        className="part-head"
                        aria-expanded={expanded}
                        data-el={pi === 0 ? "6.5" : undefined}
                        onClick={() => toggle(p.seq)}
                      >
                        <span className="part-arrow" aria-hidden="true">
                          <svg className="icon" width="18" height="18" viewBox="0 0 24 24">
                            <path d="m9 18 6-6-6-6" />
                          </svg>
                        </span>
                        <span className="part-text">
                          <span className="part-title">{p.title}</span>
                          <span className="part-count">챕터 {p.chapter_count}개</span>
                        </span>
                        <span className="part-range mono">
                          {timeLabel(p.start_sec, long)} – {timeLabel(p.end_sec, long)}
                        </span>
                      </button>
                      {expanded && (
                        <div className="part-body">
                          {result.chapters
                            .filter((c) => c.part_seq === p.seq)
                            .map((c, ci) => (
                              <ChapterCard
                                key={c.seq}
                                c={c}
                                long={long}
                                selected={selected === c.start_sec}
                                onSelect={select}
                                el={pi === 0 && ci === 0 ? "6.6" : undefined}
                              />
                            ))}
                        </div>
                      )}
                    </div>
                  );
                })}
          </div>
        </section>
      </main>

      <aside aria-label="스크립트와 질문" className="panel" data-el="7">
        <div className="panel-inner">
          <div role="tablist" aria-label="스크립트와 질문" className="tabs">
            <button
              type="button"
              role="tab"
              id="tab-script"
              aria-selected={tab === "script"}
              aria-controls="panel-script"
              className="tab"
              data-el="7.1"
              onClick={() => setTab("script")}
            >
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
            <button
              type="button"
              role="tab"
              id="tab-chat"
              aria-selected={tab === "chat"}
              aria-controls="panel-chat"
              className="tab"
              data-el="7.2"
              onClick={() => setTab("chat")}
            >
              <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
              </svg>
              질문하기
              <span className="tab-count" data-el="7.3">
                {video.chat_turn_count + asked}
              </span>
            </button>
          </div>
          <div
            role="tabpanel"
            id="panel-script"
            aria-labelledby="tab-script"
            className="script"
            data-el="8"
            hidden={tab !== "script"}
          >
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
          <div
            role="tabpanel"
            id="panel-chat"
            aria-labelledby="tab-chat"
            className="chat"
            hidden={tab !== "chat"}
          >
            <div ref={chatList} className="chat-list" data-el="9">
              {turns !== null && turns.length === 0 && pending === null && (
                <EmptyBox
                  compact
                  el="9.1"
                  title="아직 질문이 없어요"
                  body="아래 추천 질문을 누르거나 직접 물어보세요. 답에는 근거가 된 시각이 함께 붙습니다."
                />
              )}
              {turns?.map((t, i) => (
                <TurnView key={t.id} turn={t} long={long} onSelect={select} first={i === 0} />
              ))}
              {pending && (
                <div className="turn" data-el={turns?.length ? undefined : "9.2"}>
                  <div className="turn-question" data-el={turns?.length ? undefined : "9.3"}>
                    {pending.question}
                  </div>
                  <div className="turn-reply">
                    {pending.error === null ? (
                      <span role="status" className="turn-wait" data-el="9.7">
                        <span className="wait-dots va-pulse" aria-hidden="true">
                          <span />
                          <span />
                          <span />
                        </span>
                        답을 만드는 중이에요
                      </span>
                    ) : (
                      <span className="turn-fail">
                        <span role="alert" data-el="9.8">
                          {pending.error}
                        </span>
                        <button
                          type="button"
                          className="chat-retry"
                          data-el="9.9"
                          onClick={() => void ask(pending.question)}
                        >
                          다시 시도
                        </button>
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="chat-input" data-el="10">
              <div className="chat-chips">
                {result.suggested_questions.map((q, i) => (
                  <button
                    key={q.seq}
                    type="button"
                    className="chat-chip"
                    data-el={i === 0 ? "10.1" : undefined}
                    onClick={() => void ask(q.text)}
                  >
                    {q.text}
                  </button>
                ))}
              </div>
              {keyNote && (
                <p className="chat-key" data-el="10.2">
                  {keyNote.text}
                  {keyNote.link && (
                    <>
                      {" "}
                      <Link href="/settings">키 넣으러 가기</Link>
                    </>
                  )}
                </p>
              )}
              <div className="chat-box">
                <label htmlFor="ask-box" className="sr-only">
                  이 영상에 질문하기
                </label>
                <span className="chat-field" data-el="10.3">
                  <textarea
                    id="ask-box"
                    rows={2}
                    placeholder="이 영상에 대해 물어보세요"
                    value={draft}
                    disabled={keyBlocked}
                    readOnly={waiting}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => {
                      // Enter는 보내기, Shift+Enter는 줄바꿈 — 한글 조합 중인 Enter는 보내지 않는다
                      if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                        e.preventDefault();
                        submit();
                      }
                    }}
                  />
                </span>
                <button
                  type="button"
                  aria-label="보내기"
                  className="chat-send"
                  data-el="10.4"
                  aria-disabled={waiting || keyBlocked ? "true" : undefined}
                  onClick={submit}
                >
                  <svg
                    className="icon"
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path d="m5 12 7-7 7 7" />
                    <path d="M12 19V5" />
                  </svg>
                </button>
              </div>
              <span className="chat-note" data-el="10.5">
                질문, 앞선 대화, 관련 스크립트가 OpenAI로 전송됩니다.
              </span>
            </div>
          </div>
        </div>
      </aside>

      {notice && <Toast el="11" message={notice} onDone={() => setNotice(null)} />}
      {dialog === "export" && (
        <Export
          video={video}
          turns={video.chat_turn_count + asked}
          onClose={() => setDialog(null)}
          onDone={(message) => {
            setDialog(null);
            setNotice(message);
          }}
        />
      )}
      {dialog === "delete" && (
        <Delete
          video={video}
          turns={video.chat_turn_count + asked}
          onClose={() => setDialog(null)}
          onDeleted={() => {
            markListFocus();
            router.replace("/"); // 뒤로 가기가 지운 영상으로 돌아오지 않게 바꿔치기
          }}
        />
      )}
    </div>
  );
}
