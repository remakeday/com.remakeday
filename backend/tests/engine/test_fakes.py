from apps.engine.adapter.outbound.embedding.fake_embedding import FakeEmbedding
from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.adapter.outbound.tool.fake_tool import FakeTool
from apps.engine.app.ports.output.embedding_port import EMBEDDING_DIM
from apps.engine.app.ports.output.llm_port import MessageDTO
from apps.engine.app.ports.output.tool_port import ToolCallDTO


def test_fake_llm_returns_queue_in_order():
    llm = FakeLLM([{"a": 1}, {"b": 2}])
    msgs = [MessageDTO(role="user", content="hi")]
    assert llm.complete(msgs, {}) == {"a": 1}
    assert llm.complete(msgs, {}) == {"b": 2}
    assert llm.complete(msgs, {}) == {}
    assert len(llm.calls) == 3


def test_fake_embedding_is_deterministic_and_1536d():
    emb = FakeEmbedding()
    v1, v2 = emb.embed(["같은 입력", "같은 입력"])
    assert v1 == v2
    assert len(v1) == EMBEDDING_DIM
    (v3,) = emb.embed(["다른 입력"])
    assert v3 != v1


def test_fake_tool_records_calls():
    tool = FakeTool(result="ok")
    res = tool.dispatch(ToolCallDTO(name="ask_npc", args={"target": "A"}))
    assert res.result == "ok"
    assert tool.calls[0].name == "ask_npc"
