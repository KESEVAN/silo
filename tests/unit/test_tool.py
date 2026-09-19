from silo.tools.log_tool import LogTool
from silo.tools.read_tool import ReadTool
from silo.tools.send_tool import SendTool


def test_log_tool_records_a_timestamped_line():
    tool = LogTool()
    result = tool.execute({"message": "porter online"})
    assert result["status"] == "ok"
    assert "porter online" in result["line"]
    assert len(tool.entries) == 1


def test_read_tool_pops_from_inbox_in_order():
    inbox = [{"from": "a"}, {"from": "b"}]
    tool = ReadTool(inbox=inbox)
    first = tool.execute({})
    assert first["item"] == {"from": "a"}
    assert inbox == [{"from": "b"}]


def test_read_tool_reports_empty_when_nothing_pending():
    tool = ReadTool(inbox=[])
    result = tool.execute({})
    assert result["status"] == "empty"


def test_send_tool_calls_injected_delivery_function():
    delivered = []
    tool = SendTool(deliver=delivered.append)
    result = tool.execute({"recipient": "judiciary", "payload": {"note": "hi"}})
    assert result["status"] == "ok"
    assert delivered == [{"recipient": "judiciary", "payload": {"note": "hi"}}]


def test_send_tool_rejects_missing_recipient():
    tool = SendTool()
    result = tool.execute({"payload": {}})
    assert result["status"] == "error"
