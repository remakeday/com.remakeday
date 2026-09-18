/** 공통 기록·안내 패널의 플레이 안내. */
export function GameplayGuide() {
  const rules = (
    <div className="space-y-3">
      <p className="text-lg">5일 동안 반복되는 하루를 살피고, 밤마다 세계가 왜 멸망하는지 그 원인과 동기를 밝혀 쓴다.</p>
      <ul className="list-disc space-y-2 pl-5 text-base">
        <li>하루는 6장면이다. 인물을 고르고 질문하면 대화 1회를 쓰고, 한 장면에서 같은 인물에게는 한 번만 물을 수 있다.</li>
        <li>남은 대화는 하루치다. 장면이 바뀌어도 충전되지 않고, 다음 장면으로 가는 것은 무료다.</li>
        <li>밤에 직접 쓴 글만 판정한다. 기록은 참고용이고, 쓴 글은 다음 밤에도 이어진다.</li>
        <li>처음 네 번의 밤에는 신에게 3회 질문하고 남은 모든 날에 걸릴 규칙 하나를 고른다. 받아들인 규칙은 끝까지 풀리지 않는다.</li>
      </ul>
    </div>
  );
  return (
    <div className="space-y-3">
      <h2 className="text-xl">플레이 안내</h2>
      {rules}
    </div>
  );
}
