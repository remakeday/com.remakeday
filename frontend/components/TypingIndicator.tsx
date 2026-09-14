export function TypingIndicator() {
  return (
    <span className="inline-flex gap-0.5 text-lg leading-none" aria-label="응답 대기 중">
      <span className="typing-dot">·</span>
      <span className="typing-dot">·</span>
      <span className="typing-dot">·</span>
    </span>
  );
}
