/**
 * VA-UI-002#UI-5 설정 — 1 제목 · 2 키 카드(2.1 상태 배지 · 2.2 지금 쓰는 키 · 2.3 새 키 · 2.4 확인하고 저장 ·
 * 2.5 키 확인 오류 · 2.6 도움말) · 3 모델 카드(3.1 · 3.2 받아쓰기 · 3.3 · 3.4 요약) · 4 폴더(4.1) ·
 * 5 밖으로 나가는 데이터(5.1 · 5.2) · 6 버튼 줄(6.1 취소 · 6.2 저장)
 */
"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, api, publishSettings, useSettings, type ModelOption } from "@/api/client";
import { Button } from "@/components/buttons";

const OUTGOING = [
  ["OpenAI", "음성 조각", "자막 없는 영상을 받아쓸 때"],
  ["OpenAI", "스크립트 텍스트", "요약 · 챕터 · 추천 질문을 만들 때"],
  ["OpenAI", "질문, 앞선 대화, 관련 스크립트", "질문할 때"],
  ["YouTube", "영상 주소", "정보 · 자막 · 음성을 받을 때"],
];

/** '$0.006' · '$0.25' · '$15.00' — 소수 둘째 자리까지는 늘 쓰고, 더 있으면 그대로 */
function usd(value: number | undefined): string {
  if (value === undefined) return "—";
  const digits = Math.max(2, (String(value).split(".")[1] ?? "").length);
  return `$${value.toFixed(digits)}`;
}

/** '오늘 14:02' 또는 '9월 12일'(VA-UI-002 UI-5 규칙, UI-1 목록 행과 같다) */
function when(iso: string): string {
  const at = new Date(iso);
  const now = new Date();
  if (at.toDateString() === now.toDateString()) {
    const hh = String(at.getHours()).padStart(2, "0");
    const mm = String(at.getMinutes()).padStart(2, "0");
    return `오늘 ${hh}:${mm}`;
  }
  return `${at.getMonth() + 1}월 ${at.getDate()}일`;
}

function pick(options: ModelOption[], id: string | null): ModelOption | undefined {
  return options.find((o) => o.id === id) ?? options[0];
}

export default function Settings() {
  const router = useRouter();
  const settings = useSettings();
  const [newKey, setNewKey] = useState("");
  const [checking, setChecking] = useState(false);
  // 2.4가 실패한 직후에만 새로 넣은 키의 결과를 보인다. 다시 열면 저장된 키의 결과로 돌아간다
  const [keyError, setKeyError] = useState<string | null>(null);
  // 고른 모델. 고르기 전에는 저장된 모델이 골라져 있다
  const [stt, setStt] = useState<string | null>(null);
  const [text, setText] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  if (!settings) return <main className="settings" aria-busy="true" />;

  const key = settings.key;
  const stored = key.state === "invalid" ? `키를 확인하지 못했어요 — ${key.reason}` : null;
  const failed = keyError !== null || key.state === "invalid";
  const error = keyError ?? stored;
  const sttOption = pick(settings.model_options.stt, stt ?? settings.models.stt);
  const textOption = pick(settings.model_options.text, text ?? settings.models.text);

  async function checkAndSave() {
    if (!newKey.trim() || checking) return; // 비어 있으면 보내지 않는다
    setChecking(true);
    try {
      const next = await api.saveKey(newKey);
      publishSettings(next); // 배너와 분석 버튼이 바로 따라온다
      setNewKey("");
      setKeyError(null);
    } catch (e) {
      const reason = e instanceof ApiError ? e.reason : "서버에 닿지 못했습니다";
      setKeyError(`키를 확인하지 못했어요 — ${reason}`);
    } finally {
      setChecking(false);
    }
  }

  async function saveModels() {
    if (!sttOption || !textOption || saving) return;
    setSaving(true);
    try {
      publishSettings(await api.saveModels(sttOption.id, textOption.id));
      router.push("/");
    } catch {
      setSaving(false);
    }
  }

  return (
    <main className="settings">
      <div className="settings-heading" data-el="1">
        <h1 className="page-title">설정</h1>
        <p className="page-lead">키와 모델 설정은 이 PC에만 저장됩니다.</p>
      </div>

      <section aria-labelledby="key-title" className="card settings-card" data-el="2">
        <div className="settings-card-head">
          <div className="settings-card-title">
            <svg className="icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="7.5" cy="15.5" r="5.5" />
              <path d="m21 2-9.6 9.6" />
              <path d="m15.5 7.5 3 3L22 7l-3-3" />
            </svg>
            <h2 id="key-title">OpenAI API 키</h2>
          </div>
          {!failed && key.state === "ok" ? (
            <span className="badge badge-ok" data-el="2.1">
              <svg
                className="icon icon-bold"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M20 6 9 17l-5-5" />
              </svg>
              확인됨{key.checked_at ? ` · ${when(key.checked_at)}` : ""}
            </span>
          ) : (
            <span className="badge badge-danger" data-el="2.1">
              {failed ? "확인 실패" : "키 없음"}
            </span>
          )}
        </div>

        {key.masked && (
          <div className="field">
            <span className="field-label">지금 쓰는 키</span>
            <div className="value-box" data-el="2.2">
              <span className="value-box-text">{key.masked}</span>
              <span className="value-box-caption">{key.stored_in}</span>
            </div>
          </div>
        )}

        <div className="field">
          <label htmlFor="new-key" className="field-label">
            {key.masked ? "새 키로 바꾸기" : "키 넣기"}
          </label>
          <div className="field-row">
            <span className="field-wrap" data-el="2.3">
              <input
                id="new-key"
                type="password"
                className="field-input"
                placeholder="sk-로 시작하는 키를 붙여 넣으세요"
                value={newKey}
                disabled={checking}
                aria-invalid={keyError ? "true" : undefined}
                aria-describedby={error ? "key-error" : undefined}
                autoComplete="off"
                onChange={(e) => setNewKey(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void checkAndSave();
                }}
              />
            </span>
            <Button kind="secondary" tall busy={checking} el="2.4" onClick={checkAndSave}>
              확인하고 저장
            </Button>
          </div>
          {error && (
            <span id="key-error" role="alert" className="field-error" data-el="2.5">
              {error}
            </span>
          )}
          <span className="field-help" data-el="2.6">
            붙여 넣으면 가벼운 요청으로 먼저 확인한 뒤 저장합니다. 키는 저장소에 커밋되지 않아요.
          </span>
        </div>
      </section>

      <section aria-labelledby="model-title" className="card settings-card" data-el="3">
        <h2 id="model-title" className="settings-h2">
          모델
        </h2>
        <div className="settings-models">
          <div className="field">
            <label htmlFor="stt-model" className="field-label">
              받아쓰기
            </label>
            <span className="field-wrap" data-el="3.1">
              <select
                id="stt-model"
                className="field-select"
                value={sttOption?.id}
                onChange={(e) => setStt(e.target.value)}
              >
                {settings.model_options.stt.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.label}
                  </option>
                ))}
              </select>
            </span>
            <span className="field-help" data-el="3.2">
              분당 {usd(sttOption?.price.per_min_usd)} · 구간 시각을 주는 모델만 고를 수 있어요
            </span>
          </div>
          <div className="field">
            <label htmlFor="llm-model" className="field-label">
              요약 · 챕터 · 질문
            </label>
            <span className="field-wrap" data-el="3.3">
              <select
                id="llm-model"
                className="field-select"
                value={textOption?.id}
                onChange={(e) => setText(e.target.value)}
              >
                {settings.model_options.text.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.label}
                  </option>
                ))}
              </select>
            </span>
            <span className="field-help" data-el="3.4">
              100만 토큰당 입력 {usd(textOption?.price.input_per_mtok_usd)} · 출력{" "}
              {usd(textOption?.price.output_per_mtok_usd)}
            </span>
          </div>
        </div>
      </section>

      <section
        aria-labelledby="inbox-title"
        className="card settings-card settings-card-tight"
        data-el="4"
      >
        <h2 id="inbox-title" className="settings-h2">
          로컬 파일 폴더
        </h2>
        <div className="value-box value-box-folder" data-el="4.1">
          <svg className="icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
          </svg>
          <span className="value-box-text">{settings.inbox_path}</span>
          <span className="value-box-caption">읽기 전용</span>
        </div>
        <span className="field-help">
          이 폴더의 파일을 읽기만 하고 고치거나 지우지 않아요. 위치는 docker-compose.yml에서 바꿀 수
          있습니다.
        </span>
      </section>

      <section
        aria-labelledby="data-title"
        className="card settings-card settings-card-tight"
        data-el="5"
      >
        <h2 id="data-title" className="settings-h2">
          밖으로 나가는 데이터
        </h2>
        <div data-el="5.1">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">어디로</th>
                <th scope="col">무엇이</th>
                <th scope="col">언제</th>
              </tr>
            </thead>
            <tbody>
              {OUTGOING.map(([where, what, at]) => (
                <tr key={what}>
                  <td>{where}</td>
                  <td>{what}</td>
                  <td>{at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <span className="field-help" data-el="5.2">
          원본 영상 파일, 분석 결과, API 키는 이 PC 밖으로 나가지 않습니다.
        </span>
      </section>

      <div className="settings-actions" data-el="6">
        {/* 모델 변경을 버린다. 키는 2.4에서 이미 저장됐으므로 되돌리지 않는다 */}
        <Button kind="secondary" el="6.1" onClick={() => router.push("/")}>
          취소
        </Button>
        <Button kind="primary" el="6.2" busy={saving} onClick={saveModels}>
          저장
        </Button>
      </div>
    </main>
  );
}
