import os
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from config import ConfigError, ConfigStore, SecretStoreError, Settings, TokenStore


@pytest.fixture
def store(tmp_path):
    return ConfigStore(tmp_path / 'lpm')


def test_first_start_and_round_trip(store):
    assert store.load() == Settings()
    settings = replace(Settings(), ssh_mode=True, preferred_mgr='flatpak',
                       left_pane_width=53, bottom_pane_height=72,
                       current_sort='size', sort_descending=True,
                       current_priority_manager='flatpak', remember_token=False)
    store.save(settings)
    assert ConfigStore(store.directory).load() == settings
    assert store.directory.stat().st_mode & 0o777 == 0o700
    assert (store.directory / 'config.json').stat().st_mode & 0o777 == 0o600


def test_xdg_and_relative_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    assert ConfigStore().directory == tmp_path / 'lpm'
    monkeypatch.setenv('XDG_CONFIG_HOME', 'relative')
    assert ConfigStore().directory == Path.home() / '.config/lpm'


def test_unknown_fields_and_invalid_values_never_saved(store):
    settings = Settings.from_dict({'api_token': 'FAKE_SECRET', 'ssh_mode': 'false',
                                   'preferred_mgr': 'apt; echo bad', 'ai_engine': 'grok',
                                   'left_pane_width': True, 'bottom_pane_height': 999,
                                   'current_sort': ['size'], 'sort_descending': 1})
    assert settings == Settings()
    store.save(settings)
    assert 'FAKE_SECRET' not in (store.directory / 'config.json').read_text()
    assert 'api_token' not in (store.directory / 'config.json').read_text()


@pytest.mark.parametrize('raw', ['{broken', '[]', '{"version":2}', '{"version":true}', 'x' * 65537])
def test_broken_config_is_preserved(store, raw):
    store.directory.mkdir()
    path = store.directory / 'config.json'
    path.write_text(raw)
    assert store.load() == Settings()
    assert store.warning
    with pytest.raises(ConfigError):
        store.save(Settings())
    assert path.read_text() == raw


@pytest.mark.parametrize('kind', ['file_symlink', 'directory_symlink', 'hardlink', 'fifo'])
def test_unsafe_paths_rejected(tmp_path, kind):
    victim = tmp_path / 'victim'
    victim.write_text('{"ssh_mode":true}')
    directory = tmp_path / 'lpm'
    if kind == 'directory_symlink':
        target = tmp_path / 'outside'
        target.mkdir()
        directory.symlink_to(target, target_is_directory=True)
    else:
        directory.mkdir()
        path = directory / 'config.json'
        if kind == 'file_symlink':
            path.symlink_to(victim)
        elif kind == 'hardlink':
            os.link(victim, path)
        else:
            os.mkfifo(path)
    store = ConfigStore(directory)
    assert store.load() == Settings()
    assert store.warning
    with pytest.raises(ConfigError):
        store.save(Settings())
    assert victim.read_text() == '{"ssh_mode":true}'


def test_atomic_failure_keeps_previous_settings_and_cleans_temp(store, monkeypatch):
    store.save(Settings())
    old = (store.directory / 'config.json').read_bytes()
    def fail(*args, **kwargs):
        raise OSError('disk failure')
    monkeypatch.setattr(os, 'replace', fail)
    with pytest.raises(ConfigError):
        store.save(replace(Settings(), ssh_mode=True))
    assert (store.directory / 'config.json').read_bytes() == old
    assert sorted(p.name for p in store.directory.iterdir()) == ['config.json']


def test_tightens_existing_permissions(store):
    store.save(Settings())
    store.directory.chmod(0o755)
    (store.directory / 'config.json').chmod(0o644)
    store.load()
    assert store.directory.stat().st_mode & 0o777 == 0o700
    assert (store.directory / 'config.json').stat().st_mode & 0o777 == 0o600


def test_directory_error_is_safe(store, monkeypatch):
    monkeypatch.setattr(store, '_open_directory', Mock(side_effect=OSError('failure')))
    with pytest.raises(ConfigError):
        store.save(Settings())


def test_credentials_roundtrip_and_delete(monkeypatch, store):
    values = {}
    backend = Mock()
    backend.get_password.side_effect = lambda service, account: values.get((service, account))
    backend.set_password.side_effect = lambda service, account, token: values.__setitem__((service, account), token)
    backend.delete_password.side_effect = lambda service, account: values.pop((service, account))
    monkeypatch.setattr(TokenStore, '_backend', lambda self: backend)
    token_store = TokenStore()
    assert token_store.load() == ''
    token_store.save('FAKE_SECRET')
    assert TokenStore().load() == 'FAKE_SECRET'
    store.save(Settings())
    assert 'FAKE_SECRET' not in (store.directory / 'config.json').read_text()
    token_store.delete()
    token_store.delete()  # Missing tokens can be deleted again.
    assert token_store.load() == ''


@pytest.mark.parametrize('method,args', [('load', ()), ('save', ('FAKE_SECRET',)), ('delete', ())])
def test_backend_failures_do_not_expose_secrets(monkeypatch, method, args):
    monkeypatch.setattr(TokenStore, '_backend', Mock(side_effect=RuntimeError('FAKE_SECRET')))
    with pytest.raises(SecretStoreError) as error:
        getattr(TokenStore(), method)(*args)
    assert 'FAKE_SECRET' not in str(error.value)
    assert error.value.__suppress_context__


def test_explicit_secret_service_ignores_plaintext_backend_env(monkeypatch):
    monkeypatch.setenv('PYTHON_KEYRING_BACKEND', 'keyrings.alt.file.PlaintextKeyring')
    assert type(TokenStore()._backend()).__module__ == 'keyring.backends.SecretService'
