/**
 * 코드값 → 화면 글자. 두 화면 이상이 쓰는 표기만 — 단계 이름(VA-UI-002 UI-3 규칙) · 언어 이름 ·
 * 분석한 때('오늘 14:08' · '9월 12일'). 시각 표기는 components/TimeChip이 가진다.
 */
import type { JobStage } from "@/api/client";

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
