# -- coding: utf-8 --
import astrbot.api.message_components as Comp


def text_entry(text: str, *, name: str | None = None) -> dict:
    return {"name": name, "content": [Comp.Plain(text)]}


def entry(*components, name: str | None = None) -> dict:
    return {"name": name, "content": list(components)}


def _flatten_entries(entries: list[dict]):
    chain = []
    first = True
    for item in entries:
        if not first:
            chain.append(Comp.Plain("\n\n"))
        first = False
        chain.extend(item.get("content", []))
    return chain


def _make_forward_wrapper(nodes: list):
    constructors = [
        lambda: Comp.Nodes(nodes=nodes),
        lambda: Comp.Nodes(nodes),
        lambda: Comp.Forward(nodes=nodes),
        lambda: Comp.Forward(nodes),
    ]
    for ctor in constructors:
        try:
            return ctor()
        except Exception:
            continue
    return nodes


def forward_result(event, entries: list[dict], *, default_name: str = "系统记录"):
    """
    aiocqhttp / OneBot v11：优先发送单个合并转发卡片（一个卡片里包含多个节点）。
    其他平台：回退为普通消息链。
    """
    if event.get_platform_name() == "aiocqhttp":
        uin_raw = event.get_self_id() or event.get_sender_id() or 0
        try:
            uin = int(uin_raw)
        except Exception:
            uin = 0

        nodes = []
        for item in entries:
            nodes.append(
                Comp.Node(
                    uin=uin,
                    name=item.get("name") or default_name,
                    content=item.get("content", []),
                )
            )

        wrapper = _make_forward_wrapper(nodes)
        if isinstance(wrapper, list):
            return event.chain_result(wrapper)
        return event.chain_result([wrapper])

    return event.chain_result(_flatten_entries(entries))
