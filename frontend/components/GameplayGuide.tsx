/** Entry and optional daytime help share the same rules. */
export function GameplayGuide({ compact = false }: { compact?: boolean }) {
  const rules = (
    <div className="space-y-3">
      <p className="text-lg">5일 동안 반복되는 하루를 살피고, 밤마다 세계가 왜 멸망하는지 그 원인과 동기를 밝혀 쓴다.</p>
      <ul className="list-disc space-y-2 pl-5 text-base">
        <li>하루는 6장면이다. 인물을 고르고 질문을 보내면 대화 1회를 쓴다.</li>
        <li>낮 대화는 1~5일째에 8 / 7 / 6 / 5 / 4회, 기본 총 30회다. 그날의 모든 장면과 인물이 함께 쓴다.</li>
        <li>특별한 규칙을 받아들이면 그날부터 남은 모든 날에 계속 걸린다.</li>
        <li>특별한 규칙의 대가는 미리 알려 주지 않는다.</li>
        <li>한 장면에 인물마다 한 번 물을 수 있다. 다른 인물에게는 같은 장면에서, 같은 인물에게는 다음 장면에서 남은 대화로 질문한다.</li>
        <li>다음 장면으로 가는 것은 무료다. 남은 대화는 충전되지 않는다.</li>
        <li>주변 인물의 대화 듣기와 단서 기록 보기는 무료다. ‘단서 기록 열기’를 누르면 본 행동과 들은 말을 다시 볼 수 있다.</li>
        <li>밤에 직접 쓴 글은 다음 밤에도 이어진다. 판정은 직접 쓴 글로만 하고, 관찰 기록은 쓰면서 펼쳐 참고한다.</li>
        <li>처음 네 번의 밤에는 제출 뒤 낮 대화와 별도로 3회 질문하고, 남은 모든 날에 걸릴 규칙 하나를 고른다.</li>
      </ul>
    </div>
  );
  return (
    <div className="space-y-3">
      <h2 className="text-xl">플레이 안내</h2>
      {compact ? (
        <>
          <div className="space-y-2 text-lg">
            <p>하루 6장면 · 오늘 대화 8회.</p>
            <p>한 장면에 인물마다 한 번 질문한다. 장면 이동은 무료이며 대화는 충전되지 않는다.</p>
            <p>밤에 쓴 글은 다음 밤에도 이어진다.</p>
          </div>
          <details>
            <summary className="cursor-pointer text-base">자세한 규칙</summary>
            <div className="mt-2">{rules}</div>
          </details>
        </>
      ) : rules}
    </div>
  );
}
