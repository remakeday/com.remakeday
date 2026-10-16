import { useEffect } from "react";

/**
 * 판 진행 중 새로고침·탭 닫기·사이트 이탈 시 브라우저 확인창.
 * 판은 이어하기로 다시 열 수 있지만, 보내지 않은 밤 글·오늘 대화 말풍선·열린 팝업은 되살아나지 않아 경고는 남긴다.
 */
export function useLeaveWarning(active: boolean): void {
  useEffect(() => {
    if (!active) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      // 최신 브라우저는 커스텀 문구를 무시하고 기본 확인창만 띄운다.
      event.returnValue = "지금 나가도 다시 들어오면 이어서 할 수 있습니다. 쓰던 글과 오늘 대화 말풍선은 남지 않습니다.";
      return event.returnValue;
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [active]);
}
