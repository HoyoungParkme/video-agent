/**
 * VA-UI-002#UI-4 12 ~ 14 한눈에 보기 — 한 줄 요약(3)과 핵심 인사이트(4) 사이. 12.1 개수 · 12.2 안내,
 * 13 타임라인 카드(13.1 파트 띠 · 13.2 인사이트 점 · 13.3 챕터 막대 · 13.4 시각 눈금 · 13.5 범례),
 * 14 마인드맵 카드(14.1 뿌리 → 14.2 챕터 노드 · 14.3 요점, 파트가 있으면 14.4 파트 노드 → 14.5 파트 안 챕터 노드),
 * 맨 아래 15 인포그래픽 카드(Result.tsx가 children으로 넘긴다 — screens/result/InfographicCard).
 * 이미 받은 결과로만 그리고 서버에 묻지 않는다. 고른 시각과 펼친 파트는 Result.tsx가 갖고 여기는 그리기만 한다
 * (VA-DOM-002 1장). 막대 · 점 · 파트 띠 · 챕터 노드는 시각 누르기(공통 1.3)다 — 고른 시각이 든 챕터의 칸 · 노드와
 * 그 시각이 든 파트 띠가 강조되고, 그 시각이 근거인 점이 채워진다(VA-UI-001 4.4). 파트 노드는 펴고 접기이고
 * 챕터 목록의 파트 머리(6.5)와 같은 상태를 쓴다. 가로 위치는 모두 영상 길이 비례다 — 칸도 점 · 눈금과
 * 같이 시작 시각 자리에 놓고 틈은 폭에서 뺀다. 막대 칸 글자와 점 줄은 카드 안 폭(px)으로 정한다 — 창 폭이
 * 바뀌면 다시 잰다.
 */
"use client";

import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

import type { Chapter, Result } from "@/api/client";
import { timeLabel } from "@/components/TimeChip";

// 막대 칸 글자 — 칸이 이 폭을 넘으면 '{번호} {제목}', 번호 폭을 넘으면 번호만, 더 좁으면 없다(UI-4 규칙)
const TITLE_PX = 110;
const NUMBER_PX = 22;
// 칸 사이 틈 — 칸 폭에서 뺀다(마지막 칸은 빼지 않는다)
const GAP_PX = 2;
// 인사이트 점 — 이미 놓인 점과 이 거리 안이면 한 줄 아래로, 셋째 줄까지. 줄 간격은 점 26px + 4px
const DOT_PX = 26;
const DOT_NEAR_PX = 30;
const DOT_ROW_PX = 30;
const DOT_ROWS = 3;
// 시각 눈금 — 1시간 미만 10분 · 이상 30분 간격. 끝 눈금과 간격의 35% 안으로 붙는 눈금은 뺀다
const TICK_SEC = 600;
const TICK_LONG_SEC = 1800;
const TICK_NEAR_END = 0.35;
const MAX_BULLETS = 3;

type Part = Result["parts"][number];

interface Props {
  result: Result;
  long: boolean;
  /** 고른 시각(초). 처음에는 없다 */
  selected: number | null;
  /** 펼친 파트 번호 — 챕터 목록의 파트 카드와 같은 상태 */
  open: Set<number>;
  onSelect: (sec: number) => void;
  onToggle: (partSeq: number) => void;
  /** 한눈에 보기 맨 아래 — 인포그래픽 카드(15) */
  children?: ReactNode;
}

/** 두 자리 번호 — 인사이트 번호(01, 02 …). */
function two(n: number): string {
  return String(n).padStart(2, "0");
}

/** 고른 시각이 든 것 — 시작이 그 시각 이하인 마지막 것. 고른 시각이 없으면 null. */
function holding<T extends { start_sec: number }>(items: T[], sec: number | null): T | null {
  if (sec === null) return null;
  let found: T | null = null;
  for (const item of items) {
    if (item.start_sec > sec) break;
    found = item;
  }
  return found;
}

/** 챕터 길이(초) — 다음 챕터 시작까지, 마지막 챕터는 영상 끝까지. */
function chapterSecs(chapters: Chapter[], duration: number): number[] {
  return chapters.map((c, i) =>
    Math.max((chapters[i + 1]?.start_sec ?? duration) - c.start_sec, 0),
  );
}

/** 시각 눈금 — 0부터 간격마다, 끝에 영상 길이. 끝 눈금에 너무 붙는 눈금은 뺀다. */
function ticks(duration: number, long: boolean): number[] {
  const step = long ? TICK_LONG_SEC : TICK_SEC;
  const marks = [0];
  for (let t = step; t < duration; t += step) {
    if (duration - t >= step * TICK_NEAR_END) marks.push(t);
  }
  if (duration > 0) marks.push(duration);
  return marks;
}

/** 점마다 줄 번호 — 인사이트 순서대로 놓으며, 놓인 점과 가까우면 아랫줄로. xs는 점 가운데(px). */
function dotRows(xs: number[]): number[] {
  const placed: number[][] = Array.from({ length: DOT_ROWS }, () => []);
  return xs.map((x) => {
    const free = placed.findIndex((row) => row.every((y) => Math.abs(x - y) >= DOT_NEAR_PX));
    const row = free < 0 ? DOT_ROWS - 1 : free;
    placed[row].push(x);
    return row;
  });
}

/** 요소 안쪽 폭(px) — 그리기 전에 재고, 창 폭이 바뀌면 다시 잰다. */
function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const measure = () => setWidth(el.clientWidth);
    measure();
    const watch = new ResizeObserver(measure);
    watch.observe(el);
    return () => watch.disconnect();
  }, []);
  return [ref, width] as const;
}

/** 칸의 자리 — 왼쪽 끝은 시작 시각 자리, 폭은 길이 비례에서 틈을 뺀다(마지막 칸은 그대로). */
function cell(start: number, secs: number, total: number, last: boolean): CSSProperties {
  const share = (Math.max(secs, 0) / total) * 100;
  return {
    left: `${(Math.min(Math.max(start, 0), total) / total) * 100}%`,
    width: last ? `${share}%` : `max(calc(${share}% - ${GAP_PX}px), 0px)`,
  };
}

/**
 * 13 타임라인 카드 — (파트 띠) · 인사이트 점 · 챕터 막대 · 시각 눈금 · 범례. 칸은 점 · 눈금과 같은 비례로
 * 놓는다 — flex 몫으로 늘리면 틈이 쌓여 긴 영상에서 칸 경계가 점 · 눈금과 14px까지 어긋났다(UI-4 규칙).
 */
function Timeline({ result, long, selected, onSelect }: Omit<Props, "open" | "onToggle">) {
  const [track, width] = useWidth<HTMLDivElement>();
  const { chapters, parts } = result;
  const { insights } = result.summary;
  const duration = result.video.duration_sec;
  const total = Math.max(duration, 1);
  const pct = (sec: number) => `${(Math.min(Math.max(sec, 0), total) / total) * 100}%`;
  const secs = chapterSecs(chapters, duration);
  const chapter = holding(chapters, selected);
  const part = holding(parts, selected);
  const rows = dotRows(insights.map((ins) => (ins.source_secs[0] / total) * width));
  const rowCount = Math.max(0, ...rows) + 1;
  const marks = ticks(duration, long);

  return (
    <div className="timeline" data-el="13">
      {parts.length > 0 && (
        <div className="timeline-band">
          {parts.map((p, i) => (
            <button
              key={p.seq}
              type="button"
              className={`band-cell${i % 2 === 1 ? " is-alt" : ""}`}
              style={cell(p.start_sec, p.end_sec - p.start_sec, total, i === parts.length - 1)}
              aria-label={`파트 ${p.seq} · ${timeLabel(p.start_sec, long)} ${p.title}`}
              aria-pressed={part?.seq === p.seq}
              data-el={i === 0 ? "13.1" : undefined}
              onClick={() => onSelect(p.start_sec)}
            >
              <span className="cell-label">
                {p.seq} {p.title}
              </span>
            </button>
          ))}
        </div>
      )}
      <div
        ref={track}
        className="timeline-dots"
        style={{ height: DOT_PX + DOT_ROW_PX * (rowCount - 1) }}
      >
        {insights.map((ins, i) => {
          const first = ins.source_secs[0];
          return (
            <button
              key={ins.seq}
              type="button"
              className="dot"
              style={{ left: pct(first), top: rows[i] * DOT_ROW_PX }}
              aria-label={`인사이트 ${two(ins.seq)} · ${timeLabel(first, long)}`}
              aria-pressed={selected !== null && ins.source_secs.includes(selected)}
              data-el={i === 0 ? "13.2" : undefined}
              onClick={() => onSelect(first)}
            >
              {two(ins.seq)}
            </button>
          );
        })}
      </div>
      <div className="timeline-bars">
        {chapters.map((c, i) => {
          const last = i === chapters.length - 1;
          const px = (width * secs[i]) / total - (last ? 0 : GAP_PX); // 그린 칸 폭
          const wide = px > TITLE_PX;
          return (
            <button
              key={c.seq}
              type="button"
              className={`bar-cell${i % 2 === 1 ? " is-alt" : ""}${wide ? " is-wide" : ""}`}
              style={cell(c.start_sec, secs[i], total, last)}
              aria-label={`챕터 ${c.seq} · ${timeLabel(c.start_sec, long)} ${c.title}`}
              aria-pressed={chapter?.seq === c.seq}
              data-el={i === 0 ? "13.3" : undefined}
              onClick={() => onSelect(c.start_sec)}
            >
              <span className="cell-label">
                {wide ? `${c.seq} ${c.title}` : px > NUMBER_PX ? c.seq : null}
              </span>
            </button>
          );
        })}
      </div>
      <div className="timeline-ticks mono" data-el="13.4">
        {marks.map((t, i) => (
          <span
            key={t}
            className={i === 0 ? "is-first" : i === marks.length - 1 ? "is-last" : undefined}
            style={{ left: pct(t) }}
          >
            {timeLabel(t, long)}
          </span>
        ))}
      </div>
      <div className="timeline-legend" data-el="13.5">
        <span className="legend-item">
          <span className="legend-bar" aria-hidden="true" />
          막대 = 챕터 {chapters.length}개(길이만큼)
        </span>
        <span className="legend-item">
          <span className="legend-dot" aria-hidden="true" />점 = 인사이트 {insights.length}개(첫
          근거 시각)
        </span>
      </div>
    </div>
  );
}

/**
 * 14 마인드맵 카드 — 뿌리에서 오른쪽으로. 파트가 없으면 챕터 노드와 요점, 있으면 파트 노드와 펼친 파트의 챕터.
 * 줄 높이와 가지를 잇는 세로선은 CSS가 정한다(.mind-row · .mind-leaf-row) — 높이를 여기서 셈하지 않는다.
 */
function MindMap({ result, long, selected, open, onSelect, onToggle }: Props) {
  const { chapters, parts } = result;
  const chapter = holding(chapters, selected);
  const inPart = (p: Part) => chapters.filter((c) => c.part_seq === p.seq);
  const name = (c: Chapter) => `챕터 ${c.seq} · ${timeLabel(c.start_sec, long)} ${c.title}`;

  return (
    <div className="mindmap" data-el="14">
      <div className="mind-tree">
        <div className="mind-root" data-el="14.1">
          <span className="mind-root-label">한 줄 요약</span>
          <span className="mind-root-text">{result.summary.one_liner}</span>
        </div>
        <span className="mind-link" aria-hidden="true" />
        <div className="mind-branches">
          {parts.length === 0
            ? chapters.map((c, i) => (
                <div key={c.seq} className="mind-row">
                  <span className="mind-stub" aria-hidden="true" />
                  <button
                    type="button"
                    className="mind-node"
                    aria-label={name(c)}
                    aria-pressed={chapter?.seq === c.seq}
                    data-el={i === 0 ? "14.2" : undefined}
                    onClick={() => onSelect(c.start_sec)}
                  >
                    <span className="mind-node-time mono">{timeLabel(c.start_sec, long)}</span>
                    <span className="mind-node-title">{c.title}</span>
                  </button>
                  {c.bullets.length > 0 && (
                    <>
                      <span className="mind-tick" aria-hidden="true" />
                      <span className="mind-bullets">
                        {c.bullets.slice(0, MAX_BULLETS).map((b, j) => (
                          <span key={j} title={b} data-el={i === 0 && j === 0 ? "14.3" : undefined}>
                            · {b}
                          </span>
                        ))}
                      </span>
                    </>
                  )}
                </div>
              ))
            : parts.map((p, i) => {
                const expanded = open.has(p.seq);
                return (
                  <div key={p.seq} className="mind-row is-part">
                    <span className="mind-stub" aria-hidden="true" />
                    <button
                      type="button"
                      className="mind-part"
                      aria-expanded={expanded}
                      data-el={i === 0 ? "14.4" : undefined}
                      onClick={() => onToggle(p.seq)}
                    >
                      <span className="mind-part-arrow" aria-hidden="true">
                        <svg className="icon" width="14" height="14" viewBox="0 0 24 24">
                          <path d="m9 18 6-6-6-6" />
                        </svg>
                      </span>
                      <span className="mind-part-text">
                        <span className="mind-part-title">
                          {p.seq}. {p.title}
                        </span>
                        <span className="mind-part-meta">
                          챕터 {p.chapter_count}개 · {timeLabel(p.start_sec, long)}
                        </span>
                      </span>
                    </button>
                    {expanded && (
                      <>
                        <span className="mind-link is-short" aria-hidden="true" />
                        <div className="mind-leaves">
                          {inPart(p).map((c, j) => (
                            <div key={c.seq} className="mind-leaf-row">
                              <span className="mind-stub is-leaf" aria-hidden="true" />
                              <button
                                type="button"
                                className="mind-leaf"
                                aria-label={name(c)}
                                aria-pressed={chapter?.seq === c.seq}
                                data-el={i === 0 && j === 0 ? "14.5" : undefined}
                                onClick={() => onSelect(c.start_sec)}
                              >
                                <span className="mind-leaf-time mono">
                                  {timeLabel(c.start_sec, long)}
                                </span>
                                <span className="mind-leaf-title">{c.title}</span>
                              </button>
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
        </div>
      </div>
    </div>
  );
}

export default function Glance(props: Props) {
  const { parts, chapters, summary } = props.result;
  const counts = `챕터 ${chapters.length} · 인사이트 ${summary.insights.length}`;
  return (
    <section aria-labelledby="glance-title" className="result-section" data-el="12">
      <div className="result-section-head result-section-head-split">
        <div className="result-section-head">
          <h2 id="glance-title" className="section-title">
            한눈에 보기
          </h2>
          <span className="count" data-el="12.1">
            {parts.length ? `파트 ${parts.length} · ${counts}` : counts}
          </span>
        </div>
        <span className="caption" data-el="12.2">
          누르면 오른쪽 스크립트가 그 위치로 이동해요
        </span>
      </div>
      <Timeline
        result={props.result}
        long={props.long}
        selected={props.selected}
        onSelect={props.onSelect}
      />
      <MindMap {...props} />
      {props.children}
    </section>
  );
}
