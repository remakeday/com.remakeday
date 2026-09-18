export type DayMode = "intro" | "dialogue";

export interface DayModeState {
  mode: DayMode;
  pawOpen: boolean;
}

type DayModeEvent =
  | { type: "reached_end"; hasPawOffer: boolean }
  | { type: "next_scene" }
  | { type: "paw_resolved"; hasScene: boolean };

export const initialDayMode: DayModeState = { mode: "intro", pawOpen: false };

/** 도입을 다 읽은 뒤에만 제안을 열고, 수락 즉시 장면은 다시 도입으로 읽는다. */
const transitions: Record<DayMode, (state: DayModeState, event: DayModeEvent) => DayModeState> = {
  intro: (state, event) => {
    switch (event.type) {
      case "reached_end":
        if (state.pawOpen) return state;
        return event.hasPawOffer ? { mode: "intro", pawOpen: true } : { mode: "dialogue", pawOpen: false };
      case "paw_resolved":
        return { mode: event.hasScene ? "intro" : "dialogue", pawOpen: false };
      default:
        return state;
    }
  },
  dialogue: (state, event) => event.type === "next_scene" ? initialDayMode : state,
};

export function dayModeReducer(state: DayModeState, event: DayModeEvent): DayModeState {
  return transitions[state.mode](state, event);
}
