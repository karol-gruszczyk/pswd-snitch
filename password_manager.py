#!/usr/bin/env python
import functools
import urwid

import pyperclip

from components import StyledButton, OkDialog, OkCancelDialog, Dialog
from crypto.ninja import EncryptedImageNinja
from crypto.vault import ImageVault, Password


def close_app(*args):
    raise urwid.ExitMainLoop()


palette = [
    ('banner', 'dark red', ''),
    ('reversed', 'standout', ''),
]

logo = urwid.Pile(
    [
        urwid.Padding(
            urwid.BigText(('banner', "PSWD SNITCH"), urwid.Thin6x6Font()),
            width="clip",
            align=urwid.CENTER,
        ),
        urwid.Divider(),
    ]
)
background = urwid.AttrMap(urwid.SolidFill('.'), 'bg')


class PasswordEditDialog(urwid.WidgetWrap):
    def __init__(
            self, parent, loop: urwid.MainLoop, password: Password, on_save: callable
    ):
        self.loop = loop
        self.password = password
        self.on_save = on_save

        self.name_edit = urwid.Edit(edit_text=self.password.name, wrap=urwid.CLIP)
        self.login_edit = urwid.Edit(edit_text=self.password.login, wrap=urwid.CLIP)
        self.password_edit = urwid.Edit(mask="*", wrap=urwid.CLIP)

        body = urwid.ListBox(
            urwid.SimpleFocusListWalker(
                [
                    urwid.Text("Name:"),
                    urwid.LineBox(self.name_edit),
                    urwid.Text("Login:"),
                    urwid.LineBox(self.login_edit),
                    urwid.Text("Password:"),
                    urwid.LineBox(self.password_edit),
                    urwid.Columns([
                        StyledButton("Cancel", on_press=self.close),
                        StyledButton("Save", on_press=self.save),
                    ]),
                ]
            )
        )
        widget = urwid.Overlay(
            Dialog(body, message=self.password.name, title="Edit"),
            parent,
            align=urwid.CENTER,
            valign=urwid.MIDDLE,
            width=50,
            height=20,
        )
        super().__init__(widget)

    def save(self, *args):
        if not self.name_edit.get_edit_text():
            self.loop.widget = OkDialog(
                self, self.loop, "Name cannot be empty!", "Error!"
            )
        elif not self.login_edit.get_edit_text():
            self.loop.widget = OkDialog(
                self, self.loop, "Login cannot be empty!", "Error!"
            )
        elif not self.password_edit.get_edit_text():
            self.loop.widget = OkDialog(
                self, self.loop, "Password cannot be empty!", "Error!"
            )
        else:
            self.password.name = self.name_edit.get_edit_text()
            self.password.login = self.login_edit.get_edit_text()
            self.password.passphrase = self.password_edit.get_edit_text()
            self.on_save(self.password)
            self.close()

    def close(self, *args):
        self.loop.widget = self._w.bottom_w


class LoginScreen(urwid.WidgetWrap):
    def __init__(
            self, loop: urwid.MainLoop, password_check: callable, on_success: callable
    ):
        self.loop = loop
        self.password_check = password_check
        self.on_success = on_success
        self.password_edit = urwid.Edit(
            align=urwid.CENTER, multiline=False, wrap=urwid.CLIP, mask="*"
        )
        body = urwid.ListBox(
            urwid.SimpleFocusListWalker(
                [
                    urwid.Text("Enter password:", align=urwid.CENTER),
                    urwid.LineBox(self.password_edit),
                ]
            )
        )
        login_box = urwid.LineBox(
            urwid.Padding(urwid.Frame(header=logo, body=body), left=2, right=2)
        )
        widget = urwid.Overlay(
            login_box,
            background,
            align=urwid.CENTER,
            valign=urwid.MIDDLE,
            width=70,
            height=14,
        )
        super().__init__(widget)
        self.wrong_password = OkDialog(
            self, self.loop, message="Wrong password!", title="Error!"
        )

    def keypress(self, size, key):
        if key == "enter":
            passphrase = self.password_edit.get_edit_text()
            if self.password_check(passphrase):
                self.on_success(passphrase)
            else:
                self.password_edit.set_edit_text("")
                self.loop.widget = self.wrong_password
        super().keypress(size, key)


class PasswordsScreen(urwid.WidgetWrap):
    def __init__(self, loop: urwid.MainLoop, vault: ImageVault):
        self.loop = loop
        self.vault = vault
        footer = urwid.Pile(
            [
                urwid.Divider(),
                urwid.Columns(
                    [
                        urwid.Text("Q: Quit", align=urwid.CENTER),
                        urwid.Text("C: Clipboard", align=urwid.CENTER),
                        urwid.Text("A: Add", align=urwid.CENTER),
                        urwid.Text("S: Save", align=urwid.CENTER),
                    ]
                ),
            ]
        )

        self.passwords_list_box = urwid.ListBox(urwid.SimpleFocusListWalker([]))
        self.setup_password_buttons()
        main = urwid.LineBox(
            urwid.Padding(
                urwid.Frame(header=logo, body=self.passwords_list_box, footer=footer),
                left=2,
                right=2,
            )
        )

        widget = urwid.Overlay(
            main,
            background,
            align=urwid.CENTER,
            valign=urwid.MIDDLE,
            width=80,
            height=(urwid.RELATIVE, 60),
            min_height=10,
        )
        super().__init__(widget)
        self.exit_dialog = OkCancelDialog(
            self, self.loop, "Exit?", title="", on_ok=close_app
        )

    def setup_password_buttons(self):
        def edit_password(index, button):
            password = self.vault.passwords[index]
            on_save = functools.partial(self.save_password, index=index)
            self.loop.widget = PasswordEditDialog(
                self, self.loop, password, on_save=on_save
            )

        self.passwords_list_box._set_body(
            [
                StyledButton(str(p), on_press=functools.partial(edit_password, i))
                for i, p in enumerate(self.vault.passwords)
            ]
        )

    def keypress(self, size, key):
        if key == "c":
            password = self.vault.passwords[self.passwords_list_box.focus_position]
            pyperclip.copy(password.passphrase)
            self.loop.widget = OkDialog(
                self,
                self.loop,
                message=f"Copied password to clipboard!",
                title=str(password),
            )
        elif key in ("q", "Q"):
            self.loop.widget = self.exit_dialog
        elif key in ("a", "A"):
            self.loop.widget = PasswordEditDialog(
                self, self.loop, Password("", "", ""), self.save_password
            )
        elif key in ("s", "Save"):
            self.vault.save()
            self.loop.widget = OkDialog(
                self, self.loop, message="Vault saved!", title="Success!"
            )
        super().keypress(size, key)

    def save_password(self, password: Password, *, index: bool = None):
        if index is None:
            self.vault.passwords.append(password)
        else:
            self.vault.passwords[index] = password
        self.setup_password_buttons()


class Application:
    def __init__(self, path: str, for_write: bool):
        self.path = path
        self.for_write = for_write
        self.main_view = None
        self.loop = urwid.MainLoop(None, palette=palette)

        def password_check(password: str) -> bool:
            if self.for_write:
                return True
            try:
                ImageVault(self.path, password=password)
                return True
            except EncryptedImageNinja.InvalidPassword:
                return False

        def on_success(password):
            self.main_view = PasswordsScreen(
                self.loop, ImageVault(self.path, password, self.for_write)
            )
            self.loop.widget = self.main_view

        self.login_screen = LoginScreen(
            self.loop, password_check=password_check, on_success=on_success
        )
        self.loop.widget = self.login_screen

    def run(self):
        self.loop.run()


if __name__ == "__main__":
    try:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--new", action="store_true")
        parser.add_argument("image", type=argparse.FileType())
        args = parser.parse_args()

        Application(args.image.name, for_write=bool(args.new)).run()
    except KeyboardInterrupt:
        pass
