from __future__ import annotations

import sys
import types


def _install_ulauncher_stubs() -> None:
    if "ulauncher" in sys.modules:
        return

    modules = {
        "ulauncher": types.ModuleType("ulauncher"),
        "ulauncher.api": types.ModuleType("ulauncher.api"),
        "ulauncher.api.client": types.ModuleType("ulauncher.api.client"),
        "ulauncher.api.client.Extension": types.ModuleType("ulauncher.api.client.Extension"),
        "ulauncher.api.client.EventListener": types.ModuleType(
            "ulauncher.api.client.EventListener"
        ),
        "ulauncher.api.shared": types.ModuleType("ulauncher.api.shared"),
        "ulauncher.api.shared.event": types.ModuleType("ulauncher.api.shared.event"),
        "ulauncher.api.shared.item": types.ModuleType("ulauncher.api.shared.item"),
        "ulauncher.api.shared.item.ExtensionResultItem": types.ModuleType(
            "ulauncher.api.shared.item.ExtensionResultItem"
        ),
        "ulauncher.api.shared.item.ExtensionSmallResultItem": types.ModuleType(
            "ulauncher.api.shared.item.ExtensionSmallResultItem"
        ),
        "ulauncher.api.shared.action": types.ModuleType("ulauncher.api.shared.action"),
        "ulauncher.api.shared.action.RenderResultListAction": types.ModuleType(
            "ulauncher.api.shared.action.RenderResultListAction"
        ),
        "ulauncher.api.shared.action.CopyToClipboardAction": types.ModuleType(
            "ulauncher.api.shared.action.CopyToClipboardAction"
        ),
        "ulauncher.api.shared.action.OpenUrlAction": types.ModuleType(
            "ulauncher.api.shared.action.OpenUrlAction"
        ),
        "ulauncher.api.shared.action.RunScriptAction": types.ModuleType(
            "ulauncher.api.shared.action.RunScriptAction"
        ),
        "ulauncher.api.shared.action.DoNothingAction": types.ModuleType(
            "ulauncher.api.shared.action.DoNothingAction"
        ),
    }

    class Extension:
        def __init__(self) -> None:
            self.preferences = {}
            self._subscriptions = []

        def subscribe(self, event_type, listener) -> None:
            self._subscriptions.append((event_type, listener))

        def run(self) -> None:
            return

    class EventListener:
        def on_event(self, event, extension):
            raise NotImplementedError

    class KeywordQueryEvent:
        def __init__(self, argument: str | None) -> None:
            self.argument = argument

        def get_argument(self):
            return self.argument

    class ExtensionResultItem:
        def __init__(self, icon=None, name=None, description=None, on_enter=None) -> None:
            self.icon = icon
            self.name = name
            self.description = description
            self.on_enter = on_enter

    class ExtensionSmallResultItem(ExtensionResultItem):
        pass

    class RenderResultListAction:
        def __init__(self, items) -> None:
            self.items = items

    class CopyToClipboardAction:
        def __init__(self, text: str) -> None:
            self.text = text

    class OpenUrlAction:
        def __init__(self, url: str) -> None:
            self.url = url

    class DoNothingAction:
        pass

    class RunScriptAction:
        def __init__(self, script: str) -> None:
            self.script = script

    modules["ulauncher.api.client.Extension"].Extension = Extension
    modules["ulauncher.api.client.EventListener"].EventListener = EventListener
    modules["ulauncher.api.shared.event"].KeywordQueryEvent = KeywordQueryEvent
    modules["ulauncher.api.shared.item.ExtensionResultItem"].ExtensionResultItem = (
        ExtensionResultItem
    )
    modules["ulauncher.api.shared.item.ExtensionSmallResultItem"].ExtensionSmallResultItem = (
        ExtensionSmallResultItem
    )
    modules["ulauncher.api.shared.action.RenderResultListAction"].RenderResultListAction = (
        RenderResultListAction
    )
    modules["ulauncher.api.shared.action.CopyToClipboardAction"].CopyToClipboardAction = (
        CopyToClipboardAction
    )
    modules["ulauncher.api.shared.action.OpenUrlAction"].OpenUrlAction = OpenUrlAction
    modules["ulauncher.api.shared.action.RunScriptAction"].RunScriptAction = RunScriptAction
    modules["ulauncher.api.shared.action.DoNothingAction"].DoNothingAction = DoNothingAction

    for name, module in modules.items():
        sys.modules[name] = module


_install_ulauncher_stubs()
