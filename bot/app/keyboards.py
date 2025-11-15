from typing import List
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import LinkButton

try:
    from maxapi.types import ButtonsPayload, MessageButton
    def open_link_kb(rows: list[list[tuple[str, str]]]):
        builder = InlineKeyboardBuilder()
        for row in rows:
            buttons = [LinkButton(text=label, url=url) for (label, url) in row]
            builder.row(*buttons)
        return builder.as_markup()

    def reply_kb(rows: List[List[str]]):
        btn_rows = []
        for row in rows:
            line = []
            for txt in row:
                try:
                    line.append(MessageButton(text=txt, payload={"text": txt}))
                except TypeError:
                    line.append(MessageButton(label=txt, payload={"text": txt}))
            btn_rows.append(line)
        return ButtonsPayload(buttons=btn_rows).pack()

except Exception:
    def reply_kb(rows: List[List[str]]):
        return {
            "type": "buttons",
            "buttons": [
                [
                    {"type": "message", "text": txt, "payload": {"text": txt}}
                    for txt in row
                ]
                for row in rows
            ],
        }
    def open_link_kb(rows: list[list[tuple[str, str]]], inline: bool = True):
        buttons = []
        for row in rows:
            buttons.append([
                {"action": {"type": "open_link", "label": label, "link": url}}
                for (label, url) in row
            ])
        kb = {"inline": inline, "buttons": buttons}
        return kb

