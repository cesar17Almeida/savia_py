import logging

from savia import app


def test_greet_default():
    assert app.greet() == "Hello, world!"


def test_greet_custom_name():
    assert app.greet("Savia") == "Hello, Savia!"


def test_run_logs_greeting(caplog):
    with caplog.at_level(logging.INFO, logger="savia.app"):
        app.run()
    assert "Hello, Savia!" in caplog.text
