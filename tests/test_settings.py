import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from textual.app import App
from textual.widgets import Checkbox, Input, Select

import manager
from config import ConfigStore, SecretStoreError, Settings, TokenStore
from morefunction import SettingsScreen


@pytest.fixture
def environment(monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.setattr(manager.genai, 'Client', Mock(return_value=SimpleNamespace()))
    monkeypatch.setattr(TokenStore, 'load', Mock(return_value=''))
    monkeypatch.setattr(TokenStore, 'save', Mock())
    monkeypatch.setattr(TokenStore, 'delete', Mock())
    monkeypatch.setattr(manager.LinuxPackageManagerApp, 'load_installed_packages', AsyncMock())
    monkeypatch.setattr(manager.LinuxPackageManagerApp, 'load_git_projects', AsyncMock())
    return tmp_path


def data(**kwargs):
    return {'ai_engine': 'gemini', 'ssh_mode': True, 'preferred_mgr': 'apt',
            'api_token': '', 'remember_token': True, 'clear_token': False, **kwargs}


def test_save_restart_and_token_not_in_config(environment):
    app = manager.LinuxPackageManagerApp()
    app.notify = Mock()
    app.left_pane_width = 51
    asyncio.run(app.apply_settings(data(api_token='FAKE_SECRET')))
    TokenStore.save.assert_called_once_with('FAKE_SECRET')
    content = (environment / 'lpm/config.json').read_text()
    assert 'FAKE_SECRET' not in content
    restart = manager.LinuxPackageManagerApp()
    assert restart.ssh_mode
    assert restart.left_pane_width == 51
    assert restart.settings.remember_token


def test_blank_preserves_and_clear_deletes(environment):
    app = manager.LinuxPackageManagerApp()
    app.notify = Mock()
    app.current_gemini_token = 'FAKE_SECRET'
    asyncio.run(app.apply_settings(data()))
    assert app.current_gemini_token == 'FAKE_SECRET'
    TokenStore.save.assert_not_called()
    asyncio.run(app.apply_settings(data(clear_token=True, api_token='ignored')))
    assert app.current_gemini_token == ''
    assert app.ai.client is None
    TokenStore.delete.assert_called_once()
    assert not ConfigStore().load().remember_token


def test_uncheck_remember_uses_session_token_and_deletes_saved(environment):
    app = manager.LinuxPackageManagerApp()
    app.notify = Mock()
    asyncio.run(app.apply_settings(data(api_token='FAKE_SECRET', remember_token=False)))
    assert app.current_gemini_token == 'FAKE_SECRET'
    TokenStore.save.assert_not_called()
    TokenStore.delete.assert_called_once()
    assert not ConfigStore().load().remember_token


def test_cancel_changes_nothing(environment):
    app = manager.LinuxPackageManagerApp()
    asyncio.run(app.apply_settings(None))
    TokenStore.save.assert_not_called()
    TokenStore.delete.assert_not_called()
    assert not (environment / 'lpm/config.json').exists()


def test_file_failure_does_not_modify_credentials(environment):
    path = environment / 'lpm'
    path.mkdir()
    (path / 'config.json').write_text('{broken')
    app = manager.LinuxPackageManagerApp()
    app.notify = Mock()
    asyncio.run(app.apply_settings(data(api_token='FAKE_SECRET')))
    TokenStore.save.assert_not_called()
    assert not app.ssh_mode
    assert app.current_gemini_token == ''


def test_secret_failure_keeps_preferences_and_warns(environment):
    TokenStore.save.side_effect = SecretStoreError('Token 未能儲存至金鑰圈；目前只會在本次執行使用。')
    app = manager.LinuxPackageManagerApp()
    app.notify = Mock()
    asyncio.run(app.apply_settings(data(api_token='FAKE_SECRET')))
    assert ConfigStore().load().ssh_mode
    assert app.current_gemini_token == 'FAKE_SECRET'
    assert app.notify.call_args.kwargs['severity'] == 'warning'
    assert 'FAKE_SECRET' not in str(app.notify.call_args)


def test_delete_failure_disables_reload_and_warns(environment):
    TokenStore.delete.side_effect = SecretStoreError('無法刪除金鑰圈中的 Token')
    app = manager.LinuxPackageManagerApp()
    app.notify = Mock()
    asyncio.run(app.apply_settings(data(clear_token=True)))
    assert not ConfigStore().load().remember_token
    assert app.current_gemini_token == ''
    assert app.notify.call_args.kwargs['severity'] == 'warning'


def test_sdk_error_never_shows_exception_text(environment):
    explainer = manager.GeminiExplainer()
    client = SimpleNamespace(models=SimpleNamespace(generate_content=Mock(side_effect=RuntimeError('FAKE_SECRET'))))
    explainer.client = client
    response = asyncio.run(explainer.ask_gemini('vim'))
    assert 'FAKE_SECRET' not in response
    manager.genai.Client.side_effect = RuntimeError('FAKE_SECRET')
    app = manager.LinuxPackageManagerApp()
    app.notify = Mock()
    asyncio.run(app.apply_settings(data(api_token='FAKE_SECRET')))
    assert 'FAKE_SECRET' not in str(app.notify.call_args)
    assert app.ai.client is None


def test_real_modal_input_save_cancel_and_masking():
    async def scenario():
        host = App()
        results = []
        async with host.run_test(size=(100, 40)) as pilot:
            screen = SettingsScreen(token_present=True)
            await host.push_screen(screen, results.append)
            await pilot.pause()
            field = screen.query_one('#setting-api-token', Input)
            assert field.password and field.value == ''
            assert screen.query_one('#setting-ai-model', Select).value == 'gemini'
            field.focus()
            await pilot.press('q', 'z', 'a')
            assert field.value == 'qza'
            await pilot.click('#setting-save')
            await pilot.pause()
            assert results[0]['api_token'] == 'qza'
            assert field.value == ''
            assert results[0]['remember_token']
            screen = SettingsScreen()
            await host.push_screen(screen, results.append)
            cancelled_field = screen.query_one('#setting-api-token', Input)
            cancelled_field.value = 'FAKE_CANCELLED'
            await pilot.press('escape')
            await pilot.pause()
            assert results[-1] is None
            assert cancelled_field.value == ''
    asyncio.run(scenario())


def test_full_app_restart_loads_saved_token_and_layout(environment):
    ConfigStore().save(replace(Settings(), ssh_mode=True, left_pane_width=51, bottom_pane_height=72))
    TokenStore.load.return_value = 'FAKE_SAVED_SECRET'
    async def scenario():
        app = manager.LinuxPackageManagerApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            assert app.current_gemini_token == 'FAKE_SAVED_SECRET'
            assert app.query_one('#left-pane').styles.width.value == 51
            assert app.query_one('#bottom-pane').styles.height.value == 72
            app.action_open_esc_menu()
            await pilot.pause()
            await pilot.press('escape')
    asyncio.run(scenario())


def test_environment_token_has_precedence_and_is_not_persisted(environment, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'FAKE_ENV_SECRET')
    async def scenario():
        app = manager.LinuxPackageManagerApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            TokenStore.load.assert_not_called()
            assert app.current_gemini_token == 'FAKE_ENV_SECRET'
            await app.apply_settings(data())
            TokenStore.save.assert_not_called()
            assert 'FAKE_ENV_SECRET' not in (environment / 'lpm/config.json').read_text()
    asyncio.run(scenario())


def test_full_app_modal_save_does_not_trigger_shortcuts(environment):
    async def scenario():
        app = manager.LinuxPackageManagerApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            screen = SettingsScreen()
            await app.push_screen(screen, app.apply_settings)
            await pilot.pause()
            field = screen.query_one('#setting-api-token', Input)
            field.focus()
            await pilot.press('q', 'z', 'a')
            assert field.value == 'qza'
            screen.query_one('#setting-ssh-mode', Checkbox).value = True
            await pilot.click('#setting-save')
            await pilot.pause()
            assert app.current_gemini_token == 'qza'
            assert ConfigStore().load().ssh_mode
            TokenStore.save.assert_called_once_with('qza')
            assert not isinstance(app.screen, SettingsScreen)
    asyncio.run(scenario())


def test_small_terminal_settings_can_scroll_to_save():
    async def scenario():
        app = App()
        results = []
        async with app.run_test(size=(80, 24)) as pilot:
            screen = SettingsScreen()
            await app.push_screen(screen, results.append)
            await pilot.pause()
            button = screen.query_one('#setting-save')
            button.scroll_visible(animate=False)
            await pilot.pause()
            await pilot.click('#setting-save')
            await pilot.pause()
            assert results[0]['api_token'] == ''
    asyncio.run(scenario())


def test_token_input_does_not_broadcast_changed_or_submitted_events():
    from morefunction import TokenInput
    field = TokenInput(password=True)
    assert not field.post_message(Input.Changed(field, 'FAKE_SECRET'))
    assert not field.post_message(Input.Submitted(field, 'FAKE_SECRET'))


def test_missing_keyring_keeps_app_usable(environment):
    TokenStore.load.side_effect = SecretStoreError('無法存取系統金鑰圈')
    async def scenario():
        app = manager.LinuxPackageManagerApp()
        app.notify = Mock()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            assert app.ai.client is None
            assert app.current_gemini_token == ''
            assert any('無法存取' in str(call) for call in app.notify.call_args_list)
    asyncio.run(scenario())
