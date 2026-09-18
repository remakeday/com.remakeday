"use client";

export function AskBar({ input, onInput, onAsk, onNext, inputLocked, nextLocked, waitingReply, waitingBeat, hint, placeholder, failure, onRetry, dayDone, onNight }: {
  input: string;
  onInput: (value: string) => void;
  onAsk: () => void;
  onNext: () => void;
  inputLocked: boolean;
  nextLocked: boolean;
  waitingReply: boolean;
  waitingBeat: boolean;
  hint: string;
  placeholder: string;
  failure?: string;
  onRetry?: () => void;
  dayDone: boolean;
  onNight: () => void;
}) {
  return (
    <div className="shrink-0 border-t border-ink/20 px-3 py-2">
      <p id="conversation-hint" className="mb-2 text-sm text-ink/75" role="status">{hint}</p>
      {failure && <p className="mb-2 text-base" role="alert">{failure}</p>}
      {onRetry && <button type="button" onClick={onRetry} className="mb-2 border border-ink px-3 py-2 text-base">같은 질문 다시 보내기</button>}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex min-w-0 basis-full items-center gap-2 sm:flex-1 sm:basis-auto">
          <input aria-label="인물에게 질문" aria-describedby="conversation-hint" type="text" maxLength={200}
            value={input} onChange={(event) => onInput(event.target.value)} disabled={inputLocked} placeholder={placeholder}
            onKeyDown={(event) => {
              // 한글 조합 중 Enter는 전송하지 않는다.
              if (event.key === "Enter" && !event.nativeEvent.isComposing) {
                event.preventDefault();
                onAsk();
              }
            }}
            className="min-w-0 flex-1 border border-ink/40 bg-transparent px-3 py-2 text-lg outline-none placeholder:opacity-40 focus:border-ink disabled:opacity-40" />
          <button type="button" onClick={onAsk} disabled={inputLocked || !input.trim()} aria-busy={waitingReply}
            className="shrink-0 border border-ink px-3 py-2 text-lg hover:bg-ink hover:text-paper disabled:opacity-30">
            {waitingReply ? "답변 기다리는 중…" : "묻기"}
          </button>
        </div>
        <button type="button" onClick={dayDone ? onNight : onNext} disabled={nextLocked} aria-busy={waitingBeat}
          className="shrink-0 border border-ink/40 px-3 py-2 text-lg hover:border-ink disabled:opacity-30"
          title={dayDone ? undefined : "다음 장면 (무료, 대화 횟수는 충전되지 않음)"}>
          {waitingBeat ? "다음 장면 준비 중…" : dayDone ? "밤이 온다" : "다음 장면"}
        </button>
      </div>
    </div>
  );
}
