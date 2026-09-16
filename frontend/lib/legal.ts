/** 법적 고지·footer에서 공유하는 서비스 식별 정보. */
export const LEGAL = {
  serviceName: "Remake Day",
  operator: "BeyondBob",
  contactEmail: "privacy@remakeday.com",
  effectiveDate: "2026년 9월 15일",
  /** Google OAuth에 요청하는 범위. Gmail·Drive 등 추가 API는 요청하지 않음. */
  googleOAuthScopes: ["openid", "email", "profile"] as const,
} as const;
