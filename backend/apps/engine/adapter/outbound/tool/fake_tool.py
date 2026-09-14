from apps.engine.app.ports.output.tool_port import ToolCallDTO, ToolResultDTO


class FakeTool:
    def __init__(self, result: str = "") -> None:
        self._result = result
        self.calls: list[ToolCallDTO] = []

    def dispatch(self, call: ToolCallDTO) -> ToolResultDTO:
        self.calls.append(call)
        return ToolResultDTO(result=self._result, side_effect=None)
