import type { Metadata } from "next";
import Link from "next/link";
import { LegalDoc, LegalSection } from "@/components/LegalDoc";
import { LEGAL } from "@/lib/legal";

export const metadata: Metadata = {
  title: `이용약관 · ${LEGAL.serviceName}`,
  description: `${LEGAL.serviceName} 이용약관`,
};

export default function TermsPage() {
  return (
    <LegalDoc title="이용약관">
      <LegalSection title="제1조 (목적)">
        <p>
          본 약관은 {LEGAL.operator}(이하 &quot;운영팀&quot;)이 제공하는{" "}
          {LEGAL.serviceName}(이하 &quot;서비스&quot;)의 이용 조건과 운영팀·이용자
          간의 권리·의무 및 책임사항을 규정합니다.
        </p>
      </LegalSection>

      <LegalSection title="제2조 (정의)">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            &quot;서비스&quot;란 운영팀이 제공하는 AI 기반 내러티브·추리 게임{" "}
            {LEGAL.serviceName} 및 관련 웹·API·부가 기능을 말합니다.
          </li>
          <li>
            &quot;이용자&quot;란 본 약관에 동의하고 서비스를 이용하는 자를
            말합니다.
          </li>
          <li>
            &quot;계정&quot;이란 Google OAuth 등 운영팀이 정한 인증 수단으로
            생성·연동되는 이용자 식별 단위를 말합니다.
          </li>
          <li>
            &quot;콘텐츠&quot;란 텍스트, 이미지, 음성, 규칙, 시나리오, AI 생성
            응답 등 서비스에 포함되거나 이용 중 생성되는 일체의 자료를
            말합니다.
          </li>
        </ul>
      </LegalSection>

      <LegalSection title="제3조 (약관의 효력과 변경)">
        <p>
          본 약관은 서비스 화면에 게시하거나 기타 방법으로 공지함으로써
          효력이 발생합니다. 운영팀은 관련 법령을 위반하지 않는 범위에서
          약관을 개정할 수 있으며, 변경 시 적용 일자와 사유를 서비스에
          공지합니다. 이용자가 변경 약관 시행 이후에도 서비스를 계속
          이용하면 변경에 동의한 것으로 봅니다. 동의하지 않으면 이용을
          중단하고 탈퇴할 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="제4조 (서비스의 내용)">
        <p>
          서비스는 반복되는 하루 속에서 단서를 모아 세계의 진실을 추리하는
          인터랙티브 게임을 제공합니다. NPC 대화·밤 서술 채점·신의 개입 등
          일부 기능은 대규모 언어모델(LLM)을 통해 생성·보조될 수 있으며,
          동일 입력에도 결과가 달라질 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="제5조 (이용 계약 및 Google 로그인)">
        <ol className="list-decimal space-y-2 pl-5">
          <li>
            이용 계약은 이용자가 본 약관과{" "}
            <Link href="/privacy" className="underline underline-offset-4">
              개인정보 처리방침
            </Link>
            에 동의하고, Google 계정으로 로그인을 완료한 때 성립합니다.
          </li>
          <li>
            서비스 회원 인증은 Google OAuth를 통해 이루어집니다. 운영팀
            서버가 Google의 인증 결과를 확인한 뒤 서비스 계정을
            생성·연동하며, Google 비밀번호는 운영팀이 보관하지 않습니다.
          </li>
          <li>
            운영팀이 Google에 요청하는 권한 범위는{" "}
            {LEGAL.googleOAuthScopes.join(", ")} 에 한정되며, 이메일, 이름,
            프로필 이미지, 계정 식별자 등 해당 범위에서 제공되는 정보를
            계정 생성·유지에 사용합니다.
          </li>
          <li>
            하나의 Google 계정에는 원칙적으로 하나의 서비스 계정이
            연결됩니다. 이용자는 본인 소유의 Google 계정만 사용해야 하며,
            타인의 계정을 무단으로 사용해서는 안 됩니다.
          </li>
          <li>
            만 14세 미만은 서비스를 이용할 수 없습니다. 만 14세 이상
            미성년자는 법정대리인 동의 등 관련 법령이 요구하는 절차를 갖춘
            경우에 한해 이용할 수 있습니다.
          </li>
        </ol>
      </LegalSection>

      <LegalSection title="제6조 (계정 관리)">
        <p>
          계정 및 Google 연동 정보의 관리 책임은 이용자에게 있습니다. 무단
          사용이 의심되면 즉시 Google 계정 보안을 확인하고 운영팀에
          알려주세요. 이용자는 서비스에서 로그아웃 수 있으며, Google 계정
          설정에서 본 서비스에 대한 앱 액세스 권한을 철회할 수 있습니다.
          운영팀은 보안상 필요하거나 약관·법령 위반이 확인된 경우 계정
          이용을 제한할 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="제7조 (이용자의 의무)">
        <p>이용자는 다음 행위를 해서는 안 됩니다.</p>
        <ul className="list-disc space-y-2 pl-5">
          <li>법령 또는 본 약관을 위반하는 행위</li>
          <li>타인의 개인정보·계정을 도용하거나 허위 정보를 등록하는 행위</li>
          <li>서비스의 서버·네트워크·보안을 방해하거나 무단 접근하는 행위</li>
          <li>
            자동화된 수단으로 비정상적으로 요청을 보내거나 시스템을 남용하는
            행위
          </li>
          <li>
            서비스 콘텐츠를 무단 복제·배포·판매하거나, 역설계·크롤링으로
            시나리오·모델 입출력을 대량 수집하는 행위
          </li>
          <li>
            타인을 괴롭히거나, 불법·유해한 내용을 입력해 AI·다른 이용자에게
            피해를 주는 행위
          </li>
        </ul>
      </LegalSection>

      <LegalSection title="제8조 (운영팀의 의무)">
        <p>
          운영팀은 안정적인 서비스 제공을 위해 노력하며, 이용자의 개인정보를
          개인정보 처리방침에 따라 보호합니다. 다만 천재지변, 장비 장애, 외부
          API·LLM 제공자 장애 등 불가항력으로 인한 중단에 대해서는 법령이
          허용하는 범위에서 책임을 제한할 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="제9조 (AI 생성 콘텐츠에 관한 고지)">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            NPC 대사, 조언, 채점 보조 등 일부 출력은 AI가 생성하며 사실·완성도를
            보증하지 않습니다.
          </li>
          <li>
            이용자가 입력한 텍스트는 게임 진행을 위해 모델 호출·로그에 포함될
            수 있습니다. 민감하거나 타인에 관한 정보를 입력하지 않도록
            주의하세요.
          </li>
          <li>
            서비스의 서사·이미지·음성은 허구의 창작물이며, 실제 인물·단체와
            무관한 경우가 있습니다.
          </li>
        </ul>
      </LegalSection>

      <LegalSection title="제10조 (지적재산권)">
        <p>
          서비스와 이에 포함된 시나리오, 문구, 이미지, 음성, 소프트웨어,
          상표 등에 관한 권리는 운영팀 또는 정당한 권리자에게 귀속됩니다.
          이용자는 서비스 이용을 위한 범위 내에서만 콘텐츠를 사용할 수
          있습니다. 이용자가 입력한 플레이 텍스트에 대한 권리는 이용자에게
          있으나, 운영팀은 서비스 제공·개선·보안·법령 준수를 위해 이를
          저장·처리할 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="제11조 (서비스의 변경·중단)">
        <p>
          운영팀은 운영상·기술상 필요에 따라 서비스의 전부 또는 일부를
          수정·중단·종료할 수 있습니다. 이용자에게 중대한 영향을 미치는 경우
          사전에 공지하며, 긴급한 보안·장애 대응 시에는 사후 공지할 수
          있습니다.
        </p>
      </LegalSection>

      <LegalSection title="제12조 (계약 해지 및 이용 제한)">
        <p>
          이용자는 언제든지 계정 삭제 또는 Google 연동 해제를 요청하여 이용을
          종료할 수 있습니다. 운영팀은 약관 위반, 부정 이용, 장기 미사용,
          서비스 종료 등의 사유로 이용을 제한하거나 계약을 해지할 수 있습니다.
        </p>
      </LegalSection>

      <LegalSection title="제13조 (면책)">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            운영팀은 무료로 제공되는 서비스의 특정 목적 적합성, 무중단,
            오류 없음을 보증하지 않습니다.
          </li>
          <li>
            AI 응답의 부정확성, 외부 인증·호스팅·LLM 제공자 측 장애로 인한
            손해에 대해 운영팀의 고의 또는 중과실이 없는 한 책임을 지지
            않습니다.
          </li>
          <li>
            이용자 간 또는 이용자와 제3자 사이에서 발생한 분쟁에 대해서는
            개입할 의무가 없습니다.
          </li>
        </ul>
      </LegalSection>

      <LegalSection title="제14조 (준거법 및 관할)">
        <p>
          본 약관은 대한민국 법령에 따릅니다. 서비스와 관련하여 분쟁이 발생한
          경우 민사소송법 등 관련 법령에 따른 관할 법원에 제소합니다.
        </p>
      </LegalSection>

      <LegalSection title="제15조 (문의)">
        <p>
          약관 및 서비스 관련 문의: {LEGAL.contactEmail}
        </p>
        <p>본 약관은 {LEGAL.effectiveDate}부터 시행합니다.</p>
      </LegalSection>
    </LegalDoc>
  );
}
