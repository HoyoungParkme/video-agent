/**
 * 코드값 → 화면 글자. 두 화면 이상이 쓰는 표기만 — 단계 이름(VA-UI-002 UI-3 규칙) · 언어 이름 ·
 * 분석한 때('오늘 14:08' · '9월 12일') · 음성 파일 판정 · 값(USD) · 인포그래픽 만든 정보. 시각 표기는
 * components/TimeChip이 가진다.
 */
import type { InfographicImage, JobStage } from "@/api/client";

/** 단계 이름(4.3). download는 자막이 있으면 '자막 가져오기', 없으면 '음성 내려받기'. */
export function stageName(stage: JobStage, hasCaptions: boolean): string {
  switch (stage) {
    case "download":
      return hasCaptions ? "자막 가져오기" : "음성 내려받기";
    case "extract":
      return "음성 추출";
    case "transcribe":
      return "받아쓰기";
    case "summarize":
      return "핵심 요약";
    case "chapter":
      return "챕터";
    case "suggest":
      return "추천 질문";
    case "frames":
      return "장면";
    default:
      return "";
  }
}

const LANGUAGES: Record<string, string> = {
  ko: "한국어",
  en: "영어",
  ja: "일본어",
  zh: "중국어",
  es: "스페인어",
  fr: "프랑스어",
  de: "독일어",
  pt: "포르투갈어",
  ru: "러시아어",
  vi: "베트남어",
};

/** 언어 코드 → 이름. 모르는 코드는 그대로. */
export function languageName(code: string | null): string {
  if (!code) return "";
  return LANGUAGES[code] ?? code;
}

/** 분석한 때 — 오늘이면 '오늘 HH:MM', 아니면 'M월 D일'. 브라우저의 시간대로. */
export function analyzedLabel(iso: string, now: Date = new Date()): string {
  const at = new Date(iso);
  const sameDay =
    at.getFullYear() === now.getFullYear() &&
    at.getMonth() === now.getMonth() &&
    at.getDate() === now.getDate();
  if (sameDay) {
    const two = (n: number) => String(n).padStart(2, "0");
    return `오늘 ${two(at.getHours())}:${two(at.getMinutes())}`;
  }
  return `${at.getMonth() + 1}월 ${at.getDate()}일`;
}

// 받는 형식 — 서버 설정값 VIDEO_EXTS · AUDIO_EXTS(MS-001 ACCEPTED)와 같다. 음성 파일은 추출 단계가
// 없다(UC-H2 2b). 올리기는 보내기 전에 이 목록으로 거른다(UI-1 규칙)
const VIDEO_EXTS = ["mp4", "mkv", "mov", "webm"];
const AUDIO_EXTS = ["mp3", "m4a", "wav"];
export const ACCEPTED = [...VIDEO_EXTS, ...AUDIO_EXTS];
/** 받는 형식 안내 — '영상 mp4 · mkv · mov · webm, 음성 mp3 · m4a · wav'(UI-1 4.9 · 8.3) */
export const KINDS = `영상 ${VIDEO_EXTS.join(" · ")}, 음성 ${AUDIO_EXTS.join(" · ")}`;

/**
 * 파일 크기 — 1 GB 이상이면 GB 소수 한 자리, 1 MB 이상이면 MB 정수, 그 아래는 KB(UI-1 4.3 · 4.13 ·
 * 4.17, UI-6 '올린 사본'). unit을 주면 그 크기로 단위를 정한다('0.7 GB / 1.8 GB'처럼 보낸 / 전체를
 * 같은 단위로).
 */
export function sizeLabel(bytes: number, unit = bytes): string {
  if (unit >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  if (unit >= 1e6) return `${Math.round(bytes / 1e6)} MB`;
  return `${Math.max(1, Math.round(bytes / 1e3))} KB`;
}

/** 파일 이름이 음성 파일인가 — 확장자를 소문자로 본다. */
export function isAudioFile(name: string): boolean {
  const dot = name.lastIndexOf(".");
  return dot >= 0 && AUDIO_EXTS.includes(name.slice(dot + 1).toLowerCase());
}

/** '$0.006' · '$0.25' · '$15.00' — 소수 둘째 자리까지는 늘 쓰고, 더 있으면 그대로(UI-5 · UI-4 · UI-8). */
export function usd(value: number | undefined): string {
  if (value === undefined) return "—";
  const digits = Math.max(2, (String(value).split(".")[1] ?? "").length);
  return `$${value.toFixed(digits)}`;
}

const QUALITY_NAMES = { low: "낮은 품질", medium: "중간 품질" } as const;

/** 인포그래픽 만든 정보 — '{이미지 모델} · {품질} · {만든 시각} 만듦'(UI-4 15.6 · UI-9 1.2). */
export function madeLabel(image: InfographicImage, now: Date = new Date()): string {
  return `${image.model} · ${QUALITY_NAMES[image.quality]} · ${analyzedLabel(image.created_at, now)} 만듦`;
}
