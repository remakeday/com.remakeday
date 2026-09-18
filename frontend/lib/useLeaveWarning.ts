import { useEffect } from "react";

/** 판 진행 중 새로고침·탭 닫기·사이트 이탈 시 브라우저 확인창. 이어받기는 없다. */
export function useLeaveWarning(active: boolean): void {
  useEffect(() => {
    if (!active) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      // 최신 브라우저는 커스텀 문구를 무시하고 기본 확인창만 띄운다.
      event.returnValue = "나가면 이 판은 사라집니다";
      return event.returnValue;
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [active]);
}
