import type { Metadata } from "next";
import { LegalDoc, LegalSection } from "@/components/LegalDoc";
import { LEGAL } from "@/lib/legal";

export const metadata: Metadata = {
  title: `개인정보 처리방침 · ${LEGAL.serviceName}`,
  description: `${LEGAL.serviceName} 개인정보 처리방침`,
};

export default function PrivacyPage() {
  return (
    <LegalDoc title="개인정보 처리방침">
      <LegalSection title="1. 총칙">
        <p>
          {LEGAL.operator}(이하 &quot;운영팀&quot;)은 {LEGAL.serviceName}(이하
          &quot;서비스&quot;)를 운영하면서 「개인정보 보호법」 등 관련 법령에
          따라 이용자의 개인정보를 보호하고, 이와 관련한 고충을 신속·원활하게
          처리할 수 있도록 다음과 같이 개인정보 처리방침을 수립·공개합니다.
        </p>
        <p>
          본 방침은 서비스 웹사이트·애플리케이션 및 Google 계정을 통한 로그인
          기능이 포함된 서비스 이용 전반에 적용됩니다.
        </p>
      </LegalSection>

      <LegalSection title="2. 개인정보의 처리 목적">
        <p>운영팀은 다음 목적을 위해 개인정보를 처리합니다. 목적이 변경되는 경우 사전 고지 후 동의를 받습니다.</p>
        <ul className="list-disc space-y-2 pl-5">
          <li>Google OAuth를 통한 회원 식별·인증 및 로그인 상태 유지</li>
          <li>게임 세션·진행 기록·점수·회고 등 플레이 데이터의 저장과 복원</li>
          <li>서비스 제공, 장애 대응, 부정 이용 방지 및 보안</li>
          <li>이용자 문의 응대 및 공지 전달</li>
          <li>서비스 품질 개선을 위한 통계·분석(가능한 경우 가명·집계 처리)</li>
        </ul>
      </LegalSection>

      <LegalSection title="3. 수집하는 개인정보 항목">
        <p className="font-semibold">가. Google 계정 로그인(OAuth) 시</p>
        <p>
          서비스는 Google OAuth 2.0 인증 코드 흐름을 사용합니다. 이용자가
          Google 로그인에 동의하면, 운영팀 서버의 콜백 엔드포인트로 인증
          결과가 전달되고, 운영팀은 Google이 동의한 범위에서 신원 정보를
          확인한 뒤 서비스 계정을 생성·연동합니다.
        </p>
        <p>
          요청하는 OAuth 범위(scope)는{" "}
          <span className="font-semibold">
            {LEGAL.googleOAuthScopes.join(", ")}
          </span>
          로 한정됩니다. Gmail, Google Drive, 연락처, 캘린더 등 그 밖의
          Google 사용자 데이터·API에는 접근하지 않습니다.
        </p>
        <p>위 범위에서 수집·이용할 수 있는 항목은 다음과 같습니다.</p>
        <ul className="list-disc space-y-2 pl-5">
          <li>Google 계정 고유 식별자(sub)</li>
          <li>이메일 주소</li>
          <li>이름(표시 이름)</li>
          <li>프로필 이미지 URL(제공되는 경우)</li>
        </ul>
        <p>
          운영팀은 Google 계정 비밀번호를 수집·저장하지 않습니다. 로그인
          화면과 비밀번호 입력은 Google이 처리하며, Google이 처리하는 정보에
          대해서는{" "}
          <a
            href="https://policies.google.com/privacy"
            className="underline underline-offset-4"
            target="_blank"
            rel="noopener noreferrer"
          >
            Google 개인정보처리방침
          </a>
          이 적용됩니다. Google에서 받은 액세스 토큰 등은 신원 확인 목적에만
          사용하고, Google 계정의 다른 데이터에 접근하는 용도로 보관·재사용하지
          않습니다.
        </p>

        <p className="mt-4 font-semibold">나. 서비스 이용 과정에서 생성·수집되는 정보</p>
        <ul className="list-disc space-y-2 pl-5">
          <li>서비스가 발급하는 로그인 세션·토큰 정보(쿠키 등으로 유지될 수 있음)</li>
          <li>게임 세션·시도(attempt) 식별자, 회차·장면 진행 상태</li>
          <li>이용자가 입력한 질문·밤 서술·신의 개입 응답 등 플레이 텍스트</li>
          <li>점수, 클리어/실패 결과, 관찰·이벤트 로그 등 게임 기록</li>
          <li>
            접속 로그: IP 주소, 브라우저·기기 정보, 접속 일시, 오류 기록 등
            자동 생성 정보
          </li>
          <li>쿠키·로컬 스토리지 등 서비스 운영에 필요한 식별·설정 정보</li>
        </ul>
      </LegalSection>

      <LegalSection title="4. 개인정보의 처리 및 보유 기간">
        <p>
          운영팀은 법령에 따른 보유·이용 기간 또는 수집 시 동의받은 기간 내에서
          개인정보를 처리·보유합니다. 원칙적으로 회원 탈퇴 또는 목적 달성 시
          지체 없이 파기합니다. 다만 다음의 경우에는 해당 기간 동안 보관할 수
          있습니다.
        </p>
        <ul className="list-disc space-y-2 pl-5">
          <li>계정·로그인 정보: 회원 탈퇴 시까지(법령상 보존 의무가 있는 경우 해당 기간)</li>
          <li>플레이 기록: 서비스 제공 및 분쟁 대응에 필요한 기간, 또는 이용자가 삭제를 요청한 때</li>
          <li>접속·보안 로그: 최대 12개월(보안·부정이용 방지 목적)</li>
          <li>
            관계 법령에 따른 보존(예: 통신비밀보호법상 로그인 기록 3개월 등
            해당 시)
          </li>
        </ul>
      </LegalSection>

      <LegalSection title="5. 개인정보의 제3자 제공">
        <p>
          운영팀은 이용자의 개인정보를 본 방침 제2조의 목적 범위에서만
          처리하며, 이용자 동의 없이 제3자에게 제공하지 않습니다. 다만 다음의
          경우는 예외입니다.
        </p>
        <ul className="list-disc space-y-2 pl-5">
          <li>이용자가 사전에 동의한 경우</li>
          <li>법령에 근거하거나 수사기관이 법령에 따라 요청한 경우</li>
        </ul>
        <p>
          Google로부터 받은 계정 정보(이메일·이름·프로필 등)를 판매하거나,
          독립적인 광고·마케팅 목적의 제3자 제공·이전에는 사용하지 않습니다.
        </p>
      </LegalSection>

      <LegalSection title="6. 개인정보 처리의 위탁 및 외부 서비스">
        <p>
          서비스 제공을 위해 다음과 같이 외부 서비스를 이용할 수 있습니다.
          위탁·연동 시 관련 법령에 따라 계약을 체결하고 관리·감독합니다.
        </p>
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <span className="font-semibold">Google</span> — Google OAuth 로그인
            인증({LEGAL.googleOAuthScopes.join(", ")}). 설정에 따라 임베딩 등
            Google AI API를 게임 기능에 사용할 수 있으나, 이는 OAuth로 받은
            계정 정보와 별개의 서비스 호출입니다.
          </li>
          <li>
            <span className="font-semibold">호스팅·데이터베이스 제공자</span> —
            서비스 서버 및 데이터 저장
          </li>
          <li>
            <span className="font-semibold">대규모 언어모델(LLM) 제공자</span> —
            게임 NPC·내레이션 등 응답 생성. 이용자가 입력한 질문·서술 텍스트가
            모델 호출에 포함될 수 있습니다. 운영팀은 이를 계정·세션과 연결해
            게임을 진행하는 데 사용하며, 광고 목적 판매에는 사용하지 않습니다.
          </li>
        </ul>
      </LegalSection>

      <LegalSection title="6의2. Google 사용자 데이터의 이용 제한">
        <p>
          운영팀은 Google API로부터 받은 사용자 데이터(OAuth로 확인한 계정
          식별·이메일·프로필 정보)를 Google API Services User Data Policy의
          Limited Use 요건에 따라, 서비스의 이용자 대면 기능(로그인, 계정 유지,
          플레이 기록 연결) 제공 및 보안·개선 목적에만 사용합니다. 해당 데이터를
          판매하지 않으며, 광고 목적으로 이용하거나 허용되지 않는 방식으로
          이전·공개하지 않습니다.
        </p>
      </LegalSection>

      <LegalSection title="7. 개인정보의 국외 이전">
        <p>
          Google OAuth 및 일부 클라우드·AI 서비스는 해외에 서버를 둔 사업자가
          처리할 수 있습니다. 이 경우 이전되는 정보, 이전 국가, 시기·방법,
          보유·이용 기간 등은 해당 사업자의 정책과 계약에 따르며, 운영팀은
          관련 법령이 요구하는 보호조치를 이행합니다. 이용자는 국외 이전에
          동의하지 않을 권리가 있으나, 동의 거부 시 Google 로그인 기반 서비스
          이용이 제한될 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="8. 이용자의 권리·의무 및 행사 방법">
        <p>이용자는 언제든지 다음 권리를 행사할 수 있습니다.</p>
        <ul className="list-disc space-y-2 pl-5">
          <li>개인정보 열람·정정·삭제·처리정지 요구</li>
          <li>동의 철회 및 회원 탈퇴(계정 삭제) 요청</li>
          <li>Google 계정 연동 해제(Google 계정 설정에서 앱 액세스 권한 관리)</li>
        </ul>
        <p>
          권리 행사는 {LEGAL.contactEmail} 로 요청하실 수 있으며, 운영팀은
          지체 없이 조치합니다. 법령상 의무 보존 정보가 있는 경우 해당 범위에서
          삭제가 제한될 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="9. 개인정보의 파기">
        <p>
          보유 기간이 경과하거나 처리 목적이 달성된 개인정보는 지체 없이
          파기합니다. 전자적 파일은 복구 불가능한 방법으로 삭제하고, 출력물은
          분쇄 또는 소각합니다.
        </p>
      </LegalSection>

      <LegalSection title="10. 개인정보의 안전성 확보 조치">
        <ul className="list-disc space-y-2 pl-5">
          <li>접근 권한 최소화 및 관리자 인증</li>
          <li>전송 구간 암호화(HTTPS 등)</li>
          <li>접속 기록 보관 및 위·변조 방지 노력</li>
          <li>악성코드·침해 대응을 위한 보안 점검</li>
        </ul>
      </LegalSection>

      <LegalSection title="11. 쿠키 등 자동 수집 장치의 설치·운영">
        <p>
          서비스는 Google 로그인 이후의 세션 유지, CSRF 등 보안 상태 보존,
          설정 저장, 이용 편의 제공을 위해 쿠키 또는 이와 유사한
          기술(로컬 스토리지 등)을 사용할 수 있습니다. 브라우저 설정에서
          저장을 거부할 수 있으나, 이 경우 로그인·진행 저장 등 일부 기능이
          제한될 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="12. 아동의 개인정보">
        <p>
          서비스는 원칙적으로 만 14세 미만 아동을 대상으로 하지 않으며, 만
          14세 미만의 Google 계정 로그인·개인정보 수집을 고의로 요청하지
          않습니다. 해당 사실이 확인되면 지체 없이 관련 정보를 삭제합니다.
        </p>
      </LegalSection>

      <LegalSection title="13. 개인정보 보호책임자">
        <p>
          개인정보 처리에 관한 문의·불만·피해 구제 요청은 아래로 연락해
          주세요.
        </p>
        <ul className="list-disc space-y-2 pl-5">
          <li>운영 주체: {LEGAL.operator}</li>
          <li>서비스명: {LEGAL.serviceName}</li>
          <li>이메일: {LEGAL.contactEmail}</li>
        </ul>
      </LegalSection>

      <LegalSection title="14. 권익침해 구제">
        <p>
          개인정보 침해에 대한 신고·상담이 필요하면 아래 기관에 문의할 수
          있습니다.
        </p>
        <ul className="list-disc space-y-2 pl-5">
          <li>개인정보침해신고센터 (privacy.kisa.or.kr / 국번없이 118)</li>
          <li>개인정보 분쟁조정위원회 (www.kopico.go.kr)</li>
          <li>대검찰청 사이버수사과 (www.spo.go.kr)</li>
          <li>경찰청 사이버수사국 (ecrm.cyber.go.kr)</li>
        </ul>
      </LegalSection>

      <LegalSection title="15. 방침의 변경">
        <p>
          본 방침의 내용 추가·삭제·수정이 있으면 서비스 내 공지 또는 본
          페이지를 통해 고지합니다. 중요한 변경은 시행 전에 안내합니다.
        </p>
        <p>본 방침은 {LEGAL.effectiveDate}부터 적용됩니다.</p>
      </LegalSection>
    </LegalDoc>
  );
}
